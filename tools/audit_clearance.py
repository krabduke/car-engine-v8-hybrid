"""Check that parts which must not touch each other really do not.

The bounding-box version of this test could only ever be right for parts that
are roughly the shape of their box. It caught the hybrid pack sitting 46 mm up
inside the oil pan, because both were slabs -- and then flagged the fixed pack
as a 58 mm overlap, because two lobes straddling the sump keel have a box that
encloses the sump entirely while the lobes themselves are 6 mm clear of it.

So this works on the geometry. Both parts are built from the pure-Python layer,
one is bucketed into a grid the size of the clearance being tested, and every
vertex of the other is checked against the 27 cells around it. That is linear
in the vertex count, and it is measuring the parts rather than their shadows.

    python3 tools/audit_clearance.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "engine"))

import spec
from parts import (block, bottomend, heads, plumbing, induction, turbo,
                   hybrid, drive, detail)

# (part, part, millimetres they must keep apart, why)
PAIRS = [
    ("battery", "sump", 4.0, "the pack was 46 mm up inside the oil pan"),
    ("battery", "sump_drain", 3.0, "and the drain plug was inside the pack"),
    ("battery_modules", "sump", 4.0, "same, one layer in"),
    ("battery", "crankshaft", 6.0, "the pack must clear the rotating assembly"),
    ("turbos", "camcover_l", 5.0, "the turbos live in the vee, not in a head"),
    ("turbos", "camcover_r", 5.0, "the turbos live in the vee, not in a head"),
    # one plenum per bank, outboard of its own cam cover: this is a hot
    # vee, so the induction cannot be in the vee with the turbochargers
    ("plenum_l", "camcover_l", 3.0, "the plenum sits outboard of the cover"),
    ("plenum_r", "camcover_r", 3.0, "the plenum sits outboard of the cover"),
    ("flywheel", "bedplate", 3.0, "the flywheel has to turn"),
    ("flywheel", "sump", 3.0, "the flywheel has to turn"),
]


def min_distance(a, b, want):
    """Smallest vertex-to-vertex distance between two point clouds, stopping
    as soon as it is known to be under `want`."""
    cell = max(want, 1e-3)
    grid = {}
    for (x, y, z) in b:
        k = (int(math.floor(x / cell)), int(math.floor(y / cell)),
             int(math.floor(z / cell)))
        grid.setdefault(k, []).append((x, y, z))
    best = float("inf")
    for (x, y, z) in a:
        kx = int(math.floor(x / cell))
        ky = int(math.floor(y / cell))
        kz = int(math.floor(z / cell))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for (bx, by, bz) in grid.get((kx + dx, ky + dy, kz + dz), ()):
                        d = math.dist((x, y, z), (bx, by, bz))
                        if d < best:
                            best = d
                            if best < want * 0.05:
                                return best
    return best


def check():
    built = {}
    for m in (block, bottomend, heads, plumbing, induction, turbo,
              hybrid, drive, detail):
        built.update(m.build())
    bad = []
    for (a, b, want, why) in PAIRS:
        if a not in built or b not in built:
            bad.append((f"{a} / {b}", "one of the pair does not exist", why))
            continue
        d = min_distance(built[a][0], built[b][0], want)
        if d < want:
            bad.append((f"{a} / {b}",
                        f"{d:.1f} mm apart, needs {want:.1f} mm", why))
    return bad, len(PAIRS)


if __name__ == "__main__":
    bad, n = check()
    if not bad:
        print(f"PASS  all {n} clearances hold")
        sys.exit(0)
    print(f"FAIL  {len(bad)} of {n} clearances\n")
    for pair, what, why in bad:
        print(f"  {pair:34s} {what}")
        print(f"  {'':34s} ({why})")
    sys.exit(1)
