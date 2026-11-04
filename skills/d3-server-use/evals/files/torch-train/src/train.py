"""Train a sequence model on the load data. Takes about 30 hours on one RTX 4090 (120 epochs)."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

p = argparse.ArgumentParser()
p.add_argument("--epochs", type=int, default=120)
p.add_argument("--data", default="data/processed/load.npy")
p.add_argument("--out", default="results")
args = p.parse_args()

torch.manual_seed(0)
x = torch.tensor(np.load(args.data), dtype=torch.float32)
loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x[:, :-1], x[:, -1:]), batch_size=256, shuffle=True)
model = nn.Sequential(nn.Linear(x.shape[1] - 1, 512), nn.ReLU(), nn.Linear(512, 1)).cuda()
optim = torch.optim.AdamW(model.parameters(), lr=1e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=args.epochs)
for epoch in range(args.epochs):
    for xb, yb in loader:
        loss = nn.functional.mse_loss(model(xb.cuda()), yb.cuda())
        optim.zero_grad(); loss.backward(); optim.step()
    sched.step()
    print(f"epoch {epoch} loss {loss.item():.4f}")
Path(args.out).mkdir(exist_ok=True)
torch.save(model.state_dict(), Path(args.out) / "model.pt")
json.dump({"final_loss": loss.item()}, open(Path(args.out) / "metrics.json", "w"))
