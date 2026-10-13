# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "scipy",
#     "pandas",
#     "altair",
# ]
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium", app_title="Toy Factory", css_file="uw.css")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import altair as alt
    from scipy.optimize import linprog, milp, LinearConstraint, Bounds
    return Bounds, LinearConstraint, alt, linprog, milp, mo, np, pd


# After copying this file into <site>/apps/, run `python scripts/inline_uw_css.py` in <site>:
# it inserts the style cell here (the WASM export ignores css_file).


@app.cell
def _(mo):
    mo.md(
        """
        <p class="kicker">Decision Support Systems · Universität Würzburg</p>

        # The Toy Factory

        One question in one sentence, in bold: **which product mix maximizes the weekly profit?**
        Then one sentence on what the reader can do on this page.
        """
    )
    return


@app.cell
def _(mo, pd):
    def load_csv(name, **kw):
        """Read <app dir>/public/data/<name>: open_url in the browser (WASM), a plain path or URL locally."""
        path = str(mo.notebook_location() / "public" / "data" / name)
        try:
            from pyodide.http import open_url
            return pd.read_csv(open_url(path), **kw)
        except ImportError:
            return pd.read_csv(path, **kw)
    return (load_csv,)


@app.cell
def _(mo):
    soldier_limit = mo.ui.slider(0, 80, value=40, step=5, label="Soldiers we can sell", show_value=True)
    finishing = mo.ui.slider(60, 140, value=100, step=10, label="Finishing hours", show_value=True)
    mo.vstack([mo.md(f"## {mo.icon('lucide:sliders-horizontal', color='#ED6A5B')} Your assumptions"),
               mo.hstack([soldier_limit, finishing], justify="start", gap=3)])
    return finishing, soldier_limit


@app.cell
def _(finishing, linprog, np, soldier_limit):
    # max 3 x1 + 2 x2  s.t.  x1 + x2 <= 80 (carpentry), 2 x1 + x2 <= finishing, x1 <= soldier limit, x >= 0
    result = linprog(-np.array([3, 2]), A_ub=[[1, 1], [2, 1], [1, 0]],
                     b_ub=[80, finishing.value, soldier_limit.value], bounds=(0, None), method="highs")
    return (result,)


@app.cell
def _(alt, mo, pd, result):
    _x = result.x
    _bars = (alt.Chart(pd.DataFrame({"toy": ["soldiers", "trains"], "units": _x}))
             .mark_bar(color="#02246C").encode(x=alt.X("units:Q", title="units per week"), y=alt.Y("toy:N", title=None))
             .properties(height=90, width=420))
    mo.vstack([
        mo.md(f"## {mo.icon('lucide:factory', color='#ED6A5B')} The best plan"),
        mo.hstack([mo.stat(f"{-result.fun:.0f} $", label="weekly profit"),
                   mo.stat(f"{_x[0]:.0f} / {_x[1]:.0f}", label="soldiers / trains")], justify="start", gap=2),
        _bars,
    ])
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        Solved in your browser with SciPy's HiGHS solver. *Decision Support Systems, University of Würzburg.*
        """
    )
    return


if __name__ == "__main__":
    app.run()
