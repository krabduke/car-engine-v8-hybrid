"""Check the built power unit against spec.py by measurement and design rule.

Dimensions come from build/parts.csv. The engineering checks are computed from
spec.py -- for an engine those are the numbers that decide whether it is a
coherent design rather than a shape that resembles one.
"""

import csv, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import spec  # noqa: E402


class Check:
    def __init__(self):
        self.fails, self.n = [], 0

    def band(self, label, got, lo, hi, unit="", note=""):
        self.n += 1
        if lo <= got <= hi:
            print(f"  ok  {label:42s} {got:9.3f}{unit}  [{lo:g}..{hi:g}] {note}")
            return True
        self.fails.append(f"{label}: {got:.3f}{unit} outside [{lo:g}..{hi:g}]")
        return False

    def true(self, label, cond, detail=""):
        self.n += 1
        if cond:
            print(f"  ok  {label:42s} {detail}")
            return True
        self.fails.append(f"{label}: {detail}")
        return False


def main():
    path = os.path.join(ROOT, "build", "parts.csv")
    if not os.path.exists(path):
        print("build/parts.csv missing -- run `make build` first")
        return 1
    rows = list(csv.DictReader(open(path)))
    by = {r["name"]: r for r in rows}
    f = lambda r, k: float(r[k])
    c = Check()

    print("\nARCHITECTURE")
    c.band("swept volume", spec.swept_volume_cc(), 1995.0, 2005.0, " cc",
           f"{spec.N_CYL} x {spec.BORE:.0f} x {spec.STROKE:.1f} mm")
    c.band("bore/stroke ratio", spec.bore_stroke_ratio(), 1.45, 2.20, "",
           "oversquare, for revs")
    c.band("rod/stroke ratio", spec.rod_stroke_ratio(), 1.60, 2.15, "",
           "limits piston side load")
    c.band("compression ratio", spec.COMPRESSION_RATIO, 11.0, 16.0, ":1")

    print("\nKINEMATICS")
    # If the deck is not exactly throw + rod + compression height, the piston
    # either never reaches the deck or tries to hit the head.
    c.band("deck height vs slider-crank", spec.DECK_HEIGHT,
           spec.required_deck_height() - 0.6, spec.required_deck_height() + 0.6,
           " mm", f"needs {spec.required_deck_height():.2f}")
    c.band("mean piston speed at redline", spec.mean_piston_speed(), 0.0, 26.0,
           " m/s", f"at {spec.REDLINE_RPM:.0f} rpm")
    c.band("firing interval", spec.firing_interval(), 89.9, 90.1, " deg",
           "even")
    c.true("firing order is a permutation of all cylinders",
           sorted(spec.FIRING_ORDER) == list(range(1, spec.N_CYL + 1)),
           str(spec.FIRING_ORDER))
    c.true("flat-plane crankpins",
           set(spec.CRANKPIN_ANGLES) == {0.0, 180.0}
           and len(spec.CRANKPIN_ANGLES) == spec.N_CYL // 2,
           f"{spec.CRANKPIN_ANGLES}")
    # A flat-plane V8 only fires evenly at 90 degrees included.
    c.band("bank angle for even firing", spec.V_ANGLE, 89.9, 90.1, " deg")

    print("\nOUTPUT")
    c.band("specific power", spec.specific_power_kw_per_litre(), 250.0, 450.0,
           " kW/L", f"{spec.ICE_POWER_KW:.0f} kW ICE")
    c.band("combined power", spec.COMBINED_KW, 800.0, 1100.0, " kW",
           f"{spec.COMBINED_KW*1.341:.0f} hp")
    c.band("power to weight", spec.power_to_weight_kw_per_kg(), 4.0, 9.0,
           " kW/kg", f"{spec.MASS_KG:.0f} kg")
    c.true("hybrid share is credible",
           0.15 <= (spec.MGUK_POWER_KW + spec.MGUH_POWER_KW) / spec.COMBINED_KW <= 0.45,
           f"{(spec.MGUK_POWER_KW+spec.MGUH_POWER_KW)/spec.COMBINED_KW*100:.0f} % of combined")

    print("\nPACKAGING")
    x0 = min(f(r, "x_min_mm") for r in rows); x1 = max(f(r, "x_max_mm") for r in rows)
    y0 = min(f(r, "y_min_mm") for r in rows); y1 = max(f(r, "y_max_mm") for r in rows)
    z0 = min(f(r, "z_min_mm") for r in rows); z1 = max(f(r, "z_max_mm") for r in rows)
    c.band("overall length", x1 - x0, 0, 1000.0, " mm")
    c.band("overall width", y1 - y0, 0, 900.0, " mm")
    c.band("overall height", z1 - z0, 0, 800.0, " mm")
    print(f"      envelope {x1-x0:.0f} x {y1-y0:.0f} x {z1-z0:.0f} mm")

    # pistons must stay inside their bores
    if "pistons" in by:
        pz = f(by["pistons"], "z_max_mm")
        deck_z = spec.DECK_HEIGHT * math.cos(math.radians(spec.V_ANGLE / 2))
        c.true("pistons stay below the deck", pz <= spec.DECK_HEIGHT + 1.0,
               f"crown max z {pz:.1f} mm, deck {spec.DECK_HEIGHT:.1f} along bore")

    print("\nCOMPLETENESS")
    # every per-cylinder and per-valve part, counted. These are the checks
    # that keep the valvetrain honest as it is split up or rebuilt.
    n_valves = spec.N_CYL * spec.VALVE["n_per_cyl"]
    for stem, want_n in (("valve_in", n_valves // 2), ("valve_ex", n_valves // 2),
                         ("camlobe", n_valves), ("valve_spring", n_valves),
                         ("retainer", n_valves), ("tappet", n_valves),
                         ("injector", spec.N_CYL), ("coil", spec.N_CYL),
                         ("sparkplug", spec.N_CYL)):
        have = [k for k in by if k.startswith(stem + "_")]
        c.true(f"{stem} count", len(have) == want_n,
               f"{len(have)} of {want_n}")

    for stem in ("piston", "gudgeon_pin", "conrod", "rod_cap",
                 "ring_top", "ring_second", "ring_oil",
                 "primary", "runner"):
        have = [k for k in by if k.startswith(stem + "_")]
        c.true(f"{stem} per cylinder", len(have) == spec.N_CYL,
               f"{len(have)} of {spec.N_CYL}")
    want = ["block_crankcase", "bedplate", "sump", "crankshaft",
            "head_l", "head_r", "camshaft_l_in", "camshaft_r_ex",
            "valve_in_1_1", "valve_ex_8_2", "camlobe_l_in_1_1",
            "injector_1", "coil_8", "sparkplug_4",
            "valve_spring_1_0", "retainer_8_3", "tappet_5_2",
            "collets_in_1_1", "main_shell_3_upper", "rod_shell_5_lower",
            "main_cap_2", "cam_caps", "rod_bolts", "fuel_rail_l",
            "collector_1", "alternator", "starter", "catch_tank",
            "plenum", "throttle", "turbos", "flywheel", "clutch",
            "mguk", "mguh", "ecu", "pump_oil", "pump_water",
            # without this the engine cannot be timed or started
            "crank_trigger"]
    missing = [w for w in want if w not in by]
    c.true("key components present", not missing, f"{len(want)} checked")
    for m in missing:
        c.fails.append(f"missing component: {m}")
    c.true("every object has a material", all(r["material"] for r in rows),
           f"{len(rows)} objects")
    # A name in MATERIAL_MAP that is not in PALETTE silently falls back to the
    # default, so a part comes out the wrong material and nothing says so.
    # Caught exactly that on the turbofan: six parts were assigned a
    # "steel_polished" that does not exist -- the palette calls it "steel".
    unknown = sorted({v for v in spec.MATERIAL_MAP.values()
                      if v not in spec.PALETTE})
    c.true("every material name is real", not unknown,
           f"{len(spec.PALETTE)} in palette"
           + (f", unknown: {', '.join(unknown)}" if unknown else ""))
    c.true("no empty meshes", all(int(r["verts"]) > 0 for r in rows), "all non-empty")

    print("\n" + "=" * 66)
    if c.fails:
        print(f"FAIL  {len(c.fails)} of {c.n} checks")
        for x in c.fails:
            print("   x " + x)
        return 1
    print(f"PASS  all {c.n} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
