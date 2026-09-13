"""Build the power unit in Blender. Run under `blender --background`."""

import csv, math, os, sys, time
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import spec              # noqa: E402
import mesh as meshlib   # noqa: E402
import materials         # noqa: E402
from parts import (block, bottomend, heads, induction,   # noqa: E402
                   turbo, hybrid, drive)

MM = 0.001
MODULES = [("block", block), ("bottom end", bottomend), ("heads", heads),
           ("induction", induction), ("turbo", turbo), ("hybrid", hybrid),
           ("drive", drive)]
COLLECTIONS = ["01 Block", "02 Bottom End", "03 Heads and Valvetrain",
               "04 Induction", "05 Turbo and Exhaust", "06 Hybrid",
               "07 Drive and Ancillaries"]


def collection_for(n):
    n = n.lower()
    if n.startswith(("crank", "piston", "conrod")):
        return "02 Bottom End"
    if n.startswith(("head", "cam", "valve", "injector", "coil")):
        return "03 Heads and Valvetrain"
    if n.startswith(("plenum", "trumpet", "throttle")):
        return "04 Induction"
    if n.startswith(("turbo", "exhaust", "tailpipe", "wastegate")):
        return "05 Turbo and Exhaust"
    if n.startswith(("mgu", "inverter", "battery", "ecu")):
        return "06 Hybrid"
    if n.startswith(("flywheel", "clutch", "bellhousing", "pump")):
        return "07 Drive and Ancillaries"
    return "01 Block"


def material_for(name):
    n = name.lower()
    best, bl = spec.DEFAULT_MATERIAL, -1
    for k, m in spec.MATERIAL_MAP.items():
        if k in n and len(k) > bl:
            best, bl = m, len(k)
    return best


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "MILLIMETERS"


def make_object(name, verts, faces, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x * MM, y * MM, z * MM) for (x, y, z) in verts],
                   [], [list(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def recalc_normals(obj):
    """Outward normals from winding. Every part here is a closed manifold, so
    Blender resolves this reliably -- more robust than getting face order right
    by hand for parts that are rotated onto two different bank angles."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def shade(obj, angle_deg=34.0):
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    limit = math.cos(math.radians(angle_deg))
    normals = [tuple(p.normal) for p in me.polygons]
    by_edge = {}
    for pi, poly in enumerate(me.polygons):
        for ek in poly.edge_keys:
            by_edge.setdefault(ek, []).append(pi)
    edges = {e.key: e for e in me.edges}
    n = 0
    for ek, fs in by_edge.items():
        e = edges.get(ek)
        if e is None:
            continue
        if len(fs) != 2:
            e.use_edge_sharp = True; n += 1; continue
        a, b = normals[fs[0]], normals[fs[1]]
        if sum(p * q for p, q in zip(a, b)) < limit:
            e.use_edge_sharp = True; n += 1
    return n


def main():
    t0 = time.time()
    clear_scene()
    mats = materials.build_all()
    cols = {}
    for c in COLLECTIONS:
        col = bpy.data.collections.new(c)
        bpy.context.scene.collection.children.link(col)
        cols[c] = col

    rows, n_sharp = [], 0
    for label, module in MODULES:
        t1 = time.time()
        built = module.build()
        for name, (v, f) in sorted(built.items()):
            cname = collection_for(name)
            ob = make_object(name, v, f, cols[cname])
            recalc_normals(ob)
            mname = material_for(name)
            ob.data.materials.append(mats[mname])
            n_sharp += shade(ob)
            bb = meshlib.bbox([tuple(x.co) for x in ob.data.vertices])
            rows.append({
                "name": name, "collection": cname, "material": mname,
                "verts": len(ob.data.vertices), "faces": len(ob.data.polygons),
                "x_min_mm": round(bb[0]/MM, 1), "x_max_mm": round(bb[3]/MM, 1),
                "y_min_mm": round(bb[1]/MM, 1), "y_max_mm": round(bb[4]/MM, 1),
                "z_min_mm": round(bb[2]/MM, 1), "z_max_mm": round(bb[5]/MM, 1),
            })
        print(f"  [{label}] {len(built)} objects in {time.time()-t1:.1f}s")

    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    p = os.path.join(ROOT, "build", "parts.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    tv = sum(r["verts"] for r in rows); tf = sum(r["faces"] for r in rows)
    print(f"\n{len(rows)} objects | {tv:,} verts | {tf:,} faces | sharp {n_sharp:,}")
    blend = os.path.join(ROOT, "build", "engine.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print(f"blend -> {blend}\ntotal {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
