"""Hyperparameter sweep of the forecasting model: `python src/sweep.py`.

Trains every combination of learning rate, hidden width and seed, one after another, and writes one JSON per
combination to results/. One training (200 epochs) takes about 90 minutes on an RTX 4090, so the whole grid
(4 x 3 x 4 = 48 trainings) takes about three days on one GPU.
"""
import itertools
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

LRS = [1e-4, 3e-4, 1e-3, 3e-3]
WIDTHS = [128, 256, 512]
SEEDS = [0, 1, 2, 3]
EPOCHS = 200


def train(lr: float, width: int, seed: int, data: torch.Tensor) -> dict:
    torch.manual_seed(seed)
    x, y = data[:, :-1], data[:, -1:]
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=256, shuffle=True)
    model = nn.Sequential(nn.Linear(x.shape[1], width), nn.ReLU(), nn.Linear(width, width), nn.ReLU(),
                          nn.Linear(width, 1)).cuda()
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    for epoch in range(EPOCHS):
        for xb, yb in loader:
            loss = nn.functional.mse_loss(model(xb.cuda()), yb.cuda())
            optim.zero_grad(); loss.backward(); optim.step()
    return {"final_loss": loss.item()}


def main() -> None:
    data = torch.tensor(np.load("data/processed/load.npy"), dtype=torch.float32)
    out = Path("results"); out.mkdir(exist_ok=True)
    for lr, width, seed in itertools.product(LRS, WIDTHS, SEEDS):
        metrics = train(lr, width, seed, data)
        name = f"lr{lr:g}_w{width}_s{seed}"
        (out / f"{name}.json").write_text(json.dumps({"lr": lr, "width": width, "seed": seed, **metrics}))
        print("done", name, metrics)


if __name__ == "__main__":
    main()
