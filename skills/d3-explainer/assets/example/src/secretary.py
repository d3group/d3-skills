"""Cutoff rule for sequential selection (the secretary problem). Toy project of the d3-explainer example."""
import json
import sys

import numpy as np


def success_probability(r: int, n: int) -> float:
    """Probability that the rule 'skip r - 1 candidates, then take the first record' picks the best of n."""
    if r <= 1:
        return 1.0 / n
    return (r - 1) / n * sum(1.0 / (k - 1) for k in range(r, n + 1))


def optimal_cutoff(n: int) -> int:
    """Exact finite-n optimum by enumeration. The paper analyses the limit of large n instead."""
    return max(range(1, n + 1), key=lambda r: success_probability(r, n))


def run_once(scores: np.ndarray, r: int) -> bool:
    """Apply the rule to one arrival order. True if the overall best candidate is chosen."""
    benchmark = scores[: r - 1].max() if r > 1 else -np.inf
    for s in scores[r - 1:]:
        if s > benchmark:
            return bool(s == scores.max())
    return False  # nobody beat the benchmark: the best was among the skipped candidates


def simulate(r: int, n: int, reps: int, rng: np.random.Generator) -> float:
    return float(np.mean([run_once(rng.random(n), r) for _ in range(reps)]))


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    out = {"note": "share of runs in which the best candidate was chosen, 20000 replications per cutoff"}
    for n, step in ((20, 1), (100, 5)):
        rs = list(range(1, n + 1, step))
        out[f"n{n}"] = {"r": rs, "simulated": [round(simulate(r, n, 20000, rng), 4) for r in rs],
                        "exact": [round(success_probability(r, n), 4) for r in rs], "optimal_r": optimal_cutoff(n)}
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "results/success.json", "w"))
