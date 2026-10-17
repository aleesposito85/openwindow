#!/bin/sh
# cad/box.sh (container variant): run OpenSCAD locally in the openwindow LXC.
# Same interface as the Windows-box version: render | test | png | ping.
# The original Windows-over-SSH version is kept as cad/box.sh.windows.
set -e
HOST=${BOX_HOST:-openwindow-local}
SCAD=${SCAD:-/opt/squashfs-root/usr/bin/openscad}
CAD=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$CAD")
TMP=$(mktemp -d)
ERRPAT='^ERROR:|^WARNING:|Assertion|^FAILED'
GENLOCK="$ROOT/.generate.lock"
LOCK_HELD=0

cleanup() {
  rc=$?
  if [ "$LOCK_HELD" = 1 ]; then
    rmdir "$GENLOCK" 2>/dev/null || true
  fi
  rm -rf "$TMP"
  exit $rc
}
trap cleanup EXIT

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

generate() {
  python3 "$ROOT/tools/generate.py" "$1"
}

render() {
  name=${1:?usage: box.sh render <params-name> [ID ...]}
  shift
  had_ids=$#
  lock_acquire || return 1
  rc=0
  generate "$ROOT/params/$name.json" || rc=$?
  if [ "$rc" != 0 ]; then
    lock_release
    return 1
  fi
  if [ "$had_ids" -gt 0 ]; then
    ids="$*"
  else
    ids=$(cd "$CAD/generated/parts" && ls *.scad | sed 's/\.scad$//')
  fi
  lock_release
  mkdir -p "$CAD/stl/$name"
  if [ "$had_ids" -eq 0 ]; then
    rm -f "$CAD/stl/$name"/*.stl
  fi
  status=0
  for id in $ids; do
    echo "== $id"
    if ! "$SCAD" --backend=manifold -o "$CAD/stl/$name/$id.stl" "$CAD/generated/parts/$id.scad" 2>"$TMP/$id.err"; then
      grep -E "$ERRPAT" "$TMP/$id.err" || cat "$TMP/$id.err" >&2
      status=1
    fi
    grep -E "$ERRPAT" "$TMP/$id.err" && status=1
    [ -f "$CAD/stl/$name/$id.stl" ] || { echo "FAILED $id"; status=1; }
  done
  python3 "$ROOT/tools/check_stl.py" "$name" $* || status=1
  return $status
}

tests() {
  lock_acquire || return 1
  rc=0
  generate "$ROOT/params/${1:-bench-600}.json" >/dev/null || rc=$?
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
  lock_release
  passed=0
  for f in $(cd "$CAD/tests" && ls *_test.scad); do
    echo "== $f"
    if "$SCAD" -o "$TMP/$f.echo" "$CAD/tests/$f" 2>&1 | grep -qE "$ERRPAT"; then
      echo "FAILED $f"
    else
      passed=$((passed + 1))
    fi
  done
  if [ "$passed" -ne "$expected" ]; then
    echo "box.sh test: expected $expected test file(s), $passed passed" >&2
    return 1
  fi
  printf '%d test files passed\n' "$passed"
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
  generate "$ROOT/params/${PARAMS:-bench-600}.json" >/dev/null || rc=$?
  if [ "$rc" != 0 ]; then
    lock_release
    return 1
  fi
  lock_release
  QT_QPA_PLATFORM=offscreen "$SCAD" --backend=manifold --render --imgsize=1600,1000 \
    --colorscheme=Tomorrow "$@" -o "$out" "$CAD/$src" 2>&1 | grep -E "$ERRPAT" && return 1
  [ -f "$out" ]
}

cmd=${1:?usage: box.sh render|test|png|ping ...}
shift
case $cmd in
  render) render "$@" ;;
  test) tests "$@" ;;
  png) png "$@" ;;
  ping) echo ok ;;
  *) echo "unknown command $cmd" >&2; exit 2 ;;
esac
