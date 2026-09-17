# -*- coding: utf-8 -*-
"""D3 HTML deck: every slide type once. The twin of assets/latex/example-presentation.tex.

Build from the skill folder:  uv run assets/html/example-slides.py  ->  assets/html/dist/example.html
Verify:                       uv run --with playwright --with pillow assets/html/d3deck/shoot.py assets/html/dist/example.html --contact
"""
from d3deck import *

meta(title='Data-driven decisions raise forecast accuracy by 38 percent',
     subtitle='A worked example of every D3 slide type',
     presenter='Author Name',
     chair='Chair of Information Systems and Business Analytics',
     sections=['Basic slides', 'Code boxes', 'Chevrons and timelines', 'Figures and numbers'],
     tracker=True, numbering='content')

# ── TITLE AND AGENDA ────────────────────────────────────────────────────
titleslide()
agenda()

# ── SECTION 1: BASIC SLIDES ─────────────────────────────────────────────
section(1)

onecol('One-column slides carry one message, with at most one build', '''
<ul>
 <li>Every slide title is a complete sentence that states the message</li>
 <li>Bullets stay grammatically parallel and short</li>
 <li>Later steps stay hidden and keep their place, so nothing on the slide moves</li>
 <li data-s="1">''' + highlight('The one orange element is the point of the slide') + '''</li>
</ul>''', steps=2, notes='Three rules at once, then the point of the slide as the one build.',
       src='Rules for one-column slides')

twocol('Two columns compare two things side by side',
       columnheader('Observation') + '''
<ul>
 <li>Forecast errors cluster in the last quarter</li>
 <li>Manual overrides grow with team size</li>
</ul>''',
       columnheader('Implication') + '''
<ul>
 <li>Seasonality needs its own model term</li>
 <li>Override rights should follow accountability</li>
</ul>''', src='Observation versus implication')

twocoltakeaway('Takeaway slides end a block with the sentence to remember',
               columnheader('Before') + '<p>Weekly spreadsheets, three planners, no shared baseline.</p>',
               columnheader('After') + '<p>One model, one baseline, overrides logged with a reason.</p>',
               'A shared baseline turns disagreement into a measurable override rate.',
               src='Before and after the intervention')

# ── SECTION 2: CODE BOXES ───────────────────────────────────────────────
section(2)

twocol('Code boxes keep the three states of a program apart',
       columnheader('Standard and error') + codebox('''def forecast(series, horizon=12):
    model = fit(series)
    return model.predict(horizon)''') + errorbox('''TypeError: unsupported operand type(s)
  for +: 'int' and 'str\''''),
       columnheader('Terminal') + terminalbox('''$ python main.py
Loading 1,622,969 rows
Fitting model ... done (4.2 s)
MAPE: 6.1 %'''), src='Code box variants')

# ── SECTION 3: CHEVRONS AND TIMELINES ───────────────────────────────────
section(3)

onecol('Process flows highlight the phase under discussion', '''
<p>Three phases, the second one active:</p>''' +
       chevrons(2, [('Phase 1:', 'Collect'), ('Phase 2:', 'Model'), ('Phase 3:', 'Decide')]) + '''
<p style="margin-top:28px">Four phases with single labels:</p>''' +
       chevrons(4, ['Plan', 'Build', 'Test', 'Ship']), src='Chevron process flows')

onecol('Project timelines show work packages against the calendar',
       timeline(2025, 2028, [
           ('WP1: Research and analysis', 'teal!60', 0, 0.5, 1, 'M1'),
           ('WP2: Development', 'yellow!80', 0.17, 0.67, 2, 'M2'),
           ('WP3: Testing', 'peach!80', 0.33, 0.83, 3, 'M3'),
           ('WP4: Deployment', 'lavender!80', 0.67, 1.0, 4, 'M4'),
       ]) + '''
<p style="margin-top:20px"><b>Milestones:</b> M1 research complete, M2 development complete,
M3 testing complete, M4 project delivered.</p>''', src='Gantt timeline with milestones')

# ── SECTION 4: FIGURES AND NUMBERS ──────────────────────────────────────
section(4)

twocol('Embedded figures keep their aspect ratio',
       fig('example', width='100%'),
       columnheader('Reading the chart') + '''
<ul>
 <li>Bars are yearly forecast accuracy</li>
 <li>The container matches the figure ratio, so annotations stay anchored</li>
 <li data-s="1">2024 carries the intervention and the one orange bar</li>
</ul>''', steps=2, src='Figure with one build: the reading of the chart')

onecol('Stat cards reveal a grid one cell at a time with a scrim', '''
<div class="grid2" style="height:100%;position:relative">
''' + stat('1.6M', 'team matches analysed') + stat('14,000', 'focal players', accent=True) +
       stat('25', 'matches per player as the threshold') + stat('0.61', 'AUC on the held-out split') + '''
</div>''' + scrim(1, '50%', 0, 0, '50%') + scrim(2, 0, '50%', '50%', 0) + scrim(3, '50%', '50%', 0, 0),
       steps=4, src='Grid revealed by scrims')

slide('One number can carry a slide', '''
<div class="body" style="display:flex;align-items:center;justify-content:center;text-align:center">
 <div>''' + bignum('38 %', 'higher forecast accuracy after twelve months') + '''</div>
</div>''', src='Big number')

thankyou()

# ── BACKUP ──────────────────────────────────────────────────────────────
appendix()
backuphome()

mark('method')
onecol('Backup: the estimation follows four steps', crumb(('Method', None)) + '''
<ol>
 <li>Predict the outcome on the estimation split</li>
 <li>Compute the residual per team</li>
 <li>Aggregate residuals per player</li>
 <li>Validate on the disjoint split</li>
</ol>
<p style="margin-top:20px">''' + link('robust', 'Robustness checks') + '</p>', group='Method')

mark('robust')
onecol('Backup: results hold across thresholds', crumb(('Method', 'method'), ('Robustness', None)) + '''
<table>
 <tr><th>Threshold</th><th>Coefficient</th><th>n</th></tr>
 <tr><td>10</td><td>0.041</td><td>21,300</td></tr>
 <tr><td>25</td><td>0.044</td><td>14,000</td></tr>
 <tr><td>50</td><td>0.046</td><td>7,900</td></tr>
</table>''', group='Method')

onecol('Backup: literature the talk builds on', crumb(('Literature', None)) + '''
<ul>
 <li>Weidmann and Deming (2021) measure team player effects in the lab with about 250 participants</li>
 <li>Ching, Forti and Rawley (2021) show that team familiarity complements coordination in observational data</li>
 <li>This talk adds field data at scale and variation in team size</li>
</ul>''', group='Literature')

build('example')
