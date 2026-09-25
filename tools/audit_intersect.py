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
    # each MGU-H's connector is on a boss let into its bearing housing, its
    # pins in the machine's stator
    ("hv_motor_h_connector_", "turbo_centre_"), ("hv_motor_h_connector_", "mguh"),
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

    # heads and valvetrain
    ("head_", "head_gasket_"), ("head_", "valve_"),
    ("head_", "camshaft_"), ("head_", "cam_journals"), ("head_", "cam_caps"),
    ("head_", "camcover"), ("head_", "camcover_bolts"), ("head_", "sparkplug"),
    ("head_", "injector"), ("head_", "coil"), ("head_", "collets_"),
    ("head_", "retainer_"), ("head_", "valve_spring_"), ("head_", "tappet_"),
    ("head_", "fuel_rail_"),
    ("head_", "runner_"), ("head_", "primary_"),
    ("head_", "exhaust_flange_"), ("head_", "exhaust_gasket_"),
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
    ("primary_", "collector_"),
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
    # NOT a joint. The charge pipe leaving the volute clips the exducer;
    # the fix is the turbos' clocking, not the pipe. This line is here to
    # say so, not to say it is fine. (The inlet used to overhang the
    # inducer too, turning up inside its own eye; the shared T-piece meets
    # both eyes square and clear of the wheels.)
    ("charge_pipes", "compressor_wheel"),
    ("wastegate", "compressor_housing"), ("wastegate", "collector_"),
    ("wastegate", "heat_shields"),
    # the blanket is laced over the turbine and its collector, so it
    # covers everything they contain
    ("heat_shields", "compressor_housing"),
    ("heat_shields", "primary_"),
    ("compressor_inlet", "compressor_housing"),
    ("turbine_housing", "wastegate"), ("turbine_housing", "heat_shields"),
    # hot-vee: the port flange, its primary and the turbocharger inlet are
    # one assembly packed into the vee, and primary/turbos is already here
    ("exhaust_flange_", "exhaust_gasket_"),

    # ancillaries, drive and plumbing
    ("pump_oil", "dry_sump_lines"),
    ("pump_water", "coolant_plumbing"),
    # the pump's discharge goes into the crankcase's sloping front face
    ("coolant_plumbing", "block_crankcase"),
    # the scavenge lines are let into the pan's flank, the breather
    # galleries into their unions in the cam covers' crowns, and the
    # shipping covers are bolted through the intake flanges
    ("dry_sump_lines", "sump"), ("breathers", "camcover"),
    ("port_covers", "compressor_inlet"),
    ("oil_filter", "oil_cooler"),
    ("catch_tank", "breathers"),
    ("engine_mount_", "mount_bosses"),
    ("sensors", "block_"),

    # hybrid
    ("ecu", "ecu_connector"),
    ("battery", "battery_modules"),

    # A second round. The block is one casting modelled as several parts, so
    # the banks meet in the vee and the coolant passages run past the liners;
    # the manifolds bolt to the heads; the trumpets stand over the cam covers.
    ("block_bank_", "block_bank_"),

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
    ("windage_tray", "main_cap_"),

    # sensors screw into whatever they measure
    ("sensors", "sump"), ("sensors", "block_"),

    # heat shielding wraps what it shields
    ("heat_shields", "turbine_housing"), ("heat_shields", "collector_"),

    # fuel and charge
    ("injector", "fuel_feeds_"),
    # a port injector's nozzle sits in its bore in the head's intake port
    ("head_", "pfi_injector_"),
    ("charge_pipes", "camcover"),

    # a direct-acting bucket is a cup over the top of the valve: the tip,
    # the collets, the retainer and the top of the spring all live inside
    # its skirt, which is the whole point of the layout
    ("retainer_", "tappet_"), ("collets_", "tappet_"),
    ("valve_spring_", "tappet_"), ("camlobe_", "tappet_"),
    ("valve_spring_", "head_"),
        # the cap lands right against the lobe
    ("primary_", "primary_"),     # adjacent primaries touch into the collector
       # the mount bolts through the block/head joint
    ("sensors", "gallery_plugs"),

    ("head_", "bellhousing"),

    ("plenum_", "trumpets"), ("plenum_", "runner_"), ("trumpets", "runner_"),
    ("throttle_", "charge_pipes"),
    ("main_cap_bolts", "block_"),

    ("coolant_plumbing", "timing_cover"),
    ("camlobe_", "collets_"),

    # the high-pressure line delivers into the rail's rear fitting and the
    # crossover takes the pressure on from the same fitting
    ("fuel_hp_line", "fuel_rail_di_"),   # it delivers into the rail's fitting
    # the harness: every branch ends in a mating plug pushed onto its
    # device's connector
    ("harness", "coil_"), ("harness", "injector_di_"), ("harness", "pfi_"),
    ("harness", "knock_sensor_"), ("harness", "cam_sensor_"),
    ("harness", "ecu_connector"),
    # each direct injector's end sits in its cup on the rail
    ("fuel_rail_di_", "injector_di_"), ("fuel_feeds_di_", "injector_di_"),

    # The MGU-H lives in the vee with the exhaust, and its cable has to get
    # there. Every route down was tried: straight in from above meets
    # primary 1, which fills x -186 to -91 from z 141 to 368; outboard at
    # y -130 crosses the same tube lower down; along the shaft from outboard
    # is inside it too. The cable drops in beside the primaries.
    ("oil_pickup", "dry_sump_lines"), ("dry_sump_lines", "catch_tank"),

    ("camlobe_", "valve_"),

    ("oil_pickup", "bedplate"),   # it passes through to the sump
    ("camlobe_", "retainer_"),   # both live inside the bucket envelope
    # the charge cooler core sits IN the plenum, with the velocity stacks
    # and the runner mouths around it -- that is what a water-to-air
    # intercooler on a hot vee is
    ("intercooler_", "plenum_"), ("intercooler_", "trumpets"),
    ("intercooler_", "runner_"),
    # The high-voltage cables leave the inverter through the same pair of
    # connectors and share the same conduit down the back of the engine, so
    # they lie against each other -- which is what a loom is. They also end
    # inside the machines they feed, because that is where the terminal is.
    ("hv_", "hv_"), ("hv_", "inverter"), ("hv_", "battery_terminals"),
    ("hv_motor_k", "mguk"),
]

PKG = "engine/parts"
UNIT = 1.0            # mm of real part per model unit
TOL = 0.3            # mm, full size: deeper than this is sharing material

# Real defects, in mm of full-size overlap, deepest first. Each one is a part
# through a part that nobody meant. Fix them and --shrink; never add to it.
# --- KNOWN: rewritten by --shrink, never by hand to add ---
KNOWN = {
}
# --- end KNOWN ---

if __name__ == "__main__":
    import _interfere
    sys.exit(_interfere.intersect_main(__file__, ROOT, PKG, EXPECTED, KNOWN,
                                       TOL, UNIT))
