"""Crank and turbo machine envelopes, inverter and split sidepod store.

Finned cases and machine envelopes illustrate packaging, not validated cooling
or electromagnetic internals. The HV loom illustrates connections only; it is
not an electrically certified routing, insulation or thermal design.
"""

import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spec
import mesh

SM = spec.RES["small_revolve"]
import shapes
from parts import common

Y = spec.HYBRID
SEG = spec.RES["revolve"]


def build():
    out = {}
    out.update(_mguk())
    out.update(_mguh())
    out.update(_electronics())
    out.update(_hv_loom())
    return out


def _hv_loom():
    ix, iy, iz = Y["inverter_pos"]
    iw, _, ih = Y["inverter"]
    bx, by, bz = Y["battery_pos"]
    bw, bd, bh = Y["battery"]
    rear = ix + iw / 2 + 38.0
    side = max(spec.INTAKE["plenum_y"] + spec.INTAKE["plenum_r"] + 24.0,
               abs(by) + bd / 2 + 24.0)
    low = bz + bh / 2 + 35.0
    out = {}
    out["inverter_connectors"] = mesh.join(*[
        shapes.connector(ix + sgn * (iw / 2 + 12.0), iy, iz + ih * 0.1,
                         28.0, 22.0, 16.0, 8)
        for sgn in (-1.0, 1.0)])
    out["battery_terminals"] = mesh.join(*[
        shapes.connector(bx - sgn * bw * 0.3, by + sgn * bd * 0.38,
                         bz + bh / 2 + 7.0, 34.0, 20.0, 14.0, 2)
        for sgn in (1.0, -1.0)])
    for sgn, tag in ((-1.0, "l"), (1.0, "r")):
        source = (ix + sgn * (iw / 2 + 12.0), iy, iz + ih * 0.1)
        terminal = (bx - sgn * bw * 0.3, by + sgn * bd * 0.38,
                    bz + bh / 2 + 7.0)
        path = [source, (source[0], sgn * side, source[2]),
                (rear, sgn * side, source[2]), (rear, sgn * side, low),
                (terminal[0], sgn * side, low),
                (terminal[0], terminal[1], low), terminal]
        out[f"hv_store_{tag}"] = mesh.pipe(path, 5.0, SM)
    motor = (Y["mguk_x"], -Y["mguk_r"], 0.0)
    source = (ix - iw / 2 - 12.0, iy, iz + ih * 0.1)
    path = [source, (source[0], -side, source[2]),
            (rear, -side, source[2]), (rear, -side, low + 16.0),
            (motor[0], -side, low + 16.0), (motor[0], -side, 0.0), motor]
    out["hv_motor_k"] = mesh.pipe(path, 6.0, SM)
    out["hv_motor_k_connector"] = shapes.connector(*motor, 24.0, 20.0, 18.0, 3)
    for index, x in enumerate(spec.TURBO["x"]):
        sgn = -1.0 if index % 2 == 0 else 1.0
        terminal = (x, sgn * Y["mguh_r"], spec.TURBO["z"])
        source = (ix + sgn * (iw / 2 + 12.0), iy, iz + ih * 0.1)
        high = spec.TURBO["z"] + Y["mguh_r"] + 100.0
        path = [source, (source[0], sgn * side, source[2]),
                (source[0], sgn * side, high), (x, sgn * side, high),
                (x, terminal[1], high), terminal]
        out[f"hv_motor_h_{index}"] = mesh.pipe(path, 4.0, SM)
        out[f"hv_motor_h_connector_{index}"] = shapes.connector(
            *terminal, 18.0, 16.0, 14.0, 3)
    return out


def _mguk():
    """Crankshaft motor-generator packaging envelope."""
    v, f = mesh.tube(Y["mguk_x"] - Y["mguk_len"] / 2, Y["mguk_x"] + Y["mguk_len"] / 2,
                     spec.CRANK["nose_r"] + 4.0, Y["mguk_r"], SEG)
    fins = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        fv, ff = shapes.rounded_box(Y["mguk_x"], Y["mguk_r"] + 5.0, 0.0,
                                    Y["mguk_len"] * 0.86, 11.0, 3.0, 1.2)
        fins.append((mesh.rot_x(fv, a), ff))
    return {"mguk": mesh.join((v, f), *fins)}


