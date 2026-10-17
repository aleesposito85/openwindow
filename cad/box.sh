#!/bin/sh
# cad/box.sh: run OpenSCAD on the Windows build box (render | test | png | ping)
set -e
HOST=${BOX_HOST:-alees@192.168.68.61}
REMOTE=C:/Users/alees/diywindow
WREMOTE='C:\Users\alees\diywindow'
SCAD=C:/Users/alees/tools/OpenSCAD-2026.10.02-x86-64/openscad.com
CAD=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$CAD")
TMP=$(mktemp -d)
RUNID=$(date +%Y%m%d%H%M%S)-$$
REMOTE_RUN="$REMOTE/run-$RUNID"
WREMOTE_RUN="$WREMOTE\\run-$RUNID"
RUN_DIR_READY=0
ERRPAT='^ERROR:|^WARNING:|Assertion|^FAILED'
GENLOCK="$ROOT/.generate.lock"
LOCK_HELD=0

cleanup() {
  rc=$?
  if [ "$LOCK_HELD" = 1 ]; then
    rmdir "$GENLOCK" 2>/dev/null || true
  fi
  if [ "$RUN_DIR_READY" = 1 ]; then
    remote "if exist $WREMOTE_RUN rmdir /s /q $WREMOTE_RUN" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  exit $rc
}
trap cleanup EXIT

remote() { ssh -B en0 -o BatchMode=yes -o ConnectTimeout=10 "$HOST" "$@"; }
put() { scp -q -o BindInterface=en0 -o BatchMode=yes -o ConnectTimeout=10 "$1" "$HOST:$2"; }
get() { scp -q -o BindInterface=en0 -o BatchMode=yes -o ConnectTimeout=10 "$HOST:$1" "$2"; }

lock_acquire() {
  i=0
  while ! mkdir "$GENLOCK" 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge 300 ]; then
      echo "box.sh: timed out waiting for the generate.py lock ($GENLOCK)" >&2
      return 1
    fi
    sleep 0.1
  done
  LOCK_HELD=1
}

lock_release() {
  LOCK_HELD=0
  rmdir "$GENLOCK" 2>/dev/null || true
}

snapshot() {
  COPYFILE_DISABLE=1 tar -cf "$TMP/cad.tar" -C "$ROOT" --exclude 'cad/stl' cad
}

upload() {
  remote "mkdir $WREMOTE 2>nul & forfiles /p $WREMOTE /m run-* /d -1 /c \"cmd /c if @isdir==TRUE rd /s /q @path\" >nul 2>&1 & mkdir $WREMOTE_RUN\\out"
  RUN_DIR_READY=1
  put "$TMP/cad.tar" "$REMOTE_RUN/cad.tar"
  remote "tar -xf $REMOTE_RUN/cad.tar -C $REMOTE_RUN"
}

run_batch() {
  CONN_FAILED=0
  put "$TMP/run.cmd" "$REMOTE_RUN/run.cmd"
  rc=$?
  if [ "$rc" != 0 ]; then
    [ "$rc" = 255 ] && CONN_FAILED=1
    echo "box.sh: failed to upload run.cmd (scp exit $rc)" >&2
    return 1
  fi
  remote "$WREMOTE_RUN\\run.cmd" > "$TMP/log.raw" 2>&1
  rc=$?
  tr -d '\r' < "$TMP/log.raw" > "$TMP/log.txt"
  if [ "$rc" = 255 ]; then
    CONN_FAILED=1
    echo "box.sh: ssh connection failed (exit 255)" >&2
    return 1
  fi
  if ! grep -q "^== DONE$" "$TMP/log.txt"; then
    echo "box.sh: batch did not finish (no '== DONE' marker in log)" >&2
    grep -E "^== |$ERRPAT" "$TMP/log.txt" >&2 || true
    return 1
  fi
  if grep -qE "$ERRPAT" "$TMP/log.txt"; then
    grep -E "^== |$ERRPAT" "$TMP/log.txt"
    return 1
  fi
}

