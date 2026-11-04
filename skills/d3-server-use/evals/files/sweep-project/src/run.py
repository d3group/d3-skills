"""Fit one model from a config: `python src/run.py --config configs/xgb/seed00.yaml`. Writes results/<config stem>/."""
import argparse
import yaml

p = argparse.ArgumentParser()
p.add_argument("--config", required=True)
cfg = yaml.safe_load(open(p.parse_args().config))
if cfg["model"] == "xgboost":
    ...   # about 2 minutes on 4 CPUs
else:
    ...   # LSTM, about 3 hours on one GPU
