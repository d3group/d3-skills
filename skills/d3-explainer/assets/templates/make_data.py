# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]          # list what the project's functions need; nothing is installed globally
# ///
"""Compute the numbers of one explainer figure with the project's own code.

    uv run explainer/data/make_data.py            # from the repository root; writes explainer/data/<name>.json

Copy this template to explainer/data/make_data.py and adapt the three marked places. It lives next to its output so
that a co-author can regenerate the data. It never writes into the repository's own folders.
If the project needs its full environment (heavy or pinned dependencies), run it with that instead:
    uv run --project . python explainer/data/make_data.py
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True                       # importing project modules must not leave __pycache__ in the repo
HERE = Path(__file__).resolve().parent
REPO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parents[1]
sys.path.insert(0, str(REPO))                        # 1. adapt if the package root is REPO / "src"

from src.model import evaluate                       # 2. the project's own function(s)  # noqa: E402

grid = [i / 50 for i in range(51)]                   # 3. the values the figure's slider will snap to
out = {"x": grid, "y": [float(evaluate(x)) for x in grid],
       "source": "src/model.py:evaluate", "note": "computed by the repository's code; regenerate with make_data.py"}
(HERE / "figure_data.json").write_text(json.dumps(out, separators=(",", ":")))
print(f"wrote {HERE / 'figure_data.json'} ({len(grid)} points)")
