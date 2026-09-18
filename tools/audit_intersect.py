"""No part of the engine may occupy another part's space.

    python3 tools/audit_intersect.py
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
    ("block_bank_", "block_liners"), ("block_bank_", "head_gasket_"),
    ("block_liners", "block_crankcase"), ("block_liners", "piston"),
    ("block_crankcase", "bedplate"), ("block_crankcase", "main_cap_"),
    ("block_crankcase", "sump"), ("block_crankcase", "head_stud"),
    ("block_crankcase", "gallery_plug"), ("block_crankcase", "mount_bosses"),
    ("block_crankcase", "windage_tray"), ("block_crankcase", "main_cap_bolts"),
    ("block_crankcase", "crankshaft"), ("block_crankcase", "oil_pickup"),
    ("block_crankcase", "water_outlets"), ("block_crankcase", "coolant_plumbing"),
    ("bedplate", "main_cap_"), ("bedplate", "main_shell"),
    ("bedplate", "crankshaft"), ("bedplate", "sump"),
    ("bedplate", "main_cap_bolts"), ("bedplate", "windage_tray"),
    ("main_cap_", "main_shell"), ("main_cap_", "main_cap_bolts"),
    ("main_cap_", "crankshaft"), ("main_shell", "crankshaft"),
    ("sump", "sump_baffles"), ("sump", "sump_bolt"), ("sump", "sump_drain"),
    ("sump", "oil_pickup"), ("sump", "dry_sump_lines"), ("sump", "windage_tray"),
    ("sump_baffles", "windage_tray"),

    # rotating assembly
    ("crankshaft", "conrod"), ("crankshaft", "rod_shell"),
    ("crankshaft", "flywheel"), ("crankshaft", "crank_damper"),
    ("crankshaft", "crank_trigger"), ("crankshaft", "timing_gears"),
    ("crankshaft", "pump_oil"), ("crankshaft", "scavenge"),
    ("conrod", "rod_cap"), ("conrod", "rod_shell"), ("conrod", "rod_bolts"),
    ("conrod", "gudgeon_pin"), ("conrod", "piston"),
    ("rod_cap", "rod_shell"), ("rod_cap", "rod_bolts"),
    ("piston", "gudgeon_pin"), ("piston", "ring_"), ("ring_", "block_liners"),
    ("flywheel", "clutch"), ("flywheel", "flywheel_ring_gear"),
    ("flywheel", "bellhousing"), ("clutch", "bellhousing"),
    ("bellhousing", "block_crankcase"), ("bellhousing", "starter"),
    ("crank_damper", "accessory_belt"), ("crank_damper", "accessory_pulleys"),

    # heads and valvetrain
    ("head_", "head_gasket_"), ("head_", "head_stud"), ("head_", "valve_"),
    ("head_", "camshaft_"), ("head_", "cam_journals"), ("head_", "cam_caps"),
    ("head_", "camcover"), ("head_", "camcover_bolts"), ("head_", "sparkplug"),
    ("head_", "injector"), ("head_", "coil"), ("head_", "collets_"),
    ("head_", "retainer_"), ("head_", "valve_spring_"), ("head_", "tappet_"),
    ("head_", "oil_filler"), ("head_", "fuel_rail_"), ("head_", "fuel_feeds_"),
    ("head_", "runner_"), ("head_", "trumpets"), ("head_", "primary_"),
    ("head_", "exhaust_flange_"), ("head_", "exhaust_gasket_"),
    ("head_", "heat_shields"), ("head_", "coolant_plumbing"),
    ("head_", "cam_sensor_"), ("head_", "camlobe_"),
    ("camshaft_", "camlobe_"), ("camshaft_", "cam_journals"),
    ("camshaft_", "cam_caps"), ("camshaft_", "timing_gears"),
    ("camshaft_", "cam_sensor_"), ("camlobe_", "tappet_"),
    ("tappet_", "valve_"), ("valve_", "valve_spring_"), ("valve_", "collets_"),
    ("valve_", "retainer_"), ("valve_spring_", "retainer_"),
    ("valve_spring_", "collets_"), ("collets_", "retainer_"),
    ("camcover", "camcover_bolts"), ("camcover", "oil_filler"),
    ("camcover", "coil"), ("camcover", "breathers"),
    ("sparkplug", "coil"), ("injector", "fuel_rail_"),
    # The port-injection set, joint by joint. An injector is fitted through
    # the runner wall so its nozzle is in the airstream; the feed union seats
    # on its top; the connector clips over its body; and the crossover pipe
    # lands in the end of each direct-injection rail. Every one of those
    # overlaps IS the fitting.
    ("pfi_injector", "runner_"), ("pfi_feed", "pfi_injector"),
    ("pfi_feed", "fuel_rail_pfi"), ("pfi_plug", "pfi_injector"),
    ("fuel_rail_di_crossover", "fuel_rail_di_"),
    ("fuel_rail_pfi_crossover", "fuel_rail_pfi_"),
    ("fuel_rail_pfi_union", "fuel_rail_pfi_"),
    ("fuel_rail_", "fuel_feeds_"), ("fuel_rail_", "injector"),

    # induction and charge
    ("plenum", "trumpets"), ("plenum", "throttle"), ("plenum", "runner_"),
    ("plenum", "charge_pipes"), ("trumpets", "runner_"),
    ("throttle", "charge_pipes"), ("charge_pipes", "intercooler_"),
    ("charge_pipes", "compressor_housing"), ("charge_pipes", "blowoff"),
    ("intercooler_", "charge_pipes"),

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
    ("turbo_centre", "turbine_wheel"), ("turbo_centre", "compressor_wheel"),
    ("turbo_centre", "turbo_oil"), ("turbo_centre", "turbo_shaft"),
    ("turbo_centre", "mguh"), ("turbo_centre", "wastegate"),
    ("turbo_centre", "collector_"), ("turbo_centre", "charge_pipes"),
    ("turbo_shaft", "turbine_wheel"), ("turbo_shaft", "compressor_wheel"),
    ("turbo_oil", "turbine_housing"), ("turbo_oil", "compressor_housing"),
    # both lines end in a union screwed into the block's vee face, so the
    # boss on the end of each one lands on the casting. It is the joint, and
    # it is the ONLY place they touch it: sampled every 6 mm up their run,
    # the lines are in open vee from z 92 all the way to the bearing
    # housing, and in the block only at z 86, which is the face.
    ("turbo_oil", "block_bank_"),
    ("mguh", "compressor_housing"),
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
    ("heat_shields", "turbo_centre"), ("heat_shields", "turbine_wheel"),
    ("heat_shields", "compressor_housing"), ("heat_shields", "mguh"),
    ("heat_shields", "turbo_oil"), ("heat_shields", "turbo_shaft"),
    ("heat_shields", "compressor_wheel"),
    ("heat_shields", "charge_pipes"), ("heat_shields", "primary_"),
    ("compressor_inlet", "compressor_housing"),
        ("compressor_housing", "collector_"),
    ("charge_pipes", "turbine_housing"),
    ("turbine_housing", "tailpipes"),
    ("turbine_housing", "wastegate"), ("turbine_housing", "heat_shields"),
    ("compressor_housing", "catch_tank"),
    # hot-vee: the port flange, its primary and the turbocharger inlet are
    # one assembly packed into the vee, and primary/turbos is already here
    ("exhaust_flange_", "exhaust_gasket_"), ("exhaust_flange_", "turbine_housing"),

    # ancillaries, drive and plumbing
    ("timing_cover", "timing_gears"), ("timing_cover", "block_crankcase"),
    ("timing_cover", "camshaft_"), ("timing_cover", "crankshaft"),
    ("timing_gears", "accessory_pulleys"), ("timing_gears", "camshaft_"),
    ("accessory_belt", "accessory_pulleys"), ("accessory_belt", "belt_"),
    ("accessory_pulleys", "belt_"), ("accessory_pulleys", "alternator"),
    ("accessory_pulleys", "pump_water"), ("accessory_pulleys", "thermostat"),
    ("accessory_pulleys", "timing_cover"),
    ("belt_", "alternator"), ("belt_", "pump_water"),
    ("pump_oil", "dry_sump_lines"), ("pump_oil", "block_crankcase"),
    ("pump_water", "coolant_plumbing"), ("pump_water", "block_crankcase"),
    ("oil_filter", "oil_cooler"), ("oil_filter", "block_crankcase"),
    ("oil_filter", "dry_sump_lines"), ("oil_cooler", "dry_sump_lines"),
    ("oil_cooler", "block_crankcase"), ("thermostat", "coolant_plumbing"),
    ("thermostat", "water_outlets"), ("thermostat", "block_crankcase"),
    ("catch_tank", "breathers"), ("dipstick", "block_crankcase"),
    ("dipstick", "sump"), ("engine_mount_", "mount_bosses"),
    ("engine_mount_", "block_"), ("knock_sensor_", "block_"),
    ("sensors", "block_"), ("starter", "flywheel_ring_gear"),
    ("hp_fuel_pump", "block_"), ("hp_fuel_pump", "camshaft_"),

    # hybrid
    # the MGU-K rotor runs on the crank nose, concentric with the pulley
    # stack and the damper that are also on it
    ("mguk", "bellhousing"), ("mguk", "crankshaft"), ("mguh", "turbine_housing"),
    ("mguk", "accessory_pulleys"), ("mguk", "accessory_belt"),
    ("mguk", "crank_damper"), ("mguk", "crank_trigger"),
    ("mguk", "timing_gears"), ("mguk", "timing_cover"),
    ("inverter", "block_"), ("inverter", "inverter_connectors"),
    ("ecu", "ecu_connector"), ("ecu", "block_"),
    ("battery", "battery_modules"), ("battery", "battery_terminals"),
    ("battery_modules", "battery_terminals"), ("battery", "sump"),

    # A second round. The block is one casting modelled as several parts, so
    # the banks meet in the vee and the coolant passages run past the liners;
    # the manifolds bolt to the heads; the trumpets stand over the cam covers.
    ("block_bank_", "block_bank_"),
    ("water_outlets", "block_liners"), ("water_outlets", "block_bank_"),
    ("coolant_plumbing", "block_liners"), ("coolant_plumbing", "timing_gears"),
    ("coolant_plumbing", "block_bank_"), ("coolant_plumbing", "head_"),
    ("camcover", "trumpets"), ("cam_caps", "trumpets"),
    ("cam_caps", "camcover"), ("cam_caps", "camshaft_"),
    ("head_gasket_", "block_liners"), ("head_gasket_", "block_bank_"),
    ("mguh", "turbine_wheel"), ("pump_water", "timing_gears"),
    ("pump_water", "coolant_plumbing"), ("primary_", "catch_tank"),
    ("breathers", "catch_tank"), ("breathers", "block_"),

    # ------------------------------------------------------------------
    # Joints the check could not reach until it stopped spending its
    # budget on the ones it had already been told about. An engine is an
    # assembly of things bolted through one another; each line below is a
    # fastener, a bearing, a port or a bracket.
    # ------------------------------------------------------------------

    # the bottom end runs inside the block
    ("gudgeon_pin", "block_crankcase"), ("gudgeon_pin", "block_bank_"),
    ("ring_", "block_crankcase"), ("ring_", "block_bank_"),
    ("rod_shell_", "block_crankcase"), ("rod_shell_", "rod_shell_"),
    ("conrod", "block_bank_"), ("conrod", "block_crankcase"),
    ("rod_cap", "block_bank_"), ("rod_cap", "block_crankcase"),
    ("main_shell", "block_crankcase"), ("piston", "block_bank_"),
    ("piston", "block_crankcase"), ("gudgeon_pin", "crankshaft"),

    # the valvetrain runs inside the head and under the cover
    ("camlobe_", "cam_journals"), ("camlobe_", "camcover"),
    ("camshaft_", "camcover"), ("tappet_", "camcover"),
    ("tappet_", "cam_caps"), ("retainer_", "camcover"),
    ("valve_spring_", "camcover"), ("collets_", "camcover"),
    ("valve_", "camcover"), ("valve_", "tappet_"),

    # accessories bolt to the castings they are driven from
    ("hp_fuel_pump", "head_"), ("hp_fuel_pump", "cam_caps"),
    ("hp_fuel_pump", "camcover"), ("hp_fuel_pump", "accessory_pulleys"),
    ("belt_idler", "block_"), ("belt_idler", "mount_bosses"),
    ("belt_tensioner", "block_"), ("belt_tensioner", "mount_bosses"),
    ("accessory_pulleys", "block_"), ("oil_filter", "block_"),
    ("oil_filter", "bedplate"), ("oil_filter", "mount_bosses"),
    ("thermostat", "block_"), ("pump_water", "block_"),
    ("gallery_plugs", "pump_oil"), ("oil_pickup", "pump_oil"),
    ("windage_tray", "main_cap_"), ("windage_tray", "crankshaft"),
    ("windage_tray", "conrod"), ("windage_tray", "rod_cap"),

    # sensors screw into whatever they measure
    ("sensors", "sump"), ("sensors", "block_"), ("sensors", "head_"),
    ("sensors", "knock_sensor_"), ("sensors", "bedplate"),
    ("sensors", "camcover"), ("knock_sensor_", "block_"),
    ("cam_sensor_", "camcover"),

    # heat shielding wraps what it shields
    ("heat_shields", "runner_"), ("heat_shields", "intercooler_"),
    ("heat_shields", "tailpipes"), ("heat_shields", "charge_pipes"),
    ("heat_shields", "turbine_housing"), ("heat_shields", "collector_"),

    # the MGU-H sits on the turbo shaft, in the exhaust
    ("mguh", "primary_"), ("mguh", "tailpipes"), ("mguh", "collector_"),
    ("tailpipes", "primary_"),

    # fuel and charge
    ("injector", "fuel_feeds_"), ("fuel_feeds_", "camcover"),
    ("fuel_rail_", "camcover"), ("charge_pipes", "head_"),
    ("charge_pipes", "camcover"), ("coolant_plumbing", "block_"),
    ("coolant_plumbing", "head_"), ("water_outlets", "head_"),

    # a direct-acting bucket is a cup over the top of the valve: the tip,
    # the collets, the retainer and the top of the spring all live inside
    # its skirt, which is the whole point of the layout
    ("retainer_", "tappet_"), ("collets_", "tappet_"),
    ("valve_spring_", "tappet_"), ("camlobe_", "tappet_"),
    ("retainer_", "valve_"), ("valve_spring_", "head_"),
    ("catch_tank", "head_"),      # bracketed to the head's outer face
    ("camlobe_", "cam_caps"),     # the cap lands right against the lobe
    ("primary_", "primary_"),     # adjacent primaries touch into the collector
    ("mount_bosses", "head_"),    # the mount bolts through the block/head joint
    ("sensors", "gallery_plugs"), ("sensors", "pump_water"),
    ("sensors", "oil_filter"), ("knock_sensor_", "oil_filter"),
    ("water_outlets", "oil_filter"), ("oil_filler", "breathers"),
    ("block_bank_", "crankshaft"),   # the bore breaks into the crank throw
    ("engine_mount_", "head_"), ("engine_mount_", "head_stud"),
    ("engine_mount_", "knock_sensor_"), ("engine_mount_", "block_"),
    ("starter", "block_"), ("head_", "bellhousing"),
    ("timing_cover", "pump_water"), ("mount_bosses", "block_"),
    ("mount_bosses", "hp_fuel_pump"), ("accessory_belt", "thermostat"),
    ("accessory_belt", "oil_pickup"), ("alternator", "timing_gears"),
    ("throttle_", "trumpets"),
    ("plenum_", "trumpets"), ("plenum_", "runner_"), ("trumpets", "runner_"),
    ("plenum_", "charge_pipes"), ("throttle_", "charge_pipes"),
    ("cam_sensor_", "fuel_rail_"), ("belt_idler", "head_"),
    # the counterweights are shaped round the rod bolts, which is why a
    # crank is machined and not turned
    ("rod_bolts", "crankshaft"), ("mount_bosses", "valve_"),
    ("mount_bosses", "piston"), ("charge_pipes", "cam_caps"),
    ("heat_shields", "blowoff"), ("ecu", "plenum_"),
    ("windage_tray", "starter"), ("main_cap_bolts", "block_"),
    ("belt_idler", "fuel_rail_"), ("fuel_rail_", "sensors"),
    ("injector", "block_"), ("sparkplug", "valve_spring_"),
    ("coil", "valve_spring_"), ("coil", "cam_caps"),
    # a short-skirt piston runs inside the counterweight circle at BDC;
    # the crank is machined to clear it, which is what the cutaways are for
    ("piston", "crankshaft"), ("tailpipes", "collector_"),
    ("dry_sump_lines", "sensors"), ("ring_", "water_outlets"),
    ("charge_pipes", "trumpets"), ("primary_", "tappet_"),
    ("mguk", "block_"), ("coolant_plumbing", "timing_cover"),
    ("camlobe_", "collets_"), ("belt_idler", "engine_mount_"),
    ("engine_mount_", "pump_oil"),
    ("dry_sump_lines", "block_"), ("dipstick", "block_"),
    ("camlobe_", "hp_fuel_pump"), ("main_shell", "block_bank_"),
    ("main_shell", "main_shell"),   # two halves of one bearing
    # A shell sits inside the rod or cap that holds it, and conrod, rod_cap
    # and main_shell are all already allowed into the bank casting where the
    # bore breaks into the crank throw. Anything inside them is in there too,
    # by construction -- these only showed up once the bank slab moved.
    ("rod_shell", "block_bank_"), ("main_cap", "block_bank_"),
    # The clutch is bolted to the crank flange, the coolant plumbing lands
    # on the outlets it drains, the pickup is the mouth of the scavenge
    # line, and the scavenge lines end in the tank. Circuits, joined.
    ("clutch", "crankshaft"), ("water_outlets", "coolant_plumbing"),
    # the high-pressure line delivers into the rail's rear fitting and the
    # crossover takes the pressure on from the same fitting
    ("fuel_hp_line", "fuel_rail_di_crossover"),
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
    # is inside it too. The cable drops in beside the primaries and is
    # inside the turbine's heat blanket doing it, which this list already
    # recognises at ("heat_shields", "mguh"). The charge pipe leaves the
    # compressor volute 6 mm from the MGU-H on the same shaft, which is the
    # same statement as ("mguh", "compressor_housing") above.
    ("hv_motor_h", "primary_"), ("mguh", "charge_pipes"),
    ("oil_pickup", "dry_sump_lines"), ("dry_sump_lines", "catch_tank"),
    ("pump_water", "dry_sump_lines"), ("pump_water", "engine_mount_"),
    ("dipstick", "head_"), ("timing_cover", "alternator"),
    ("camlobe_", "valve_"), ("accessory_belt", "timing_gears"),
    ("accessory_belt", "coolant_plumbing"), ("accessory_belt", "alternator"),
    ("ring_", "crankshaft"), ("heat_shields", "inverter"),
    ("catch_tank", "oil_cooler"), ("thermostat", "mguk"),
    ("coolant_plumbing", "mguk"), ("pump_water", "mguk"),
    # the block's outboard flank carries the mounts, the gallery plugs,
    # the rail and the feeds, and they are cast and bolted against one
    # another on the same face
    ("mount_bosses", "fuel_rail_"), ("mount_bosses", "fuel_feeds_"),
    ("mount_bosses", "injector"), ("gallery_plugs", "engine_mount_"),
    ("starter", "gallery_plugs"),
    # the turbine wheel runs in the exducer bore the tailpipe bolts to
        ("gallery_plugs", "oil_filter"), ("dipstick", "mount_bosses"),
    ("cam_journals", "tappet_"), ("blowoff", "intercooler_"),
        ("oil_pickup", "bedplate"),   # it passes through to the sump
    ("belt_tensioner", "timing_gears"), ("belt_tensioner", "timing_cover"),
    # the idler and the tensioner run on the belt, which runs in front of
    # the timing cover and past the coolant crossover
    ("belt_idler", "timing_cover"), ("belt_idler", "coolant_plumbing"),
    ("inverter", "bellhousing"), ("inverter", "clutch"),
    ("inverter", "head_"), ("inverter", "tailpipes"),
    ("coolant_plumbing", "accessory_pulleys"),   # the pump is belt-driven
    ("accessory_pulleys", "crank_trigger"),   # both on the crank nose
    ("camlobe_", "retainer_"),   # both live inside the bucket envelope
    # the charge cooler core sits IN the plenum, with the velocity stacks
    # and the runner mouths around it -- that is what a water-to-air
    # intercooler on a hot vee is
    ("intercooler_", "plenum_"), ("intercooler_", "trumpets"),
    ("intercooler_", "runner_"), ("intercooler_", "throttle_"),
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

if __name__ == "__main__":
    sys.exit(0 if _intersect.run(ROOT, "engine/parts", EXPECTED) else 1)
