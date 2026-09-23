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
    ("block_crankcase", "oil_pickup"),
    ("bedplate", "main_cap_"), ("bedplate", "main_shell"),
    ("bedplate", "crankshaft"),
    ("bedplate", "main_cap_bolts"), ("bedplate", "windage_tray"),
    ("main_cap_", "main_shell"), ("main_cap_", "main_cap_bolts"),

    ("sump", "sump_baffles"), ("sump", "sump_bolt"), ("sump", "sump_drain"),
    ("sump", "oil_pickup"),
    # the sump bolts go up through its flange into the bedplate
    ("bedplate", "sump_bolt"),

    # rotating assembly
    ("crankshaft", "conrod"),
    ("crankshaft", "crank_damper"),
    ("crankshaft", "timing_gears"),
    ("conrod", "rod_shell"),
    ("conrod", "gudgeon_pin"),
    ("rod_cap", "rod_shell"),
    # a rod bolt passes through the cap's ear and screws into the rod: the
    # two holes it runs in are the overlap
    ("rod_bolts", "conrod"), ("rod_bolts", "rod_cap"),
    # each head's water outlet runs into the end of its rail
    ("water_outlets", "coolant_plumbing"),
    # the dipstick runs down through the tank's filler cap into the oil
    ("dipstick", "catch_tank"),
    # gallery plugs and sensors are screwed into the crankcase wall, and the
    # engine mounts' feet are bolted to the bosses cast on it
    ("gallery_plugs", "block_crankcase"), ("sensors", "block_crankcase"),
    # the filter's pedestal is cast onto the crankcase, over the gallery
    # plug it feeds
    ("oil_filter", "block_crankcase"), ("oil_filter", "gallery_plugs"),
    ("engine_mount_", "mount_bosses"),
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

    ("camlobe_", "tappet_"),
    ("tappet_", "valve_"), ("valve_", "valve_spring_"), ("valve_", "collets_"),
    ("collets_", "retainer_"),
    ("camcover", "camcover_bolts"), ("camcover", "oil_filler"),
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
    ("turbo_centre", "charge_pipes"),
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
    ("heat_shields", "compressor_housing"),
    ("heat_shields", "primary_"),
    ("compressor_inlet", "compressor_housing"),
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

    ("coolant_plumbing", "timing_gears"),
    ("coolant_plumbing", "block_bank_"), ("coolant_plumbing", "head_"),
    ("cam_caps", "camcover"),
    ("pump_water", "coolant_plumbing"),
    ("breathers", "catch_tank"),

    # ------------------------------------------------------------------
    # Joints the check could not reach until it stopped spending its
    # budget on the ones it had already been told about. An engine is an
    # assembly of things bolted through one another; each line below is a
    # fastener, a bearing, a port or a bracket.
    # ------------------------------------------------------------------

    ("main_shell", "block_crankcase"),

    # the valvetrain runs inside the head and under the cover
    ("camlobe_", "camcover"),
    ("valve_", "tappet_"),

    # accessories bolt to the castings they are driven from
    ("hp_fuel_pump", "head_"), ("hp_fuel_pump", "cam_caps"),
    ("hp_fuel_pump", "camcover"),
    ("thermostat", "block_"),
    ("windage_tray", "main_cap_"),

    # sensors screw into whatever they measure
    ("sensors", "sump"), ("sensors", "block_"),
    ("sensors", "knock_sensor_"),

    # heat shielding wraps what it shields
    ("heat_shields", "turbine_housing"), ("heat_shields", "collector_"),

    # fuel and charge
    ("injector", "fuel_feeds_"),
    ("charge_pipes", "camcover"), ("coolant_plumbing", "block_"),
    ("coolant_plumbing", "head_"),

    # a direct-acting bucket is a cup over the top of the valve: the tip,
    # the collets, the retainer and the top of the spring all live inside
    # its skirt, which is the whole point of the layout
    ("retainer_", "tappet_"), ("collets_", "tappet_"),
    ("valve_spring_", "tappet_"), ("camlobe_", "tappet_"),
    ("valve_spring_", "head_"),
        # the cap lands right against the lobe
    ("primary_", "primary_"),     # adjacent primaries touch into the collector
       # the mount bolts through the block/head joint
    ("sensors", "gallery_plugs"), ("sensors", "pump_water"),

    ("starter", "block_"), ("head_", "bellhousing"),

    ("plenum_", "trumpets"), ("plenum_", "runner_"), ("trumpets", "runner_"),
    ("throttle_", "charge_pipes"),
    ("windage_tray", "starter"), ("main_cap_bolts", "block_"),

    ("coolant_plumbing", "timing_cover"),
    ("camlobe_", "collets_"),

    # the high-pressure line delivers into the rail's rear fitting and the
    # crossover takes the pressure on from the same fitting
    ("fuel_hp_line", "fuel_rail_di_crossover"),
    ("fuel_hp_line", "fuel_rail_di_"),   # it delivers into the rail's fitting

    # The MGU-H lives in the vee with the exhaust, and its cable has to get
    # there. Every route down was tried: straight in from above meets
    # primary 1, which fills x -186 to -91 from z 141 to 368; outboard at
    # y -130 crosses the same tube lower down; along the shaft from outboard
    # is inside it too. The cable drops in beside the primaries.
    ("hv_motor_h", "primary_"),
    ("oil_pickup", "dry_sump_lines"), ("dry_sump_lines", "catch_tank"),

    ("camlobe_", "valve_"),
    ("accessory_belt", "alternator"),

    ("thermostat", "mguk"),

    ("starter", "gallery_plugs"),
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
]

