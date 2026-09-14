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
    ("fuel_rail_", "fuel_feeds_"), ("fuel_rail_", "injector"),

    # induction and charge
    ("plenum", "trumpets"), ("plenum", "throttle"), ("plenum", "runner_"),
    ("plenum", "charge_pipes"), ("trumpets", "runner_"),
    ("throttle", "charge_pipes"), ("charge_pipes", "intercooler_"),
    ("charge_pipes", "turbos"), ("charge_pipes", "blowoff"),
    ("intercooler_", "charge_pipes"),

    # exhaust and turbos
    ("primary_", "collector_"), ("primary_", "turbos"),
    ("primary_", "exhaust_manifolds"), ("primary_", "exhaust_flange_"),
    ("primary_", "exhaust_gasket_"), ("primary_", "heat_shields"),
    ("collector_", "turbos"), ("collector_", "exhaust_manifolds"),
    ("turbos", "turbo_wheels"), ("turbos", "tailpipes"), ("turbos", "mguh"),
    ("turbos", "wastegate"), ("turbos", "heat_shields"),
    ("turbos", "catch_tank"), ("turbos", "exhaust_manifolds"),
    ("exhaust_manifolds", "heat_shields"),
    # hot-vee: the port flange, its primary and the turbocharger inlet are
    # one assembly packed into the vee, and primary/turbos is already here
    ("exhaust_flange_", "exhaust_gasket_"), ("exhaust_flange_", "turbos"),

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
    ("mguk", "bellhousing"), ("mguk", "crankshaft"), ("mguh", "turbos"),
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
    ("exhaust_manifolds", "head_"), ("exhaust_manifolds", "mguh"),
    ("exhaust_manifolds", "exhaust_flange_"), ("exhaust_manifolds", "turbos"),
    ("camcover", "trumpets"), ("cam_caps", "trumpets"),
    ("cam_caps", "camcover"), ("cam_caps", "camshaft_"),
    ("head_gasket_", "block_liners"), ("head_gasket_", "block_bank_"),
    ("mguh", "turbo_wheels"), ("pump_water", "timing_gears"),
    ("pump_water", "coolant_plumbing"), ("primary_", "catch_tank"),
    ("breathers", "catch_tank"), ("breathers", "block_"),
]

if __name__ == "__main__":
    sys.exit(0 if _intersect.run(ROOT, "engine/parts", EXPECTED) else 1)