def _mguh():
    """Turbo-shaft motor-generator packaging envelopes."""
    parts = []
    for x in spec.TURBO["x"]:
        v, f = mesh.tube(x - Y["mguh_len"] / 2, x + Y["mguh_len"] / 2,
                         spec.TURBO["shaft_r"] * 2.5, Y["mguh_r"], SM)
        v = [(px, py, pz + spec.TURBO["z"]) for (px, py, pz) in v]
        parts.append((v, f))
    return {"mguh": mesh.join(*parts)}


def _electronics():
    """Finned inverter, split energy-store and ECU packaging with connectors."""
    out = {}
    ix, iy, iz = Y["inverter_pos"]
    sx, sy, sz = Y["inverter"]
    out["inverter"] = shapes.finned_case(ix, iy, iz, sx, sy, sz,
                                         n_fins=11, fin_h=9.0, fin_t=3.4,
                                         r=7.0, axis="x")
    out["inverter_connectors"] = mesh.join(
        shapes.connector(ix - sx * 0.5 - 12.0, iy, iz + sz * 0.1, 28.0, 22.0, 16.0, 8),
        shapes.connector(ix + sx * 0.5 + 12.0, iy, iz + sz * 0.1, 28.0, 22.0, 16.0, 8))

    bx, by, bz = Y["battery_pos"]
    sx, sy, sz = Y["battery"]
    # Two flat lobes straddling the sump keel, not one slab hung underneath
    # it. Underneath, the pack was either inside the oil pan or -- once it had
    # been dropped clear of it -- 106 mm below the floor of the engine bay
    # when this engine is installed in the car. Beside the keel it clears the
    # sump and stays inside the bay, which is also where a real energy store
    # goes: low and flat, either side of the centreline.
    # Each lobe's inboard face is set from the pan's own half-width, so the
    # clearance holds if the pan is ever reshaped -- rather than from a
    # fraction that happened to look right once.
    lobe_y = sy * 0.28
    inner = spec.ANCILLARY["sump_w"] / 2 + 10.0
    lobe_c = inner + lobe_y / 2
    out["battery"] = mesh.join(*[
        shapes.finned_case(bx, by + sgn * lobe_c, bz,
                           sx, lobe_y, sz, n_fins=14, fin_h=5.0, fin_t=3.0,
                           r=8.0, axis="x", side=-1.0)
        for sgn in (-1.0, 1.0)])
    # the modules inside it, visible when the case is hidden
    mods = []
    for i in range(6):
        f = (i + 0.5) / 6
        for sgn in (-1.0, 1.0):
            mods.append(shapes.rounded_box(
                bx - sx / 2 + sx * f, by + sgn * lobe_c, bz,
                sx / 7.6, lobe_y * 0.78, sz * 0.72, 4.0))
    # a through-bolt strap: without it the modules float inside a case they
    # never touch. The strap crosses both lobes and pierces their walls, so
    # the pack is one structurally honest object.
    mods.append(shapes.rounded_box(
        bx, by, bz, sx * 0.42, lobe_c * 2 + lobe_y, sz * 0.30, 3.0))
    out["battery_modules"] = mesh.join(*mods)
    out["battery_terminals"] = mesh.join(
        # outboard of the bedplate, which fills the middle of this face
        shapes.connector(bx - sx * 0.3, by + sy * 0.38, bz + sz * 0.5 + 7.0,
                         34.0, 20.0, 14.0, 2),
        shapes.connector(bx + sx * 0.3, by - sy * 0.38, bz + sz * 0.5 + 7.0,
                         34.0, 20.0, 14.0, 2))

    a = spec.ANCILLARY
    sx, sy, sz = a["ecu"]
    # On top of the right bank's plenum. At y 132 it was inside the cam
    # cover, the camshaft and four of the lobes.
    # Low on the block's right flank, below the plenum and outboard of
    # the engine mounts. On top of the plenum it was inside the cam cover;
    # directly under it, it was in the intake runners.
    ey, ez = 206.0, -80.0
    out["ecu"] = shapes.finned_case(0.0, ey, ez, sx, sy, sz,
                                    n_fins=9, fin_h=5.0, fin_t=2.6, r=5.0)
    out["ecu_connector"] = shapes.connector(-sx * 0.5 - 10.0, ey, ez,
                                            22.0, sy * 0.6, sz * 0.5, 10)
    return out