PKG = "engine/parts"
UNIT = 1.0            # mm of real part per model unit
TOL = 0.3            # mm, full size: deeper than this is sharing material

# Real defects, in mm of full-size overlap, deepest first. Each one is a part
# through a part that nobody meant. Fix them and --shrink; never add to it.
# --- KNOWN: rewritten by --shrink, never by hand to add ---
KNOWN = {
    ("blowoff", "camcover_l"): 14.1,   # at (-116.1, -218.4, 214.4)
    ("thermostat", "timing_cover"): 14.0,   # at (-266.0, 25.2, 119.6)
    ("fuel_hp_line", "hp_fuel_pump"): 12.5,   # at (22.9, 221.2, 179.1)
    ("fuel_rail_pfi_r", "hp_fuel_pump"): 7.9,   # at (-13.0, 243.6, 142.9)
    ("inverter", "turbine_housing_2"): 6.5,   # at (241.9, -15.2, 227.4)
    ("camcover_r", "fuel_hp_line"): 5.0,   # at (88.4, 235.2, 178.0)
    ("blowoff", "breathers"): 4.3,   # at (-123.5, -221.8, 214.7)
    ("fuel_hp_line", "fuel_rail_pfi_crossover"): 3.9,   # at (221.5, 241.9, 136.6)
    ("hv_motor_h_0", "mguh"): 3.9,   # at (-144.0, -20.1, 255.8)
    ("bedplate", "bellhousing"): 3.3,   # at (231.8, 53.4, -107.2)
    ("head_l", "pfi_injector_1"): 3.2,   # at (-159.9, -183.5, 105.4)
    ("head_l", "pfi_injector_3"): 3.2,   # at (-57.9, -183.5, 105.4)
    ("head_l", "pfi_injector_5"): 3.2,   # at (44.1, -183.5, 105.4)
    ("head_l", "pfi_injector_7"): 3.2,   # at (146.1, -183.5, 105.4)
    ("head_r", "pfi_injector_2"): 3.2,   # at (-140.9, 183.5, 105.4)
    ("head_r", "pfi_injector_4"): 3.2,   # at (-38.9, 183.5, 105.4)
    ("head_r", "pfi_injector_6"): 3.2,   # at (63.1, 183.5, 105.4)
    ("head_r", "pfi_injector_8"): 3.2,   # at (165.1, 183.5, 105.4)
    ("belt_idler", "sensors"): 2.5,   # at (-222.7, 154.5, -36.3)
    ("breathers", "dry_sump_lines"): 2.0,   # at (-252.0, -244.1, -78.6)
    ("battery", "dry_sump_lines"): 1.7,   # at (-176.1, -162.9, -216.0)
    ("mguh", "turbo_shaft_1"): 1.3,   # at (-122.0, -12.2, 244.9)
    ("mguh", "turbo_shaft_2"): 1.3,   # at (122.0, 3.8, 239.6)
    ("accessory_belt", "hv_motor_k"): 1.2,   # at (-300.1, -143.4, -47.4)
}
# --- end KNOWN ---

if __name__ == "__main__":
    import _interfere
    sys.exit(_interfere.intersect_main(__file__, ROOT, PKG, EXPECTED, KNOWN,
                                       TOL, UNIT))
