"""Hyperparameter sweep of the forecasting model: one training per call, one call per Slurm job.

The grid (4 learning rates x 3 hidden widths x 4 seeds = 48 trainings) is written by src/make_configs.py as one
config per combination to configs/sweep/. On the server each config is one run: `d3run.py new --config
configs/sweep/*.json` books the 48 runs and `d3run.py submit` starts each as its own 1-GPU job (jobs/train.sbatch).
One training (200 epochs) takes about 90 minutes on an RTX 4090.

    python src/sweep.py --config configs/smoke/smoke.json      # on the laptop (CPU) or in a job
    python src/sweep.py                                       # in a job: reads runs/<run id>/config.json

The training saves a checkpoint (model, optimizer, RNG state, epoch) at the end of an epoch on a timer and resumes
from the newest one, so a job that is stopped or dies continues where it was (tools/d3job.py). Data loader workers
follow SLURM_CPUS_PER_TASK (one CPU drives the GPU, the others load batches); the batch order does not depend on
the number of workers. The result is runs/<run id>/results/lr<lr>_w<width>_s<seed>.json, as before.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))     # d3job.py lives in tools/
from d3job import RunContext  # noqa: E402

DATA = Path("data/processed/load.npy")
BATCH_SIZE = 256
KEYS = {"lr": float, "width": int, "seed": int, "epochs": int}


def load_config(path: Path) -> dict:
    """Read one config and check its types (a JSON 1 for a learning rate is accepted as 1.0)."""
    cfg = json.loads(Path(path).read_text())
    missing = [k for k in KEYS if k not in cfg]
    if missing:
        raise ValueError(f"{path}: missing {missing}")
    for key, typ in KEYS.items():
        val = cfg[key]
        if typ is float and isinstance(val, int) and not isinstance(val, bool):
            val = float(val)
        if isinstance(val, bool) or not isinstance(val, typ):
            raise TypeError(f"{path}: {key} must be {typ.__name__}, got {val!r}")
        cfg[key] = val
    if cfg["lr"] <= 0 or cfg["width"] < 1 or cfg["epochs"] < 1:
        raise ValueError(f"{path}: lr > 0, width >= 1 and epochs >= 1 expected")
    return cfg


def unit_name(cfg: dict) -> str:
    return f"lr{cfg['lr']:g}_w{cfg['width']}_s{cfg['seed']}"


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if os.environ.get("SLURM_JOB_ID"):
        # A GPU job that sees no GPU must not train on one CPU for days.
        raise RuntimeError("no GPU visible in this Slurm job: submit with --gpus 1")
    return torch.device("cpu")                                      # laptop test


def train(cfg: dict, ctx: RunContext, device: torch.device, workers: int, data_path: Path) -> float:
    """Train one configuration; returns the loss of the last batch. Exits with 0 when the job's time is up."""
    epochs = cfg["epochs"]
    torch.manual_seed(cfg["seed"])
    data = torch.tensor(np.load(data_path), dtype=torch.float32)
    x, y = data[:, :-1], data[:, -1:]
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=BATCH_SIZE, shuffle=True,
                                         num_workers=workers, pin_memory=device.type == "cuda")
    width = cfg["width"]
    model = nn.Sequential(nn.Linear(x.shape[1], width), nn.ReLU(), nn.Linear(width, width), nn.ReLU(),
                          nn.Linear(width, 1)).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=cfg["lr"])

    start, last_loss = 0, float("nan")
    ckpt = ctx.latest_checkpoint()
    if ckpt:
        state = torch.load(ckpt, map_location="cpu")
        model.load_state_dict(state["model"])
        optim.load_state_dict(state["optim"])
        torch.set_rng_state(state["rng_torch"])                     # the next epochs shuffle as without a stop
        if device.type == "cuda" and state.get("rng_cuda") is not None:
            torch.cuda.set_rng_state_all(state["rng_cuda"])
        start, last_loss = state["epoch"] + 1, state["loss"]
        print(f"resumed from checkpoint {ckpt.name}: continuing at epoch {start + 1} of {epochs}", flush=True)
    else:
        print(f"fresh start: {epochs} epochs", flush=True)
    ctx.mark("running", progress=start / epochs)

    for epoch in range(start, epochs):
        t0 = time.monotonic()
        for xb, yb in loader:
            loss = nn.functional.mse_loss(model(xb.to(device, non_blocking=True)), yb.to(device, non_blocking=True))
            optim.zero_grad()
            loss.backward()
            optim.step()
        last_loss = loss.item()
        if epoch == start or (epoch + 1) % 10 == 0 or epoch + 1 == epochs:
            print(f"epoch {epoch + 1}/{epochs} loss {last_loss:.6g} {time.monotonic() - t0:.1f} s", flush=True)
        if ctx.should_checkpoint():                                 # once per epoch: timer due or end near
            with ctx.checkpoint(epoch) as path:
                torch.save({"model": model.state_dict(), "optim": optim.state_dict(), "epoch": epoch,
                            "loss": last_loss, "rng_torch": torch.get_rng_state(),
                            "rng_cuda": torch.cuda.get_rng_state_all() if device.type == "cuda" else None}, path)
            if ctx.should_stop() and epoch + 1 < epochs:
                ctx.mark("interrupted", progress=(epoch + 1) / epochs)
                print(f"stopping after epoch {epoch + 1} of {epochs}: the next segment resumes", flush=True)
                raise SystemExit(0)
    return last_loss


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, help="config of one training (default: the run folder's config.json)")
    ap.add_argument("--data", type=Path, default=DATA, help=f"training data (default {DATA})")
    ap.add_argument("--workers", type=int, help="data loader workers (default: SLURM_CPUS_PER_TASK - 1)")
    args = ap.parse_args()

    ctx = RunContext.from_env()
    if ctx.finished():                                              # done or failed: later segments exit at once
        raise SystemExit(0)
    try:
        cfg_path = args.config or ctx.run_dir / "config.json"
        cfg = load_config(cfg_path)
        cpus = int(os.environ.get("SLURM_CPUS_PER_TASK") or 1)
        workers = args.workers if args.workers is not None else max(0, cpus - 1)
        torch.set_num_threads(max(1, cpus - workers))
        device = pick_device()
        gpu = torch.cuda.get_device_name(0) if device.type == "cuda" else "none"
        print(f"run {ctx.run_id} attempt {ctx.attempt}: config {cfg_path} {cfg}", flush=True)
        print(f"torch {torch.__version__}, cuda available {torch.cuda.is_available()}, GPU {gpu}, "
              f"CPUs {cpus}, loader workers {workers}, data {args.data}", flush=True)

        final_loss = train(cfg, ctx, device, workers, args.data)

        name = unit_name(cfg)
        result = {"lr": cfg["lr"], "width": cfg["width"], "seed": cfg["seed"], "final_loss": final_loss,
                  "epochs": cfg["epochs"], "run_id": ctx.run_id}
        out = ctx.results_dir / f"{name}.json"
        tmp = out.with_name(f".{out.name}.tmp")
        tmp.write_text(json.dumps(result) + "\n")
        os.replace(tmp, out)
        print("done", name, {"final_loss": final_loss}, flush=True)
        ctx.finish(final_loss=final_loss)                           # uploads results/ to S3, marks the run done
    except Exception as exc:
        ctx.fail(exc)
        raise


if __name__ == "__main__":
    main()
