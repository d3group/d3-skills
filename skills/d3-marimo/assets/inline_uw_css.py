"""Copy apps/uw.css into the style cell of every app that uses it (marimo's html-wasm export ignores css_file).
Run after editing uw.css:  python scripts/inline_uw_css.py"""
import re
from pathlib import Path

css = Path("apps/uw.css").read_text()
cell = ('@app.cell(hide_code=True)\ndef _uw_style(mo):\n    # generated from apps/uw.css by scripts/inline_uw_css.py; edit uw.css, not this cell\n'
        '    mo.Html("""<style>\n' + css.replace('\\', '\\\\') + '</style>""")\n    return\n\n\n')
for f in sorted(Path("apps").glob("*.py")):
    s = f.read_text()
    if 'css_file="uw.css"' not in s:
        continue
    s = re.sub(r'@app\.cell\(hide_code=True\)\ndef _uw_style\(mo\):.*?    return\n\n\n', '', s, flags=re.S)
    i = s.index('@app.cell', s.index('import marimo as mo'))          # after the import cell
    f.write_text(s[:i] + cell + s[i:])
    print("styled", f)
