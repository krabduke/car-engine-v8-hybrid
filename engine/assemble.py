"""Build the power unit in Blender. Run under `blender --background`."""

import csv, math, os, sys, time
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import spec              # noqa: E402
import mesh as meshlib   # noqa: E402
import materials         # noqa: E402
from parts import (block, bottomend, heads, plumbing, induction,   # noqa: E402
                   turbo, hybrid, drive, detail, ancillaries, harness)

MM = 0.001
MODULES = [("block", block), ("bottom end", bottomend), ("heads", heads),
           ("plumbing", plumbing),
           ("induction", induction), ("turbo", turbo), ("hybrid", hybrid),
           ("drive", drive), ("detail", detail),
           ("ancillaries", ancillaries), ("harness", harness)]
COLLECTIONS = ["01 Block", "02 Bottom End", "03 Heads and Valvetrain",
               "04 Induction", "05 Turbo and Exhaust", "06 Hybrid",
               "07 Drive and Ancillaries"]


def collection_for(n):
    n = n.lower()
    if n.startswith(("valve_spring", "spring_retainer", "retainer_",
                     "bucket_", "tappet_", "head_stud", "sparkplug",
                     "camcover", "oil_filler", "collets_", "cam_caps")):
        return "03 Heads and Valvetrain"
    if n.startswith(("timing_", "oil_", "coolant_", "sump_bolt", "dry_sump",
                     "sensor", "water_outlet", "gallery_plug", "mount_boss",
                     "scavenge", "thermostat", "belt_", "engine_mount",
                     "knock_")):
        return "07 Drive and Ancillaries"
    if n.startswith(("turbo_wheel", "heat_shield")):
        return "05 Turbo and Exhaust"
    if n.startswith(("crank", "piston", "conrod", "rod_cap", "rings_",
                     "ring_", "gudgeon_", "main_shell", "main_cap",
                     "rod_shell", "rod_bolts")):
        return "02 Bottom End"
    if n.startswith(("head", "cam", "valve", "injector", "coil")):
        return "03 Heads and Valvetrain"
    if n.startswith(("plenum", "trumpet", "throttle", "runner_",
                     "intercooler", "charge_pipe", "blowoff", "pfi_")):
        return "04 Induction"
    if n.startswith(("turbo", "turbine_", "compressor_", "exhaust",
                     "tailpipe", "wastegate", "primary_", "collector_")):
        return "05 Turbo and Exhaust"
    if n.startswith(("mgu", "inverter", "battery", "ecu", "harness")):
        return "06 Hybrid"
    if n.startswith(("flywheel", "clutch", "bellhousing", "pump",
                     "alternator", "starter", "accessory_", "breathers",
                     "catch_tank", "dipstick", "fuel_rail", "fuel_feeds",
                     "hp_fuel_pump")):
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


