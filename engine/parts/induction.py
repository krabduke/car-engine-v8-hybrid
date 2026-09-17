"""Twin plenums, bank throttles, eight velocity stacks and port injectors.

Injectors, feeds and bank rails illustrate packaging, not calibrated fueling.
Stack lengths illustrate packaging rather than validated acoustic tuning.
Each plenum inlet has one butterfly shared by its bank's four cylinders.
"""

import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spec
import mesh

SM = spec.RES["small_revolve"]
import shapes
import gaspath
from parts import common

I = spec.INTAKE
SEG = spec.RES["revolve"]


def build():
    out = {}
    out.update(_plenum())
    out.update(_trumpets())
    out.update(_injection())
    return out


def _injection():
    out = {}
    rail_points = {0: [], 1: []}
    for n, pair, bank, x, a in spec.cylinders():
        port = gaspath.intake_port(bank, x)
        runner = gaspath.runner_path(bank, x)[-2]
        d, lat = common.bank_dir(bank), common.bank_lat(bank)
        tip = tuple((port[k] + runner[k]) / 2 for k in range(3))
        profile = [(0.0, 0.0), (0.0, 3.0), (12.0, 3.0),
                   (14.0, 7.0), (38.0, 7.0), (40.0, 9.0),
                   (46.0, 9.0), (48.0, 4.0), (48.0, 0.0)]
        verts, faces = mesh.revolve_closed(profile, SM)
        verts = [(tip[0] + py,
                  tip[1] - lat[1] * px + d[1] * pz,
                  tip[2] - lat[2] * px + d[2] * pz)
                 for px, py, pz in verts]
        if lat[1] * d[2] - lat[2] * d[1] < 0.0:
            faces = [tuple(reversed(face)) for face in faces]
        out[f"injector_{n}"] = (verts, faces)
        plug = (tip[0] + 10.0, tip[1] - lat[1] * 28.0,
                tip[2] - lat[2] * 28.0)
        out[f"injector_connector_{n}"] = shapes.connector(*plug, 14.0, 12.0, 10.0, 2)
        inlet = tuple(tip[k] - lat[k] * 48.0 for k in range(3))
        rail = tuple(tip[k] - lat[k] * 68.0 for k in range(3))
        rail_points[bank].append(rail)
        out[f"injector_feed_{n}"] = mesh.pipe([inlet, rail], 3.5, SM)
    ends = []
    for bank, tag in ((0, "l"), (1, "r")):
        points = sorted(rail_points[bank])
        start = (points[0][0] - 18.0, *points[0][1:])
        end = (points[-1][0] + 18.0, *points[-1][1:])
        out[f"fuel_rail_{tag}"] = mesh.pipe([start, *points, end], 7.0, SM)
        ends.append(end)
        out[f"fuel_rail_union_{tag}"] = mesh.pipe(
            [(end[0] - 6.0, *end[1:]), (end[0] + 6.0, *end[1:])], 10.0, 6)
    rear = max(p[0] for p in ends) + 36.0
    out["fuel_rail_crossover"] = mesh.pipe(
        [ends[0], (rear, *ends[0][1:]), (rear, *ends[1][1:]), ends[1]], 4.0, SM)
    return out


def _plenum():
    """A plenum outboard of each bank, feeding that bank's four ports.

    See the note in `spec.INTAKE`: the hot vee puts the intake ports on the
    outside of the heads, so this is where the air has to come from.
    """
    out = {}
    for bank, tag in ((0, "l"), (1, "r")):
        sgn = -1.0 if bank == 0 else 1.0
        y = sgn * I["plenum_y"]
        # A closed vessel with domed ends and a bolted end cap, not an
        # open-ended tube: as a tube it showed two black holes down the
        # front of the engine and held no pressure at all.
        L, R = I["plenum_len"] / 2, I["plenum_r"]
        v, f = mesh.revolve_closed(
            [(-L - 26.0, 0.0), (-L - 24.0, R * 0.34), (-L - 16.0, R * 0.72),
             (-L - 6.0, R * 0.94), (-L, R), (-L + 8.0, R * 1.04),
             (L - 8.0, R * 1.04), (L, R), (L + 6.0, R * 0.94),
             (L + 16.0, R * 0.72), (L + 24.0, R * 0.34), (L + 26.0, 0.0)],
            SEG)
        v = [(x, py + y, pz + I["plenum_z"]) for (x, py, pz) in v]
        out[f"plenum_{tag}"] = (v, f)
        # throttle body on the front face of each
        # body, mounting flange and the butterfly on its spindle
        tr = I["throttle_r"]
        # A stub on the plenum's OUTBOARD face at mid-length.
        #
        # Nowhere else will take it. The front of this engine is a gear
        # tower reaching 241 mm out to drive the cams; aft of the block the
        # car's bodywork has closed in to 252 mm; and the intake camshaft
        # sits directly above the plenum's crown. Outboard is the sidepod,
        # which is 456 mm of room at this height.
        tr = I["throttle_r"]
        h0 = I["plenum_r"] * 0.86
        tparts = [mesh.tube(h0, h0 + 56.0, tr - 7.0, tr, 32)]
        tparts.append(mesh.tube(h0 + 48.0, h0 + 56.0, tr, tr + 10.0, 32))
        tparts.append(mesh.tube(h0, h0 + 7.0, tr, tr + 10.0, 32))
        bv, bf = mesh.revolve_closed(
            [(-2.0, 0.0), (-2.0, tr - 8.0), (2.0, tr - 8.0), (2.0, 0.0)], 32)
        tparts.append(([(px + h0 + 27.0, py, pz) for (px, py, pz) in bv], bf))
        sv, sf = mesh.cylinder(-tr, tr, 4.0, 14)
        tparts.append(([(pz + h0 + 27.0, py, px) for (px, py, pz) in sv], sf))
        tv, tf = mesh.join(*tparts)
        # the lathe runs along its own +x; point it outboard, along y
        tv = [(pz, sgn * px + y, py + I["plenum_z"]) for (px, py, pz) in tv]
        out[f"throttle_{tag}"] = (tv, tf)
    return out


def _trumpets():
    """One velocity stack per cylinder, standing inside its bank's plenum and
    pointing at that cylinder's runner mouth."""
    parts = []
    for (n, pair, bank, x, a) in spec.cylinders():
        sgn = -1.0 if bank == 0 else 1.0
        prof = [(0.0, I["trumpet_r_in"]),
                (I["trumpet_len"] * 0.62, I["trumpet_r_in"]),
                (I["trumpet_len"], I["trumpet_r_out"]),
                (I["trumpet_len"], I["trumpet_r_out"] - 3.0),
                (I["trumpet_len"] * 0.62, I["trumpet_r_in"] - 3.0),
                (0.0, I["trumpet_r_in"] - 3.0)]
        tv, tf = mesh.revolve_closed(prof, 26)
        # the lathe runs along its own +x; the stack points inboard, from the
        # outboard wall of the plenum towards the runner mouth
        tv = [(pz + x,
               sgn * (I["plenum_y"] + I["plenum_r"] * 0.6 - px),
               py + I["plenum_z"])
              for (px, py, pz) in tv]
        parts.append((tv, tf))
    return {"trumpets": mesh.join(*parts)}
