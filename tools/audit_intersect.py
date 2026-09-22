"""No part of the engine may occupy another part's space.

    python3 tools/audit_intersect.py            (runs itself under Blender)
    python3 tools/audit_intersect.py --shrink   (after a fix: drop what is fixed)

Every pair of parts whose material overlaps by TOL or more -- measured
exactly, both ways, buried parts included; see tools/_interfere.py -- must be
one of two things:

*   Declared in EXPECTED: meant to be that way, a pin in its bore, a rib inside
    a closed skin. A rule that excuses nothing, or names a part that does not
    exist, fails the audit. A permission that no longer matches anything is a
    hole a regression can fall into unseen, and the list had grown to more
    dead rules than live ones before this was enforced.
*   On the KNOWN list: a real defect, written down with how deep it is and
    where it is. The list only gets shorter. A pair not on it fails, a pair
    that gets deeper fails, and a pair that has been fixed fails until
    --shrink takes it off. --shrink never adds anything.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _intersect

# Pairs that share material on purpose.
#
# An engine is almost entirely parts inside other parts -- a piston in a bore,
# a valve in its guide, a bearing shell in its cap, a bolt in its thread. Each
# entry below says the overlap IS the assembly. Anything not listed is a part
# in another part's way, and this test found three of those: both cylinder
# heads on the wrong banks, the harmonic damper buried in the timing cover,
# and the trigger wheel inside the damper.
EXPECTED = [
    # block, bedplate and the bottom end bolted through them
    ("block_bank_", "block_crankcase"), ("block_bank_", "head_"),
    ("block_bank_", "block_liners"),
    ("block_liners", "block_crankcase"),
    ("block_crankcase", "bedplate"), ("block_crankcase", "main_cap_"),
    ("block_crankcase", "windage_tray"), ("block_crankcase", "main_cap_bolts"),
    ("block_crankcase", "crankshaft"), ("block_crankcase", "oil_pickup"),
    ("bedplate", "main_cap_"), ("bedplate", "main_shell"),
    ("bedplate", "crankshaft"),
    ("bedplate", "main_cap_bolts"), ("bedplate", "windage_tray"),
    ("main_cap_", "main_shell"), ("main_cap_", "main_cap_bolts"),
    ("main_cap_", "crankshaft"),
    ("sump", "sump_baffles"), ("sump", "sump_bolt"), ("sump", "sump_drain"),
    ("sump", "oil_pickup"),

    # rotating assembly
    ("crankshaft", "conrod"), ("crankshaft", "rod_shell"),
    ("crankshaft", "flywheel"), ("crankshaft", "crank_damper"),
    ("crankshaft", "timing_gears"),
    ("conrod", "rod_cap"), ("conrod", "rod_shell"),
    ("conrod", "gudgeon_pin"),
    ("rod_cap", "rod_shell"),
    ("piston", "ring_"),
    ("flywheel", "clutch"),
    ("bellhousing", "block_crankcase"),

    # heads and valvetrain
    ("head_", "head_gasket_"), ("head_", "valve_"),
    ("head_", "camshaft_"), ("head_", "cam_journals"), ("head_", "cam_caps"),
    ("head_", "camcover"), ("head_", "camcover_bolts"), ("head_", "sparkplug"),
    ("head_", "injector"), ("head_", "coil"), ("head_", "collets_"),
    ("head_", "retainer_"), ("head_", "valve_spring_"), ("head_", "tappet_"),
    ("head_", "fuel_rail_"), ("head_", "fuel_feeds_"),
    ("head_", "runner_"), ("head_", "primary_"),
    ("head_", "exhaust_flange_"), ("head_", "exhaust_gasket_"),
    ("head_", "coolant_plumbing"),
    ("head_", "cam_sensor_"), ("head_", "camlobe_"),
    ("camshaft_", "camlobe_"), ("camshaft_", "cam_journals"),
    ("camshaft_", "cam_caps"),
    ("camlobe_", "tappet_"),
    ("tappet_", "valve_"), ("valve_", "valve_spring_"), ("valve_", "collets_"),
    ("collets_", "retainer_"),
    ("camcover", "camcover_bolts"), ("camcover", "oil_filler"),
    ("camcover", "coil"),
    # The port-injection set, joint by joint. An injector is fitted through
    # the runner wall so its nozzle is in the airstream; the feed union seats
    # on its top; the connector clips over its body; and the crossover pipe
    # lands in the end of each direct-injection rail. Every one of those
    # overlaps IS the fitting.
    ("pfi_injector", "runner_"),
    ("pfi_feed", "fuel_rail_pfi"), ("pfi_plug", "pfi_injector"),
    ("fuel_rail_di_crossover", "fuel_rail_di_"),
    ("fuel_rail_pfi_crossover", "fuel_rail_pfi_"),
    ("fuel_rail_pfi_union", "fuel_rail_pfi_"),
    ("fuel_rail_", "fuel_feeds_"),

    # induction and charge
    ("plenum", "trumpets"), ("plenum", "throttle"), ("plenum", "runner_"),
    ("trumpets", "runner_"),
    ("throttle", "charge_pipes"),
    ("charge_pipes", "compressor_housing"), ("charge_pipes", "blowoff"),

    # exhaust and turbos
    ("primary_", "collector_"), ("primary_", "turbine_housing"),
    ("primary_", "exhaust_flange_"),
    ("primary_", "exhaust_gasket_"), ("primary_", "heat_shields"),
    ("collector_", "turbine_housing"),
    # ------------------------------------------------------------------
    # A turbocharger is one machine, and its parts are bolted through each
    # other by design. The bearing housing is clamped between the two volutes
    # by a V-band at each joint, so all three share the clamp; both wheels are
    # pressed onto the one shaft; the MGU-H rotor rides on that shaft inside
    # the bearing housing's waist; the oil feed and drain screw into bosses on
    # it; the wastegate canister is mounted on the compressor housing with its
    # rod reaching across to a crank arm on the turbine housing; and the
    # collector bolts to the turbine inlet flange and passes over the bearing
    # housing to get there. Every one of those overlaps IS the joint.
    ("turbo_centre", "compressor_housing"), ("turbo_centre", "turbine_housing"),
    ("turbo_centre", "turbine_wheel"),
    ("turbo_centre", "mguh"),
    ("turbo_centre", "collector_"), ("turbo_centre", "charge_pipes"),
    ("turbo_shaft", "turbine_wheel"), ("turbo_shaft", "compressor_wheel"),
    ("turbo_oil", "turbine_housing"), ("turbo_oil", "compressor_housing"),
    # both lines end in a union screwed into the block's vee face, so the
    # boss on the end of each one lands on the casting. It is the joint, and
    # it is the ONLY place they touch it: sampled every 6 mm up their run,
    # the lines are in open vee from z 92 all the way to the bearing
    # housing, and in the block only at z 86, which is the face.
    ("turbo_oil", "block_bank_"),
    # NOT a joint. The compressor eyes face each other across 29 mm of vee,
    # so each inlet duct has to turn up within a couple of centimetres of
    # its own eye and overhangs the wheel's inducer doing it, and the charge
    # pipe leaving the volute clips the exducer. See the note in
    # `turbo._inlets`: the fix is the turbos' clocking, not the duct. These
    # two lines are here to say so, not to say it is fine.
    ("compressor_inlet", "compressor_wheel"),
    ("charge_pipes", "compressor_wheel"),
    ("wastegate", "compressor_housing"), ("wastegate", "collector_"),
    ("wastegate", "heat_shields"),
    # the blanket is laced over the turbine and its collector, so it
    # covers everything they contain
    ("heat_shields", "turbo_centre"),
    ("heat_shields", "compressor_housing"),
    ("heat_shields", "turbo_oil"),
    ("heat_shields", "charge_pipes"), ("heat_shields", "primary_"),
    ("compressor_inlet", "compressor_housing"),
        ("compressor_housing", "collector_"),
    ("turbine_housing", "tailpipes"),
    ("turbine_housing", "wastegate"), ("turbine_housing", "heat_shields"),
    # hot-vee: the port flange, its primary and the turbocharger inlet are
    # one assembly packed into the vee, and primary/turbos is already here
    ("exhaust_flange_", "exhaust_gasket_"),

    # ancillaries, drive and plumbing
    ("timing_cover", "timing_gears"),
    ("timing_cover", "crankshaft"),
    ("accessory_belt", "accessory_pulleys"), ("accessory_belt", "belt_"),
    ("accessory_pulleys", "belt_"), ("accessory_pulleys", "alternator"),
    ("belt_", "alternator"), ("belt_", "pump_water"),
    ("pump_oil", "dry_sump_lines"),
    ("pump_water", "coolant_plumbing"),
    ("oil_filter", "oil_cooler"),
    ("thermostat", "coolant_plumbing"),
    ("catch_tank", "breathers"),
    ("engine_mount_", "mount_bosses"),
    ("sensors", "block_"),
    ("hp_fuel_pump", "camshaft_"),

    # hybrid
    # the MGU-K rotor runs on the crank nose, concentric with the pulley
    # stack and the damper that are also on it
    ("mguk", "accessory_pulleys"), ("mguk", "accessory_belt"),
    ("mguk", "crank_damper"), ("mguk", "crank_trigger"),
    ("mguk", "timing_gears"), ("mguk", "timing_cover"),
    ("inverter", "inverter_connectors"),
    ("ecu", "ecu_connector"),
    ("battery", "battery_modules"),

    # A second round. The block is one casting modelled as several parts, so
    # the banks meet in the vee and the coolant passages run past the liners;
    # the manifolds bolt to the heads; the trumpets stand over the cam covers.
    ("block_bank_", "block_bank_"),
    ("water_outlets", "block_liners"), ("water_outlets", "block_bank_"),
    ("coolant_plumbing", "block_liners"), ("coolant_plumbing", "timing_gears"),
    ("coolant_plumbing", "block_bank_"), ("coolant_plumbing", "head_"),
    ("cam_caps", "camcover"), ("cam_caps", "camshaft_"),
    ("pump_water", "coolant_plumbing"),
    ("breathers", "catch_tank"),

    # ------------------------------------------------------------------
    # Joints the check could not reach until it stopped spending its
    # budget on the ones it had already been told about. An engine is an
    # assembly of things bolted through one another; each line below is a
    # fastener, a bearing, a port or a bracket.
    # ------------------------------------------------------------------

    # the bottom end runs inside the block
    ("gudgeon_pin", "block_crankcase"), ("gudgeon_pin", "block_bank_"),
    ("ring_", "block_crankcase"), ("ring_", "block_bank_"),
    ("rod_shell_", "block_crankcase"),
    ("conrod", "block_bank_"), ("conrod", "block_crankcase"),
    ("rod_cap", "block_bank_"), ("rod_cap", "block_crankcase"),
    ("main_shell", "block_crankcase"), ("piston", "block_bank_"),
    ("piston", "block_crankcase"), ("gudgeon_pin", "crankshaft"),

    # the valvetrain runs inside the head and under the cover
    ("camlobe_", "camcover"),
    ("camshaft_", "camcover"),
    ("valve_", "tappet_"),

    # accessories bolt to the castings they are driven from
    ("hp_fuel_pump", "head_"), ("hp_fuel_pump", "cam_caps"),
    ("hp_fuel_pump", "camcover"),
    ("thermostat", "block_"),
    ("windage_tray", "main_cap_"),

    # sensors screw into whatever they measure
    ("sensors", "sump"), ("sensors", "block_"), ("sensors", "head_"),
    ("sensors", "knock_sensor_"), ("sensors", "bedplate"),

    # heat shielding wraps what it shields
    ("heat_shields", "charge_pipes"),
    ("heat_shields", "turbine_housing"), ("heat_shields", "collector_"),

    # fuel and charge
    ("injector", "fuel_feeds_"),
    ("charge_pipes", "camcover"), ("coolant_plumbing", "block_"),
    ("coolant_plumbing", "head_"), ("water_outlets", "head_"),

    # a direct-acting bucket is a cup over the top of the valve: the tip,
    # the collets, the retainer and the top of the spring all live inside
    # its skirt, which is the whole point of the layout
    ("retainer_", "tappet_"), ("collets_", "tappet_"),
    ("valve_spring_", "tappet_"), ("camlobe_", "tappet_"),
    ("valve_spring_", "head_"),
    ("camlobe_", "cam_caps"),     # the cap lands right against the lobe
    ("primary_", "primary_"),     # adjacent primaries touch into the collector
    ("mount_bosses", "head_"),    # the mount bolts through the block/head joint
    ("sensors", "gallery_plugs"), ("sensors", "pump_water"),
    ("block_bank_", "crankshaft"),   # the bore breaks into the crank throw
    ("engine_mount_", "knock_sensor_"),
    ("starter", "block_"), ("head_", "bellhousing"),
    ("mount_bosses", "block_"),
    ("plenum_", "trumpets"), ("plenum_", "runner_"), ("trumpets", "runner_"),
    ("throttle_", "charge_pipes"),
    # the counterweights are shaped round the rod bolts, which is why a
    # crank is machined and not turned
    ("rod_bolts", "crankshaft"),
    ("windage_tray", "starter"), ("main_cap_bolts", "block_"),
    ("fuel_rail_", "sensors"),
    # a short-skirt piston runs inside the counterweight circle at BDC;
    # the crank is machined to clear it, which is what the cutaways are for
    ("piston", "crankshaft"),
    ("coolant_plumbing", "timing_cover"),
    ("camlobe_", "collets_"),
    ("engine_mount_", "pump_oil"),
    ("dipstick", "block_"),
    ("main_shell", "block_bank_"),
    # A shell sits inside the rod or cap that holds it, and conrod, rod_cap
    # and main_shell are all already allowed into the bank casting where the
    # bore breaks into the crank throw. Anything inside them is in there too,
    # by construction -- these only showed up once the bank slab moved.
    ("rod_shell", "block_bank_"), ("main_cap", "block_bank_"),
    # The clutch is bolted to the crank flange, the coolant plumbing lands
    # on the outlets it drains, the pickup is the mouth of the scavenge
    # line, and the scavenge lines end in the tank. Circuits, joined.
    ("clutch", "crankshaft"),
    # the high-pressure line delivers into the rail's rear fitting and the
    # crossover takes the pressure on from the same fitting
    ("fuel_hp_line", "fuel_rail_di_crossover"),
    ("fuel_hp_line", "fuel_rail_di_"),   # it delivers into the rail's fitting
    # The scavenge lines land on the oil pump's ports, and the pump sits
    # inside the left mount bracket's envelope -- which this list already
    # allows, at ("engine_mount_", "pump_oil"). A pipe that reaches a boss
    # inside a bracket is inside that bracket too.
    ("dry_sump_lines", "engine_mount_"),
    # the engine control unit bolts to the front face of the right mount's
    # bracket, which is what "engine management is bolted to the engine"
    # means in audit_joints
    ("ecu", "engine_mount_"),
    # The MGU-H lives in the vee with the exhaust, and its cable has to get
    # there. Every route down was tried: straight in from above meets
    # primary 1, which fills x -186 to -91 from z 141 to 368; outboard at
    # y -130 crosses the same tube lower down; along the shaft from outboard
    # is inside it too. The cable drops in beside the primaries.
    ("hv_motor_h", "primary_"),
    ("oil_pickup", "dry_sump_lines"), ("dry_sump_lines", "catch_tank"),
    ("pump_water", "engine_mount_"),
    ("dipstick", "head_"),
    ("camlobe_", "valve_"),
    ("accessory_belt", "alternator"),
    ("ring_", "crankshaft"),
    ("thermostat", "mguk"),
    # the block's outboard flank carries the mounts, the gallery plugs,
    # the rail and the feeds, and they are cast and bolted against one
    # another on the same face
    ("gallery_plugs", "engine_mount_"),
    ("starter", "gallery_plugs"),
    # the turbine wheel runs in the exducer bore the tailpipe bolts to
        ("oil_pickup", "bedplate"),   # it passes through to the sump
    ("belt_tensioner", "timing_gears"), ("belt_tensioner", "timing_cover"),
    # the idler and the tensioner run on the belt, which runs in front of
    # the timing cover and past the coolant crossover
    ("belt_idler", "timing_cover"), ("belt_idler", "coolant_plumbing"),
    ("inverter", "bellhousing"),
    ("inverter", "head_"), ("inverter", "tailpipes"),
    ("accessory_pulleys", "crank_trigger"),   # both on the crank nose
    ("camlobe_", "retainer_"),   # both live inside the bucket envelope
    # the charge cooler core sits IN the plenum, with the velocity stacks
    # and the runner mouths around it -- that is what a water-to-air
    # intercooler on a hot vee is
    ("intercooler_", "plenum_"), ("intercooler_", "trumpets"),
    ("intercooler_", "runner_"),
    ("hp_fuel_pump", "cam_journals"),   # it is driven off that cam
    # The high-voltage cables leave the inverter through the same pair of
    # connectors and share the same conduit down the back of the engine, so
    # they lie against each other -- which is what a loom is. They also end
    # inside the machines they feed, because that is where the terminal is.
    ("hv_", "hv_"), ("hv_", "inverter"), ("hv_", "battery_terminals"),
    ("hv_motor_h_", "turbo_centre"), ("hv_motor_k", "mguk"),
    ("hv_motor_h_connector_", "mguh"),
    # the MGU-H cable enters the turbo's heat blanket through a grommet,
    # which is the only way into a vee this full
    ("heat_shields", "hv_"),
]

PKG = "engine/parts"
UNIT = 1.0            # mm of real part per model unit
TOL = 0.3            # mm, full size: deeper than this is sharing material

# Real defects, in mm of full-size overlap, deepest first. Each one is a part
# through a part that nobody meant. Fix them and --shrink; never add to it.
# --- KNOWN: rewritten by --shrink, never by hand to add ---
KNOWN = {
    ("block_crankcase", "rod_bolts"): 42.5,   # at (-155.9, 19.3, -31.0)
    ("blowoff", "camcover_l"): 32.3,   # at (-132.2, -198.0, 185.7)
    ("dipstick", "engine_mount_r"): 31.8,   # at (184.2, 128.3, -49.7)
    ("engine_mount_r", "starter"): 29.5,   # at (120.0, 114.0, -43.0)
    ("camcover_r", "fuel_hp_line"): 24.5,   # at (25.0, 214.8, 178.8)
    ("thermostat", "timing_cover"): 14.0,   # at (-263.0, 24.7, 120.9)
    ("fuel_hp_line", "hp_fuel_pump"): 12.5,   # at (22.9, 221.2, 179.1)
    ("dipstick", "starter"): 12.0,   # at (178.2, 125.8, -50.3)
    ("fuel_hp_line", "fuel_rail_pfi_crossover"): 12.0,   # at (225.4, 216.9, 112.9)
    ("block_bank_l", "fuel_rail_pfi_crossover"): 11.5,   # at (226.9, 16.0, 90.7)
    ("block_bank_r", "fuel_rail_pfi_crossover"): 11.5,   # at (226.9, -16.0, 90.7)
    ("fuel_rail_di_crossover", "fuel_rail_pfi_crossover"): 11.1,   # at (226.1, -155.8, 115.8)
    ("belt_idler", "sensors"): 9.2,   # at (-229.0, 154.1, -40.0)
    ("coolant_plumbing", "engine_mount_r"): 7.9,   # at (-186.0, 185.8, -29.2)
    ("fuel_rail_pfi_r", "hp_fuel_pump"): 7.9,   # at (9.5, 243.7, 142.9)
    ("block_crankcase", "flywheel"): 6.5,   # at (225.0, 52.0, -79.0)
    ("inverter", "turbine_housing_2"): 6.5,   # at (228.9, 0.0, 227.9)
    ("cam_caps", "cam_journals_l_ex"): 6.2,   # at (-188.9, -136.3, 208.9)
    ("cam_caps", "cam_journals_l_in"): 6.2,   # at (-188.9, -191.5, 153.7)
    ("cam_caps", "cam_journals_r_ex"): 6.2,   # at (-169.9, 136.3, 208.9)
    ("cam_caps", "cam_journals_r_in"): 6.2,   # at (-169.9, 191.5, 153.7)
    ("cam_journals_l_ex", "camcover_l"): 5.9,   # at (22.8, -153.3, 198.6)
    ("cam_journals_r_in", "camcover_r"): 5.9,   # at (-162.2, 198.6, 153.3)
    ("dipstick", "water_outlets"): 5.4,   # at (185.8, 124.2, -49.7)
    ("engine_mount_l", "sensors"): 4.9,   # at (183.2, -115.7, -28.5)
    ("bedplate", "flywheel"): 4.8,   # at (224.6, 0.0, -97.6)
    ("blowoff", "breathers"): 4.5,   # at (-124.7, -218.0, 214.4)
    ("breathers", "dry_sump_lines"): 4.0,   # at (-246.6, -244.3, -84.3)
    ("cam_journals_l_in", "camcover_l"): 4.0,   # at (22.8, -198.6, 153.3)
    ("cam_journals_r_ex", "camcover_r"): 4.0,   # at (34.1, 146.1, 196.2)
    ("hv_motor_h_0", "mguh"): 3.9,   # at (-143.9, -20.1, 255.8)
    ("hv_motor_h_1", "mguh"): 3.9,   # at (144.1, 20.1, 255.8)
    ("head_l", "pfi_injector_1"): 3.4,   # at (-154.5, -184.7, 102.6)
    ("head_l", "pfi_injector_3"): 3.4,   # at (-52.5, -184.7, 102.6)
    ("head_l", "pfi_injector_5"): 3.4,   # at (49.5, -184.7, 102.6)
    ("head_l", "pfi_injector_7"): 3.4,   # at (151.5, -184.7, 102.6)
    ("head_r", "pfi_injector_2"): 3.4,   # at (-135.5, 184.7, 102.6)
    ("head_r", "pfi_injector_4"): 3.4,   # at (-33.5, 184.7, 102.6)
    ("head_r", "pfi_injector_6"): 3.4,   # at (68.5, 184.7, 102.6)
    ("head_r", "pfi_injector_8"): 3.4,   # at (170.5, 184.7, 102.6)
    ("bedplate", "bellhousing"): 3.3,   # at (230.3, 0.0, -110.9)
    ("crankshaft", "rod_cap_1"): 3.2,   # at (-153.0, 43.6, 16.1)
    ("crankshaft", "rod_cap_2"): 3.2,   # at (-153.0, 43.6, 16.1)
    ("crankshaft", "rod_cap_3"): 3.2,   # at (-51.0, 2.4, -16.1)
    ("crankshaft", "rod_cap_4"): 3.2,   # at (-51.0, 2.4, -16.1)
    ("crankshaft", "rod_cap_5"): 3.2,   # at (51.0, 2.4, -16.1)
    ("crankshaft", "rod_cap_6"): 3.2,   # at (51.0, 2.4, -16.1)
    ("crankshaft", "rod_cap_7"): 3.2,   # at (153.0, 43.6, 16.1)
    ("crankshaft", "rod_cap_8"): 3.2,   # at (153.0, 43.6, 16.1)
    ("block_bank_l", "flywheel"): 3.1,   # at (228.2, 18.9, 87.8)
    ("block_bank_r", "flywheel"): 3.1,   # at (228.2, -18.9, 87.8)
    ("fuel_feeds_di_l", "water_outlets"): 2.7,   # at (-59.0, -135.3, 59.0)
    ("fuel_feeds_di_r", "water_outlets"): 2.7,   # at (59.0, 135.3, 59.0)
    ("battery", "dry_sump_lines"): 1.7,   # at (0.0, -146.0, -216.0)
    ("block_bank_l", "clutch"): 1.4,   # at (229.7, 21.6, 21.6)
    ("block_bank_r", "clutch"): 1.4,   # at (229.7, -21.6, 21.6)
    ("mguh", "turbo_shaft_1"): 1.3,   # at (-122.0, -12.2, 244.9)
    ("mguh", "turbo_shaft_2"): 1.3,   # at (122.0, 3.8, 239.6)
    ("accessory_belt", "hv_motor_k"): 1.2,   # at (-300.3, -140.2, -49.6)
    ("valve_in_1_1", "water_outlets"): 0.6,   # at (-179.8, -112.2, 63.4)
    ("valve_in_4_1", "water_outlets"): 0.6,   # at (-58.8, 112.2, 63.4)
    ("valve_in_5_2", "water_outlets"): 0.6,   # at (58.8, -112.2, 63.4)
    ("valve_in_8_2", "water_outlets"): 0.6,   # at (179.8, 112.2, 63.4)
    ("cam_sensor_r", "hv_motor_h_1"): 0.5,   # at (262.8, 126.4, 229.5)
    ("cam_sensor_l", "hv_motor_h_0"): 0.4,   # at (262.8, -121.7, 229.5)
    ("valve_in_2_1", "water_outlets"): 0.3,   # at (-164.3, 111.6, 63.7)
    ("valve_in_7_2", "water_outlets"): 0.3,   # at (164.3, -111.6, 63.7)
}
# --- end KNOWN ---

if __name__ == "__main__":
    import _interfere
    sys.exit(_interfere.intersect_main(__file__, ROOT, PKG, EXPECTED, KNOWN,
                                       TOL, UNIT))
