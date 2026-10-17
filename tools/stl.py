"""Minimal STL reader (binary and ASCII), bounding box, volume, area and closed-shell topology."""
import pathlib
import struct


def load(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 84:
        if data.lstrip().startswith(b"solid") and b"vertex" in data:
            return _ascii(data)
        raise ValueError(f"{path}: not an STL")
    n = struct.unpack_from("<I", data, 80)[0]
    if 84 + 50 * n == len(data):
        return [tuple(struct.unpack_from("<3f", data, 84 + 50 * i + 12 + 12 * k) for k in range(3))
                for i in range(n)]
    return _ascii(data)


def _ascii(data):
    vs = []
    for line in data.decode("ascii", "replace").splitlines():
        if line.strip().startswith("vertex"):
            nums = line.split()[1:]
            if len(nums) != 3:
                raise ValueError(f"vertex line does not have exactly 3 numbers: {line.strip()!r}")
            vs.append(tuple(float(x) for x in nums))
    if not vs or len(vs) % 3:
        raise ValueError("no facets")
    return [tuple(vs[i:i + 3]) for i in range(0, len(vs), 3)]


def bbox(tris):
    pts = [v for t in tris for v in t]
    if not pts:
        raise ValueError("empty mesh")
    return tuple(round(max(p[a] for p in pts) - min(p[a] for p in pts), 3) for a in range(3))


def volume_area(tris):
    v = a = 0.0
    for p, q, r in tris:
        v += (p[0] * (q[1] * r[2] - q[2] * r[1]) - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
        ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        wx, wy, wz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
        a += 0.5 * ((uy * wz - uz * wy) ** 2 + (uz * wx - ux * wz) ** 2 + (ux * wy - uy * wx) ** 2) ** 0.5
    return abs(v) / 1000.0, a / 100.0


def _edges(tri):
    return [tuple(sorted((tri[i], tri[(i + 1) % 3]))) for i in range(3)]


def open_edges(tris):
    count = {}
    for t in tris:
        for e in _edges(t):
            count[e] = count.get(e, 0) + 1
    return sum(1 for n in count.values() if n != 2)


def shell_volumes(tris):
    parent = list(range(len(tris)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first = {}
    for i, t in enumerate(tris):
        for e in _edges(t):
            j = first.setdefault(e, i)
            parent[root(i)] = root(j)
    vols = {}
    for i, (p, q, r) in enumerate(tris):
        v = (p[0] * (q[1] * r[2] - q[2] * r[1]) - p[1] * (q[0] * r[2] - q[2] * r[0])
             + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
        k = root(i)
        vols[k] = vols.get(k, 0.0) + v
    return [v / 1000.0 for v in vols.values()]
