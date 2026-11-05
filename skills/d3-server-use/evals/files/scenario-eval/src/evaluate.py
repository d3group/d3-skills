"""Evaluate the dispatch policy on all scenarios: `python src/evaluate.py`.

Each scenario solves a year of hourly dispatch LPs with HiGHS (single-threaded) and takes 10 to 20 minutes. There
are 1,200 scenarios in data/scenarios.parquet, about 300 CPU-hours in total. On my workstation this ran with
16 processes over a weekend; on the server I want N_JOBS = 64. All rows are written to results/all.parquet at the end.
"""
from pathlib import Path

import highspy
import pandas as pd
from joblib import Parallel, delayed

N_JOBS = 64


def evaluate(row: dict) -> dict:
    h = highspy.Highs()
    h.setOptionValue("threads", 1)
    h.setOptionValue("output_flag", False)
    cost = 0.0
    for day in range(365):
        ...   # build and solve the day's dispatch LP from the scenario's profiles, add its objective to `cost`
    return {"scenario": row["scenario"], "cost": cost}


def main() -> None:
    scenarios = pd.read_parquet("data/scenarios.parquet").to_dict("records")
    rows = Parallel(n_jobs=N_JOBS)(delayed(evaluate)(r) for r in scenarios)
    Path("results").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_parquet("results/all.parquet")


if __name__ == "__main__":
    main()
