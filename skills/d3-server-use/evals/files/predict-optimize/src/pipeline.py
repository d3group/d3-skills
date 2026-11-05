"""Predict-then-optimize study, end to end: `python src/pipeline.py`.

1. Train the price forecaster (LSTM) for each of the 3 markets: about 2 h per market on one RTX 4090.
2. Predict day-ahead prices for the 365 test days of each market with that model (a few minutes on the GPU).
3. For every market and test day, solve the battery scheduling MILP on the forecast with HiGHS (single-threaded,
   2 to 10 minutes per solve, 1,095 solves).
4. Evaluate realized profit against perfect foresight and write results/summary.csv.

On my workstation the whole script runs for about four days.
"""
from pathlib import Path

import highspy
import numpy as np
import pandas as pd
import torch
from torch import nn

MARKETS = ["DE", "FR", "NL"]
EPOCHS = 150


def train_forecaster(market: str) -> nn.Module:
    data = torch.tensor(np.load(f"data/processed/{market}_train.npy"), dtype=torch.float32)
    model = nn.LSTM(input_size=data.shape[-1], hidden_size=256, num_layers=2, batch_first=True).cuda()
    optim = torch.optim.AdamW(model.parameters(), lr=1e-3)
    for epoch in range(EPOCHS):
        ...   # one epoch over the market's training windows
    return model


def predict(model: nn.Module, market: str) -> np.ndarray:
    ...   # 365 x 24 day-ahead price forecasts for the test year
    return np.zeros((365, 24))


def schedule_battery(prices: np.ndarray) -> dict:
    h = highspy.Highs()
    h.setOptionValue("threads", 1)
    h.setOptionValue("time_limit", 900.0)
    ...   # build and solve the day's MILP (charge, discharge, state of charge, binaries)
    return {"charge": np.zeros(24), "discharge": np.zeros(24)}


def evaluate(market: str, schedules: list[dict]) -> dict:
    ...   # realized profit against perfect foresight
    return {"market": market, "profit": 0.0, "regret": 0.0}


def main() -> None:
    rows = []
    for market in MARKETS:
        model = train_forecaster(market)
        forecasts = predict(model, market)
        schedules = [schedule_battery(forecasts[day]) for day in range(365)]
        rows.append(evaluate(market, schedules))
    Path("results").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv("results/summary.csv", index=False)


if __name__ == "__main__":
    main()
