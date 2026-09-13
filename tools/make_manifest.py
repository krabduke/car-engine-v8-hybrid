"""Generate viewer/parts.json from build/parts.csv and engine/spec.py."""

import csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import spec  # noqa: E402

GROUPS = [
    ("01 Block",                   "Block",       "#6E7478"),
    ("02 Bottom End",              "Bottom end",  "#8E939A"),
    ("03 Heads and Valvetrain",    "Heads",       "#7E8A93"),
    ("04 Induction",               "Induction",   "#5A6B74"),
    ("05 Turbo and Exhaust",       "Turbo",       "#A8663C"),
    ("06 Hybrid",                  "Hybrid",      "#C06A30"),
    ("07 Drive and Ancillaries",   "Drive",       "#77706A"),
]


def main():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "build", "parts.csv"))))
    groups = []
    for key, label, colour in GROUPS:
        mine = [r for r in rows if r["collection"] == key]
        if not mine:
            continue
        groups.append({"key": key, "label": label, "color": colour,
                       "parts": len(mine),
                       "faces": sum(int(r["faces"]) for r in mine)})
    parts = {r["name"]: {"g": r["collection"], "mat": r["material"],
                         "x0": float(r["x_min_mm"]), "x1": float(r["x_max_mm"]),
                         "f": int(r["faces"])} for r in rows}
    out = {
        "name": spec.NAME, "config": spec.CONFIG,
        "displacement": spec.swept_volume_cc(),
        "bore": spec.BORE, "stroke": spec.STROKE,
        "cylinders": spec.N_CYL, "v_angle": spec.V_ANGLE,
        "redline": spec.REDLINE_RPM,
        "ice_kw": spec.ICE_POWER_KW, "mguk_kw": spec.MGUK_POWER_KW,
        "mguh_kw": spec.MGUH_POWER_KW, "combined_kw": spec.COMBINED_KW,
        "hp": spec.COMBINED_KW * 1.341,
        "mass": spec.MASS_KG,
        "piston_speed": spec.mean_piston_speed(),
        "specific_kw_l": spec.specific_power_kw_per_litre(),
        "firing_order": spec.FIRING_ORDER,
        "firing_interval": spec.firing_interval(),
        "boost": spec.BOOST_BAR,
        "compression": spec.COMPRESSION_RATIO,
        "palette": {k: {"rgb": list(v[0]), "metal": v[1], "rough": v[2]}
                    for k, v in spec.PALETTE.items()},
        "groups": groups, "parts": parts,
    }
    p = os.path.join(ROOT, "viewer", "parts.json")
    json.dump(out, open(p, "w"), indent=1)
    print(f"  -> {p}  ({len(parts)} parts, {len(groups)} groups)")


if __name__ == "__main__":
    main()
