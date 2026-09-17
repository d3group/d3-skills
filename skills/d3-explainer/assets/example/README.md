# d3-explainer example fixture

A deliberately tiny research repository (one module, one paper, one results file) on a textbook topic, the
secretary problem, with a finished explainer in `explainer/`. It exists for two reasons:

1. Pattern reference: `explainer/sections/*.html` shows every component once, in working form.
2. Smoke test and eval input for the engine. Inside the skill the engine sits next to this folder:

       uv run ../d3x/build.py explainer
       uv run ../d3x/check.py explainer/dist/cutoff_rule.html --shots

   In a copy of this folder, scaffold the engine first (`uv run <skill>/scripts/init.py explainer --refresh`), then
   `uv run explainer/d3x/build.py` and `uv run explainer/d3x/check.py --shots`.

   `uv run --with numpy python src/secretary.py results/success.json` regenerates the results file.

Do not copy this folder into a user project. Test the skill on copies of this fixture, not on anyone's research repositories.
