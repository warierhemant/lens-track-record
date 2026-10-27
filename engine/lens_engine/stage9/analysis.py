"""The pre-registered analysis, engine/scripts/stage9_analysis.py, loaded as a module.

The runner never re-implements an endpoint: it writes the ledger that script reads, and calls it.
"""
from __future__ import annotations

import importlib.util
import sys

from lens_engine import paths

SCRIPT = paths.ENGINE_DIR / "scripts" / "stage9_analysis.py"


def load():
    mod = sys.modules.get("stage9_analysis")
    if mod is not None and getattr(mod, "__file__", None) == str(SCRIPT):
        return mod
    spec = importlib.util.spec_from_file_location("stage9_analysis", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stage9_analysis"] = mod  # dataclasses look the module up by name
    spec.loader.exec_module(mod)
    return mod


S9 = load()
