"""Score one forecast file: `python src/score.py data/forecasts/f00042.npz`.

Loads the forecast and the matching observations, computes CRPS, pinball loss and coverage, and prints one JSON
line. One file takes about 5 seconds on one CPU (most of it is loading). There are 6,000 files in data/forecasts/
(f00000.npz ... f05999.npz).
"""
import json
import sys
from pathlib import Path

import numpy as np


def score(path: Path) -> dict:
    f = np.load(path)
    obs = np.load(Path("data/observations") / path.name)
    ...   # CRPS, pinball loss and coverage of f["quantiles"] against obs["y"]
    return {"file": path.name, "crps": 0.0, "pinball": 0.0, "coverage": 0.0}


if __name__ == "__main__":
    print(json.dumps(score(Path(sys.argv[1]))))