def apply_cutter(ob, verts, faces):
    """Take a cutter's solid out of `ob` with an exact boolean difference.

    The cutter is authored in world millimetres like everything else and made
    as an object with no transform, so it lines up with `ob` wherever `ob`'s
    origin has been moved to. Returns 1 if the cut went through."""
    cutter = make_object(ob.name + "__cut", verts, faces,
                         bpy.context.scene.collection)
    # an exact boolean reads inside from outside off the normals, and a
    # cutter is joined from pieces authored in whatever winding they came in
    recalc_normals(cutter)
    m = ob.modifiers.new("cut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    # a cutter is often several solids joined, overlapping one another
    m.use_self = True
    m.object = cutter
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
        ok = 1
    except RuntimeError as exc:
        print(f"    ! cut failed on {ob.name}: {exc}")
        ob.modifiers.remove(m)
        ok = 0
    bpy.data.objects.remove(cutter, do_unlink=True)
    return ok


def make_object(name, verts, faces, coll, pivot=None):
    """Build one object. `pivot` (in mm) becomes the object's origin.

    Geometry is authored in world millimetres, so without this every object's
    origin is the world origin -- a piston would travel in an arc about the
    front of the crankcase instead of up and down its own bore. Putting the
    pivot in the object transform exports a glTF node that moves correctly
    for any consumer of the file, not just our viewer.
    """
    px, py, pz = (pivot or (0.0, 0.0, 0.0))
    me = bpy.data.meshes.new(name)
    me.from_pydata([((x - px) * MM, (y - py) * MM, (z - pz) * MM)
                    for (x, y, z) in verts],
                   [], [list(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = (px * MM, py * MM, pz * MM)
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
    # A module may hand back "cut:<part>" entries: solids to take out of a
    # part another module (or the same one) builds -- the bores out of the
    # block, the valve reliefs out of a piston. They are pooled across every
    # module first so a cutter reaches its target wherever that is built.
    built_all, cutters = [], {}
    for label, module in MODULES:
        built = module.build()
        for key, geom in built.items():
            if key.startswith("cut:"):
                cutters.setdefault(key[4:], []).append(geom)
        built_all.append((label, module, built))
    n_cut = n_cut_ok = 0
    for label, module, built in built_all:
        t1 = time.time()
        piv = module.pivots() if hasattr(module, "pivots") else {}
        objects = {k: v for k, v in built.items() if not k.startswith("cut:")}
        for name, (v, f) in sorted(objects.items()):
            cname = collection_for(name)
            spec_p = piv.get(name)
            ob = make_object(name, v, f, cols[cname],
                             pivot=spec_p[0] if spec_p else None)
            # outward before cutting, not only after: the boolean takes the
            # part's inside from its normals too, and 187 parts here have
            # pieces authored inside out
            if name in cutters:
                recalc_normals(ob)
            for cv, cf in cutters.get(name, ()):
                n_cut += 1
                n_cut_ok += apply_cutter(ob, cv, cf)
            recalc_normals(ob)
            mname = material_for(name)
            ob.data.materials.append(mats[mname])
            n_sharp += shade(ob)
            # World bounds computed directly: matrix_world lags an origin
            # move, and the transform here is a pure translation anyway.
            lx, ly, lz = ob.location
            bb = meshlib.bbox([(x.co.x + lx, x.co.y + ly, x.co.z + lz)
                               for x in ob.data.vertices])
            ax = spec_p[1] if spec_p else ("", "", "")
            rows.append({
                "name": name, "collection": cname, "material": mname,
                "pivot_x_mm": round(spec_p[0][0], 2) if spec_p else "",
                "pivot_y_mm": round(spec_p[0][1], 2) if spec_p else "",
                "pivot_z_mm": round(spec_p[0][2], 2) if spec_p else "",
                "axis_x": ax[0], "axis_y": ax[1], "axis_z": ax[2],
                "spin": spec_p[2] if spec_p and len(spec_p) > 2 else "",
                "role": spec_p[3] if spec_p and len(spec_p) > 3 else "",
                "cyl": spec_p[4] if spec_p and len(spec_p) > 4 else "",
                "verts": len(ob.data.vertices), "faces": len(ob.data.polygons),
                "x_min_mm": round(bb[0]/MM, 1), "x_max_mm": round(bb[3]/MM, 1),
                "y_min_mm": round(bb[1]/MM, 1), "y_max_mm": round(bb[4]/MM, 1),
                "z_min_mm": round(bb[2]/MM, 1), "z_max_mm": round(bb[5]/MM, 1),
            })
        print(f"  [{label}] {len(objects)} objects in {time.time()-t1:.1f}s")

    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    p = os.path.join(ROOT, "build", "parts.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    tv = sum(r["verts"] for r in rows); tf = sum(r["faces"] for r in rows)
    print(f"\n{len(rows)} objects | {tv:,} verts | {tf:,} faces | sharp {n_sharp:,}"
          f" | cuts {n_cut_ok}/{n_cut}")
    if n_cut_ok < n_cut:
        # a cut that did not go through leaves the material it was meant to
        # remove, and nothing downstream can tell
        raise SystemExit(f"{n_cut - n_cut_ok} cuts failed")
    blend = os.path.join(ROOT, "build", "engine.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print(f"blend -> {blend}\ntotal {time.time()-t0:.1f}s")


if __name__ == "__main__":
    # Blender exits 0 even when a background script raises, so a build that
    # dropped a whole module -- every mount, the belt drive, the charge
    # pipework -- printed a traceback into the log and then reported
    # success. `make verify` then ran against a model with those parts
    # missing and passed, because the gates only see what is there. Fail
    # loudly instead: print the traceback and hand back a non-zero status
    # that make will stop on.
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