render() {
  name=${1:?usage: box.sh render <params-name> [ID ...]}
  shift
  had_ids=$#
  lock_acquire || return 1
  rc=0
  python3 "$ROOT/tools/generate.py" "$ROOT/params/$name.json" || rc=$?
  if [ "$rc" != 0 ]; then
    lock_release
    return 1
  fi
  if [ "$had_ids" -gt 0 ]; then
    ids="$*"
  else
    ids=$(cd "$CAD/generated/parts" && ls *.scad | sed 's/\.scad$//')
  fi
  snapshot
  lock_release
  upload
  printf '@echo off\r\n' > "$TMP/run.cmd"
  for id in $ids; do
    printf 'echo == %s\r\n"%s" --backend=manifold -o %s/out/%s.stl %s/cad/generated/parts/%s.scad 2>&1 || echo FAILED %s\r\n' \
      "$id" "$SCAD" "$REMOTE_RUN" "$id" "$REMOTE_RUN" "$id" "$id" >> "$TMP/run.cmd"
  done
  printf 'echo == DONE\r\n' >> "$TMP/run.cmd"
  status=0
  run_batch || status=1
  if [ "$CONN_FAILED" = 1 ]; then
    return 1
  fi
  remote "tar -cf $REMOTE_RUN/stl.tar -C $REMOTE_RUN/out ." || return 1
  get "$REMOTE_RUN/stl.tar" "$TMP/stl.tar" || return 1
  mkdir -p "$CAD/stl/$name"
  if [ "$had_ids" -eq 0 ]; then
    rm -f "$CAD/stl/$name"/*.stl
  fi
  tar -xf "$TMP/stl.tar" -C "$CAD/stl/$name"
  python3 "$ROOT/tools/check_stl.py" "$name" $* || status=1
  return $status
}

tests() {
  lock_acquire || return 1
  rc=0
  python3 "$ROOT/tools/generate.py" "$ROOT/params/${1:-bench-600}.json" >/dev/null || rc=$?
  if [ "$rc" != 0 ]; then
    lock_release
    return 1
  fi
  expected=$(cd "$CAD/tests" && ls *_test.scad 2>/dev/null | wc -l | tr -d ' ')
  if [ "$expected" -eq 0 ]; then
    lock_release
    echo "box.sh test: no *_test.scad files found in cad/tests" >&2
    return 1
  fi
  snapshot
  lock_release
  upload
  printf '@echo off\r\n' > "$TMP/run.cmd"
  for f in $(cd "$CAD/tests" && ls *_test.scad); do
    printf 'echo == %s\r\n"%s" -o %s/out/%s.echo %s/cad/tests/%s 2>&1 || echo FAILED %s\r\ntype %s\\out\\%s.echo\r\n' \
      "$f" "$SCAD" "$REMOTE_RUN" "$f" "$REMOTE_RUN" "$f" "$f" "$WREMOTE_RUN" "$f" >> "$TMP/run.cmd"
  done
  printf 'echo == DONE\r\n' >> "$TMP/run.cmd"
  run_batch || return 1
  actual=$(grep -c "^== .*\.scad$" "$TMP/log.txt") || true
  if [ "$actual" -ne "$expected" ]; then
    echo "box.sh test: expected $expected test file(s), log shows $actual" >&2
    return 1
  fi
  printf '%d test files passed\n' "$actual"
}

png() {
  src=${1:?usage: box.sh png <file.scad relative to cad/> <out.png> [openscad args]}
  out=${2:?missing out.png}
  shift 2
  for arg in "$@"; do
    case "$arg" in
      *[\&\|\<\>\^%]*)
        echo "box.sh png: arg '$arg' contains a forbidden character (one of & | < > ^ %)" >&2
        return 1
        ;;
    esac
  done
  lock_acquire || return 1
  rc=0
  python3 "$ROOT/tools/generate.py" "$ROOT/params/${PARAMS:-bench-600}.json" >/dev/null || rc=$?
  if [ "$rc" != 0 ]; then
    lock_release
    return 1
  fi
  snapshot
  lock_release
  upload
  printf '@echo off\r\n"%s" --backend=manifold --render --imgsize=1600,1000 --colorscheme=Tomorrow %s -o %s/out/preview.png %s/cad/%s 2>&1 || echo FAILED png\r\necho == DONE\r\n' \
    "$SCAD" "$*" "$REMOTE_RUN" "$REMOTE_RUN" "$src" > "$TMP/run.cmd"
  run_batch || return 1
  get "$REMOTE_RUN/out/preview.png" "$out"
}

cmd=${1:?usage: box.sh render|test|png|ping ...}
shift
case $cmd in
  render) render "$@" ;;
  test) tests "$@" ;;
  png) png "$@" ;;
  ping) remote "echo ok" ;;
  *) echo "unknown command $cmd" >&2; exit 2 ;;
esac
