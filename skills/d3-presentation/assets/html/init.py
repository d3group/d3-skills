#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scaffold a D3 HTML talk folder.

    uv run <skill-dir>/assets/html/init.py my_talk              # creates ./my_talk
    uv run <skill-dir>/assets/html/init.py my_talk --dest ~/x   # creates ~/x/my_talk

The folder gets slides.py (a starter deck), figures/ and d3deck/ with the fonts
(Inclusive Sans UW, D3 Symbols) and the logos inside, so `uv run slides.py` builds anywhere and the talk
needs nothing from the skill afterwards.
"""
import argparse
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))        # assets/html
ASSETS = os.path.dirname(HERE)                           # assets
LOGOS = ('DataDrivenDecisions_2c.svg', 'uw-logo-navy.svg', 'uw-logo-white.svg',
         'uw-seal-blue.svg', 'uw-seal-coral.svg', 'uw-seal-faint.svg', 'uw-cover.jpg')   # coral seal: look='uni'

STARTER = '''# -*- coding: utf-8 -*-
"""__NAME__: D3 HTML deck.  Build: uv run slides.py  ->  dist/__NAME__.html
Verify: uv run --with playwright --with pillow d3deck/shoot.py dist/__NAME__.html --contact --slot <minutes>
See the skill's references/html-workflow.md for the slide API and html-components.md for the designed objects."""
from d3deck import *

meta(title='Action title that states the main message',
     subtitle='Optional subtitle',
     presenter='Author Name',
     chair='Chair of Information Systems and Business Analytics',
     sections=['Introduction', 'Methodology', 'Results', 'Conclusion'],
     numbering='content',    # structural slides carry no number, backup restarts ('all': count every slide)
     look='klar',            # D3 look on the university master: D3 logo top right, tracker, kicker titles
                             # ('beamer': the LaTeX theme's conventions; 'uni': no D3 branding, for teaching)
     feel='calm')            # motion budget agreed with the presenter: 'calm', 'rich' or 'interactive'

titleslide(time='0:15')

section(1, question='Which question does this part answer?', time='0:05')
# Every content slide centres on a designed object (references/html-components.md); sentences go into the notes.
onecol(K('Problem', 'The title is one claim in at most 15 words'), middle(
       '<div class="grid2">' +
       tile('Point one', ['a keyword line, always visible'], kick='First', ico='target') +
       tile('Point two', ['revealed on the second step'], kick='Second', ico='bulb', color='teal', s=1) +
       '</div>'), steps=2, time='0:45', notes='0: point one. 1: point two.', src='Introduction: the problem in one line')

thankyou(time='0:10')
build('__NAME__')
'''


def scaffold(name, dest='.'):
    if not re.fullmatch(r'[a-z0-9]+(_[a-z0-9]+)*', name):
        raise SystemExit(f'{name!r}: use lowercase words joined by _, for example ai_healthcare')
    target = os.path.join(os.path.abspath(dest), name)
    if os.path.exists(target):
        raise SystemExit(f'{target} exists; choose another name or remove it first')
    os.makedirs(os.path.join(target, 'figures'))
    shutil.copytree(os.path.join(HERE, 'd3deck'), os.path.join(target, 'd3deck'),
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'tests'))
    shutil.copytree(os.path.join(ASSETS, 'fonts'), os.path.join(target, 'd3deck', 'fonts'))
    os.makedirs(os.path.join(target, 'd3deck', 'logos'))
    for f in LOGOS:
        shutil.copy(os.path.join(ASSETS, 'logos', f), os.path.join(target, 'd3deck', 'logos', f))
    with open(os.path.join(target, 'slides.py'), 'w', encoding='utf-8') as fh:
        fh.write(STARTER.replace('__NAME__', name))
    with open(os.path.join(target, 'figures', '.gitkeep'), 'w') as fh:
        fh.write('')
    return target


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('name', help='talk folder name: lowercase words joined by _')
    ap.add_argument('--dest', default='.', help='parent directory (default: current)')
    a = ap.parse_args(argv)
    t = scaffold(a.name, a.dest)
    print(f'created {t}\n  next: cd {t} && uv run slides.py && open dist/{a.name}.html')


if __name__ == '__main__':
    main()
