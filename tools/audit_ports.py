"""Every port is connected.

    python3 tools/audit_ports.py            (runs itself under Blender)
    python3 tools/audit_ports.py --shrink   (after a fix: drop what is fixed)

The other audits ask whether parts overlap, touch and form circuits. None of
them asks whether the end of a hose is on anything, or whether a plug has a
cable in it -- and a part touches the assembly through its other end, so a
cable that stops in the air beside its plug passes all of them.

Every mesh.pipe end the parts are built with -- hose, line, cable, loom -- must
run into something: material, or a surface within 2.5 mm, 3 mm past its cap.
Every shapes.connector housing must have a pipe ending in or against it.

FREE names the ends that are free by design -- an exhaust's exit, a
dipstick's handle, a blanking cover's face -- each with the reason.
OPEN lists what is known to be open. It only gets shorter: anything new fails,
and anything fixed fails until --shrink drops it. --shrink never adds.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PKG = "engine/parts"
UNIT = 1.0

FREE = {
    "end port_covers @ 0,0,393": "the shipping cover over the airbox flange; "
                                 "its face is the outside",
    "end dipstick @ -28,-162,-140": "the dipstick's handle",
    "end dipstick @ -82,-162,-140": "the dipstick's end, in the oil inside "
                                    "the tank",
    "end coolant_plumbing @ -210,215,-60": "the pump inlet tee's capped end, "
                                           "past the radiator return's branch",
}

# --- OPEN: rewritten by --shrink, never by hand to add ---
OPEN = {
}
# --- end OPEN ---

if __name__ == "__main__":
    import _interfere
    sys.exit(_interfere.ports_main(__file__, ROOT, PKG, OPEN, UNIT,
                                     FREE))
