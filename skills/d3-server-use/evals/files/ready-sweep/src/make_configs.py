"""Write the sweep grid as one config per training, and check every config of the round.

    python src/make_configs.py            # writes configs/sweep/*.json (48) and configs/smoke/*.json, then checks
    python src/make_configs.py --check    # only parse and type-check the existing configs

Each file in configs/sweep/ becomes one run (`d3run.py new --config configs/sweep/*.json`). The smoke configs are
the same model with few epochs: smoke.json (3 epochs, imports, GPU, data path, output) and resume.json (10 epochs,
needs two 5-minute segments, so the second must resume from the first one's checkpoint).
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

LRS = [1e-4, 3e-4, 1e-3, 3e-3]
WIDTHS = [128, 256, 512]
SEEDS = [0, 1, 2, 3]
EPOCHS = 200

ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "configs" / "sweep"
SMOKE = ROOT / "configs" / "smoke"
SMOKE_CONFIGS = {"smoke": {"lr": 1e-3, "width": 128, "seed": 0, "epochs": 3},
                 "resume": {"lr": 1e-3, "width": 128, "seed": 0, "epochs": 10}}


def write() -> None:
    SWEEP.mkdir(parents=True, exist_ok=True)
    SMOKE.mkdir(parents=True, exist_ok=True)
    for lr, width, seed in itertools.product(LRS, WIDTHS, SEEDS):
        cfg = {"lr": lr, "width": width, "seed": seed, "epochs": EPOCHS}
        (SWEEP / f"lr{lr:g}_w{width}_s{seed}.json").write_text(json.dumps(cfg) + "\n")
    for name, cfg in SMOKE_CONFIGS.items():
        (SMOKE / f"{name}.json").write_text(json.dumps(cfg) + "\n")


def check() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from sweep import load_config, unit_name                      # the same parser the jobs use

    sweep = sorted(SWEEP.glob("*.json"))
    seen = {}
    for path in sweep + sorted(SMOKE.glob("*.json")):
        cfg = load_config(path)
        if path.parent == SWEEP:
            if path.stem != unit_name(cfg):
                raise SystemExit(f"{path.name}: name does not match its content ({unit_name(cfg)})")
            seen[(cfg["lr"], cfg["width"], cfg["seed"])] = path.name
    want = set(itertools.product(LRS, WIDTHS, SEEDS))
    if set(seen) != want or len(sweep) != len(want):
        raise SystemExit(f"configs/sweep has {len(sweep)} files for {len(want)} grid points: run without --check")
    print(f"ok: {len(sweep)} sweep configs, {len(list(SMOKE.glob('*.json')))} smoke configs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only check the existing configs")
    if not ap.parse_args().check:
        write()
    check()
