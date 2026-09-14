"""Structural audit for the RX-8V. See tools/_structure.py for what it checks.

    python3 tools/audit_structure.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _structure as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CFG = {
    # An engine is a solid lump of parts in contact; nothing on it floats.
    "gap_mm": 0.5,
    "exempt_attached": {},

    # The two banks of a V8 are offset along the crank by one big-end width,
    # so every per-bank part is displaced, not mirrored. That offset is the
    # whole reason the two rods on a shared crankpin fit.
    "mirror_tol_mm": 1.0,
    "exempt_mirror": {
        "block_bank": "banks are offset along the crank, not mirrored",
        "head_": "sits on its bank, which is offset",
        "camcover": "sits on its bank, which is offset",
        "camshaft_": "runs down its bank, which is offset",
        "cam_journals": "on its bank, which is offset",
        "oil_filler": "on its cam cover, which is offset",
        "collector": "the two collectors merge into one pipe, asymmetrically",
        "fuel_feeds": "run to the injectors, which are on the offset banks",
        "exhaust_flange": "bolts to the head, which is offset",
        "exhaust_gasket": "between head and manifold, both offset",
    },

    "distinct_tol_mm": 0.5,
    "exempt_distinct": {},
    "exempt_shape": {},

    # Clearances live in tools/audit_clearance.py now, which measures the
    # geometry instead of the bounding boxes. A box test can only be right for
    # a part shaped like its box: the hybrid pack is two lobes straddling the
    # sump keel, so its box encloses the sump while the lobes are clear of it.
    "clearances": (
        # Only pairs whose bounding boxes mean something belong here: two
        # slabs, or a part and a plug. A turbo sitting in the vee under the
        # plenum overlaps its box by design, so testing that pair would be
        # testing the box and not the parts.
    ),

    # Things an engine has exactly one of.
    "singletons": {
        "crankshaft": (("crankshaft",), 1),
        "flywheel": (("flywheel",), 1),
        "clutch": (("clutch",), 1),
        "sump": (("sump",), 1),
        "oil pump": (("pump_oil",), 1),
        "water pump": (("pump_water",), 1),
        "plenum": (("plenum",), 1),
        "crank trigger": (("crank_trigger",), 1),
        "piston": (("piston_*",), 8),
        "conrod": (("conrod_*",), 8),
        "cylinder head": (("head_l", "head_r"), 2),
        "camshaft": (("camshaft_*",), 4),
    },

}

if __name__ == "__main__":
    n = S.report(os.path.join(ROOT, "build", "parts.csv"), CFG, "RX-8V")
    sys.exit(0 if n == 0 else 1)
