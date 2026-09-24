"""Does the engine hold together, and does each circuit run end to end?

    python3 tools/audit_joints.py

Every other audit here is one-sided. `audit_intersect` lists parts sharing
material and `audit_clearance` lists parts that got too close -- both are
looking for things that touch when they should not. A charge pipe that stops
40 mm short of the throttle it feeds passes both, because not touching is
exactly what they want to see. So does a flywheel bolted to nothing.

That is the defect this catches, and it is the commonest one in a model built
a part at a time: something moves, the thing that lands on it does not, and
the only witness is a render from the one angle where the joint is not hidden
behind a cam cover.

`audit_intersect.EXPECTED` is nearly this list already -- ("crankshaft",
"flywheel") means the two are meant to be one assembly -- but it is a
permission, not a requirement. Nothing there fails when the flywheel drifts
off the crank nose; the entry just stops applying. The circuits below are the
same knowledge stated as an obligation.

Three checks:

  ASSEMBLY   every part is attached to the engine, however indirectly
  CIRCUITS   the gas, oil, coolant, fuel and drive paths are continuous
  MODULES    no two modules build a part under the same name

CONTACT_MM is 2.0. Parts that bolt together in this model interpenetrate --
that is what every entry in EXPECTED says -- so anything further apart than a
gasket's thickness is not a joint.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _joints  # noqa: E402

CONTACT_MM = 2.0
ROOT_PART = "block_crankcase"

# Cylinders 1,3,5,7 are the left bank and 2,4,6,8 the right; the two turbos
# are fore and aft on the centreline, so each takes four cylinders across
# both banks. Firing order 1-8-3-6-4-5-2-7 alternates between those two
# groups every event, which is what gives each turbine evenly spaced pulses
# off a cross-plane crank.
CIRCUITS = [
    ("charge, front turbo to the left bank",
     ["compressor_inlet_1", "compressor_housing_1", "charge_pipes",
      "throttle_l", "plenum_l", "runner_1", "head_l"]),
    ("charge, rear turbo to the right bank",
     ["compressor_inlet_2", "compressor_housing_2", "charge_pipes",
      "throttle_r", "plenum_r", "runner_2", "head_r"]),
    ("charge cooling: the core stands in the plenum it cools",
     ["plenum_l", "intercooler_l"]),
    ("charge cooling, right",
     ["plenum_r", "intercooler_r"]),
    ("boost relief",
     ["charge_pipes", "blowoff"]),

    ("exhaust, cylinder 1 to the front turbine",
     ["head_l", "exhaust_flange_l", "primary_1", "collector_1",
      "turbine_housing_1", "tailpipes"]),
    ("exhaust, cylinder 6 to the rear turbine",
     ["head_r", "exhaust_flange_r", "primary_6", "collector_2",
      "turbine_housing_2", "tailpipes"]),
    ("boost control, front",
     ["turbine_housing_1", "wastegate_1", "compressor_housing_1"]),
    ("boost control, rear",
     ["turbine_housing_2", "wastegate_2", "compressor_housing_2"]),

    ("the front turbocharger is one machine",
     ["turbine_housing_1", "turbo_centre_1", "compressor_housing_1"]),
    ("the rear turbocharger is one machine",
     ["turbine_housing_2", "turbo_centre_2", "compressor_housing_2"]),
    ("front turbo shaft",
     ["turbine_wheel_1", "turbo_shaft_1", "compressor_wheel_1"]),
    ("rear turbo shaft",
     ["turbine_wheel_2", "turbo_shaft_2", "compressor_wheel_2"]),

    ("oil: pan to pump to tank",
     ["sump", "oil_pickup", "dry_sump_lines", "pump_oil"]),
    ("oil: the scavenge stages discharge into the tank",
     ["pump_oil", "dry_sump_lines", "catch_tank"]),
    ("oil: tank to cooler to filter to the gallery",
     ["catch_tank", "dry_sump_lines", "oil_cooler", "oil_filter",
      "gallery_plugs"]),
    ("oil to the front bearing housing",
     ["block_bank_l", "turbo_oil_1", "turbo_centre_1"]),
    ("oil to the rear bearing housing",
     ["block_bank_r", "turbo_oil_2", "turbo_centre_2"]),

    ("coolant: pump to the block",
     ["pump_water", "coolant_plumbing", "block_crankcase"]),
    ("coolant: block to head to the outlet",
     ["block_bank_l", "head_l", "water_outlets"]),
    ("coolant: outlet to the thermostat and back to the pump",
     ["water_outlets", "coolant_plumbing", "timing_cover", "thermostat",
      "coolant_plumbing", "pump_water"]),

    ("fuel, high pressure: pump to rail to direct injector",
     ["hp_fuel_pump", "fuel_hp_line", "fuel_rail_di_r", "fuel_feeds_di_r",
      "injector_di_2"]),
    ("fuel, high pressure: across to the other bank",
     ["fuel_rail_di_r", "fuel_rail_di_crossover", "fuel_rail_di_l",
      "fuel_feeds_di_l", "injector_di_1"]),
    ("fuel, port: rail to feed to injector",
     ["fuel_rail_pfi_l", "pfi_feed_1", "pfi_injector_1"]),
    ("fuel, port: the crossover ties the two rails",
     ["fuel_rail_pfi_l", "fuel_rail_pfi_crossover", "fuel_rail_pfi_r"]),

    ("crankcase breather to the catch tank",
     ["camcover_l", "breathers", "catch_tank"]),

    ("drive: crank to flywheel to clutch, inside the bellhousing",
     ["crankshaft", "flywheel", "clutch"]),
    ("the bellhousing closes onto the block",
     ["block_crankcase", "bellhousing"]),
    ("cam drive",
     ["crankshaft", "timing_gears", "camshaft_l_in"]),
    ("accessory drive: crank to belt to the water pump",
     ["crank_damper", "accessory_belt", "pump_water"]),
    ("accessory drive: the belt turns the alternator",
     ["accessory_belt", "accessory_pulleys", "alternator"]),
    ("accessory drive: idler and tensioner on the timing case",
     ["accessory_belt", "belt_idler", "timing_cover", "belt_tensioner",
      "accessory_belt"]),
    ("the engine hangs on its mounts",
     ["block_crankcase", "mount_bosses", "engine_mount_l"]),
    ("the MGU-K rides on the crank nose",
     ["crankshaft", "mguk"]),
    ("the MGU-H rides on the turbo shafts",
     ["turbo_shaft_1", "mguh"]),

    ("high voltage: pack to the machines",
     ["battery", "battery_terminals", "hv_store_1"]),
    ("engine management is bolted to the engine",
     ["block_crankcase", "mount_bosses", "engine_mount_r", "ecu",
      "ecu_connector"]),
]


def main():
    parts, collisions, cut_owner, built_by, failures = _joints.load(
        ROOT, "engine/parts")
    bad = []

    print(f"\n{len(parts)} parts from {len(set(built_by.values()))} modules")

    print("\nMODULES")
    for name, why in failures:
        print(f"  x   {name:22s} did not build: {why}")
        bad.append(f"{name} did not build")
    for key, first, second in collisions:
        print(f"  x   {key:22s} built by both {first} and {second}")
        bad.append(f"{key} is built twice")
    for target, owners in sorted(cut_owner.items()):
        for owner in owners:
            if target not in built_by:
                print(f"  x   {target:22s} cut declared by {owner}, and"
                      f" nothing builds it -- the cutter has no target")
                bad.append(f"{target} cutter from {owner} has no target")
    if not failures and not collisions:
        print("  ok  every part name is built once, by one module")

    print(f"\nASSEMBLY  (contact within {CONTACT_MM:g} mm)")
    graph = _joints.contact_graph(parts, CONTACT_MM)
    groups = _joints.components(graph)
    main_group = next((g for g in groups if ROOT_PART in g), set())
    loose = [g for g in groups if g is not main_group]
    if not loose:
        print(f"  ok  all {len(main_group)} parts hang together off"
              f" {ROOT_PART}")
    for g in loose:
        names = ", ".join(sorted(g))
        print(f"  x   detached from the engine: {names}")
        bad.append(f"detached: {names}")

    print("\nCIRCUITS")
    for label, chain in CIRCUITS:
        breaks = _joints.broken_links(parts, graph, chain)
        if not breaks:
            print(f"  ok  {label}")
            continue
        for (_i, a, b, why) in breaks:
            extra = ""
            if why == "no contact":
                A, B = _joints.match(parts, a), _joints.match(parts, b)
                d = min(_joints.gap(parts[x], parts[y])
                        for x in A for y in B)
                extra = f" ({d:.0f} mm apart)"
            print(f"  x   {label}: {a} -> {b}, {why}{extra}")
            bad.append(f"{label}: {a} -> {b} {why}")

    print()
    if not bad:
        print(f"PASS  the engine is one assembly and every circuit is joined")
        return 0
    print(f"FAIL  {len(bad)} joints are not made")
    return 1


if __name__ == "__main__":
    sys.exit(main())
