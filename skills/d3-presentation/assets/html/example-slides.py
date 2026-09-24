# -*- coding: utf-8 -*-
"""D3 HTML deck: every slide type and every kit component once. Sections 1 to 4 are the twin of
assets/latex/example-presentation.tex; section 5 shows the designed objects of the component kit
(references/html-components.md).

Build from the skill folder:  uv run assets/html/example-slides.py  ->  assets/html/dist/example.html
Verify:                       uv run --with playwright --with pillow assets/html/d3deck/shoot.py assets/html/dist/example.html --contact --slot 20
"""
from d3deck import *

meta(title='Data-driven decisions raise forecast accuracy by 38 percent',
     subtitle='A worked example of every D3 slide type',
     presenter='Author Name',
     chair='Chair of Information Systems and Business Analytics',
     sections=['Basic slides', 'Code boxes', 'Chevrons and timelines', 'Figures and numbers', 'Designed objects'],
     tracker=True, numbering='content', feel='rich',
     macros={'E': r'\mathbb{E}', 'yhat': r'\hat{y}_{#1}'})      # the paper's macros, for the math slides

# ── TITLE ───────────────────────────────────────────────────────────────
# No agenda slide: the tracker on every slide and the question dividers (with their list of the part's slides)
# carry the structure. (agenda() still exists for look='beamer'.)
titleslide(time='0:15')

statement('A forecast is only worth the <b>decision</b> it changes.', src='Statement slide: one sentence, one orange word',
          time='0:20')

# ── SECTION 1: BASIC SLIDES ─────────────────────────────────────────────
section(1, question='What does a calm slide look like?', time='0:05')

onecol(K('Layout', 'One-column slides carry one message, with at most one build'), middle(
       '<div class="grid3">' +
       tile('A complete sentence', ['the titles alone read as the argument'], kick='Title', ico='quote') +
       tile('Parallel and short', ['keywords on the slide, sentences in the notes'], kick='Body', ico='listcheck') +
       tile('One orange element', ['the step that reveals it is the point'], kick='Point', ico='target', color='orange', s=1) +
       '</div>'), steps=2, time='0:45',
       notes='0: two rules of every slide. 1: the point of the slide arrives as the one build.',
       src='Rules for one-column slides')

twocol(K('Layout', 'Two columns compare two things side by side'),
       middle(tile('Errors cluster in the last quarter', ['manual overrides grow with team size'], kick='Observation', ico='search', color='gray')),
       middle(tile('Seasonality needs its own model term', ['override rights follow accountability'], kick='Implication', ico='bulb', color='teal')),
       time='0:40', src='Observation versus implication')

twocoltakeaway('Takeaway slides end a block with the sentence to remember',
               middle(tile('Three planners, no shared baseline', ['weekly spreadsheets'], kick='Before', ico='file', color='gray')),
               middle(tile('One model, one baseline', ['overrides logged with a reason'], kick='After', ico='database', color='teal')),
               'A shared baseline turns disagreement into a measurable override rate.',
               time='0:40', src='Before and after the intervention')

# ── SECTION 2: CODE BOXES ───────────────────────────────────────────────
section(2, question='How do we show code without a wall of text?', time='0:05')

twocol('Code boxes keep the three states of a program apart',
       middle(columnheader('Standard and error') + codebox('''def forecast(series, horizon=12):
    model = fit(series)
    return model.predict(horizon)''') + errorbox('''TypeError: unsupported operand type(s)
  for +: 'int' and 'str\'''')),
       middle(columnheader('Terminal') + terminalbox('''$ python main.py
Loading 1,622,969 rows
Fitting model ... done (4.2 s)
MAPE: 6.1 %''')), time='0:40', src='Code box variants')

# ── SECTION 3: CHEVRONS AND TIMELINES ───────────────────────────────────
section(3, question='How do we show a process and a plan?', time='0:05')

onecol('Process flows highlight the phase under discussion', middle('''
<p>Three phases, the second one active:</p>''' +
       chevrons(2, [('Phase 1:', 'Collect'), ('Phase 2:', 'Model'), ('Phase 3:', 'Decide')]) + '''
<p style="margin-top:28px">Four phases with single labels:</p>''' +
       chevrons(4, ['Plan', 'Build', 'Test', 'Ship'])), time='0:30', src='Chevron process flows')

onecol('Project timelines show work packages against the calendar', middle(
       timeline(2025, 2028, [
           ('WP1: Research and analysis', 'teal!60', 0, 0.5, 1, 'M1'),
           ('WP2: Development', 'yellow!80', 0.17, 0.67, 2, 'M2'),
           ('WP3: Testing', 'peach!80', 0.33, 0.83, 3, 'M3'),
           ('WP4: Deployment', 'lavender!80', 0.67, 1.0, 4, 'M4'),
       ]) + '''
<p style="margin-top:20px"><b>Milestones:</b> M1 research complete, M2 development complete,
M3 testing complete, M4 project delivered.</p>'''), time='0:40', src='Gantt timeline with milestones')

# ── SECTION 4: FIGURES AND NUMBERS ──────────────────────────────────────
section(4, question='Which numbers does the audience take home?', time='0:05')

twocol('Embedded figures keep their aspect ratio',
       fig('example', width='100%'),
       columnheader('Reading the chart') + '''
<ul>
 <li>Bars are yearly forecast accuracy</li>
 <li>The container matches the figure ratio, so annotations stay anchored</li>
 <li data-s="1">2024 carries the intervention and the one orange bar</li>
</ul>''', steps=2, time='0:40', src='Figure with one build: the reading of the chart')

# Math: LaTeX as in the paper, in raw strings (r'...'). MathJax is embedded because this slide exists.
twocoltakeaway(K('Model', 'The forecast is a weighted average of the last value and the last forecast'),
               columnheader('Update rule') + r'''
<p>Each period blends the newest observation into the forecast:</p>
\[ \yhat{t+1} = \alpha\, y_t + (1 - \alpha)\, \yhat{t} \]
<p data-s="1">The weight is chosen to minimise the expected squared error:</p>
<div data-s="1">\[ \alpha^\star = \arg\min_{\alpha \in [0,1]} \; \E\big[ (y_{t+1} - \yhat{t+1})^2 \big] \]</div>''',
               columnheader('Reading the formula') + '<div style="display:flex;gap:26px;margin-top:26px">' +
               brace(r'$\alpha\, y_t$', 'newest value', 'orange') + brace(r'$(1 - \alpha)\, \yhat{t}$', 'last forecast') +
               '</div>' + r'<p style="margin-top:28px">$\alpha \to 1$ follows the last value, $\alpha \to 0$ ignores it.</p>',
               r'One parameter, $\alpha$, carries the whole model', steps=2, time='0:50',
               src='Math slide: inline and display formulas, macros from meta(), braced terms, one build')

onecol('Stat cards reveal a grid one cell at a time with a scrim', '''
<div class="grid2" style="height:100%;position:relative">
''' + stat('1.6M', 'team matches analysed') + stat('14,000', 'focal players', accent=True) +
       stat('25', 'matches per player as the threshold') + stat('0.61', 'AUC on the held-out split') + '''
</div>''' + scrim(1, '50%', 0, 0, '50%') + scrim(2, 0, '50%', '50%', 0) + scrim(3, '50%', '50%', 0, 0),
       steps=4, time='0:45', src='Grid revealed by scrims')

facts(K('Result', 'Three numbers summarise the study'),
      [('38 %', 'higher forecast accuracy after twelve months', True), ('1.6M', 'team matches analysed'), ('0.61', 'AUC on the held-out split')],
      takeaway='The gain holds on the held-out split.', time='0:30', src='Facts slide: at most four numbers, one accented')

slide(K('Result', 'One number can carry a slide'), '''
<div class="body" style="display:flex;align-items:center;justify-content:center;text-align:center">
 <div>''' + bignum('38 %', 'higher forecast accuracy after twelve months') + '''</div>
</div>''', time='0:20', src='Big number')

# ── SECTION 5: DESIGNED OBJECTS ─────────────────────────────────────────
# Each slide centres on one object from the kit. The numbers are illustrative unless a provenance line says otherwise.
section(5, question='What carries a slide when bullets do not?', time='0:05')

# Hook: an interface rebuilt in HTML that replays on arrival, and a gauge whose gap is the point.
twocol(K('Case', 'The forecast says 54; the match day needs 80'),
       middle(chat('How many salads should we stock for Saturday?',
                   '<p>Based on the last four Saturdays, stock <b>' + flag('54 salads') + '</b>.</p>'
                   '<p>Weekday, weather and promotions are in line with those weeks.</p>',
                   title='Forecast assistant · study stimulus')),
       middle(gauge(30, 90, [(54, '54 · forecast', 'navy'), (80, '80 · demand', 'orange')], zone=(54, 80, 'orange')) +
              '<div style="height:36px"></div>' +
              tile('A home match nearby', ['the event is missing from every input of the model'],
                   kick='What only the planner knows', ico='mappin', color='orange', s=1)),
       steps=2, time='1:00', provenance='Illustrative numbers',
       notes='0: the answer replays as the participants saw it; the gauge shows the gap. 1: why the gap exists.',
       src='Hook: chat replica with replay, gauge with a zone')

# A model built one relation per step; arrows computed by model(), keys light related parts on hover.
onecol(K('Model', 'Explanations can raise or lower reliance'),
       model([node('form', 'Explanation form', col=0, y=150, w=220, h=72, sub='what the designer controls'),
              node('verify', 'Lower cost of verifying', col=1, y=62, w=220, h=72, color='teal',
                   sub=cite('Author 2024', 'Author, A. (2024). Title of the paper. Venue.', 'Study 2')),
              node('illusion', 'Illusion of understanding', col=1, y=238, w=220, h=72, color='orange', s=2,
                   sub=cite('Author 2025', 'Author, B. (2025). Title of the paper. Venue.')),
              node('rely', 'Appropriate reliance', col=2, y=150, w=220, h=72),
              node('decide', 'Decision quality', col=3, y=150, w=220, h=72, color='solid')],
             [edge('form', 'verify', 'pos', s=1, k='H1'),
              edge('verify', 'rely', 'pos', tag='H1', s=1, k='H1'),
              edge('form', 'illusion', 'pos', s=2, k='H2'),
              edge('illusion', 'rely', 'neg', tag='H2', s=2, k='H2'),
              edge('rely', 'decide', 'pos')],
             lanes=[('Design', 'explanation'), ('Mechanism', 'two findings'), ('Behaviour', 'reliance'), ('Outcome', 'what we measure')]),
       steps=3, time='1:30',
       notes='0: the chain from reliance to decision quality. 1: H1, the path that helps. 2: H2, the path that hurts. '
             'Hover H1 or H2 in Q&A to light its path; the citations open on click.',
       src='Model figure: lanes, signed edges drawn per step, tags, citations, hover keys')

# Bars on one scale, each growing out of the previous one.
onecol(K('Sample size', 'Halving the lift quadruples the sample'),
       middle(bars(
           bar('+20 % lift', 7456),
           bar('+10 % lift', 29826, grow_from=7456),
           bar('+5 % lift', 119303, 'orange', grow_from=29826, sub='our case', s=1),
           bar('+2.5 % lift', 477212, grow_from=119303, s=2),
           unit=' per arm', label_w=180, height=38, gap=26, value_w=200)),
       steps=3, time='0:50', provenance='Two-sided test · ' + nocaps('α') + ' = .05 · power .80 · baseline 5 %',
       notes='0: two lifts. 1: our case grows out of the bar above it. 2: the next halving, four times again.',
       src='Bars growing out of each other on one scale')

# A derivation as a proof rail, with braced terms naming the parts of the result.
onecol(K('Derivation', 'The rule of 16 follows from the power formula'),
       middle(proof(line(r'$n = 2\,(z_{1-\alpha/2} + z_{1-\beta})^2\;\sigma^2/\delta^2$', 'per arm, two-sided'),
             line(r'$2\,(1.96 + 0.84)^2 = 15.7 \approx 16$', r'$\alpha = .05$, power .80'),
             line(r'$n \approx 16\;\sigma^2/\delta^2$', 'the rule of 16', 'key', s=1)) +
       '<div style="display:flex;gap:40px;margin:26px 0 0 54px" data-s="2">' +
       brace('16', 'z-values', 'gray') + brace(r'$\sigma^2$', 'noise', 'teal') + brace(r'$1/\delta^2$', 'lift', 'orange') +
       '</div>'), steps=3, time='0:50',
       notes='0: the formula and the numbers. 1: the rule. 2: what each term contributes.',
       src='Proof rail and braced identity')

# Effect sizes: the row that did not come out as hoped gets its own step.
onecol(K('Results', 'Two of three hypotheses hold; the third is underpowered'), middle('''
<table class="k-table">
 <thead><tr><th></th><th>What it tests</th><th>Effect size r</th><th>Read</th></tr></thead>
 <tbody>
  <tr><td>''' + badge('H1', pop='H1: Explanations lower the cost of verifying a forecast.') + '''</td><td>Lower cost of verifying</td>
      <td>''' + effect(.41) + '</td><td>' + chip('supported', sign='ok') + '''</td></tr>
  <tr><td>''' + badge('H2', pop='H2: Explanations create an illusion of understanding.') + '''</td><td>Illusion of understanding</td>
      <td>''' + effect(-.28, 'neg') + '</td><td>' + chip('supported', sign='ok') + '''</td></tr>
  <tr data-s="1"><td>''' + badge('H3', color='gray', pop='H3: The effect is larger for novices.') + '''</td><td>Larger for novices</td>
      <td>''' + effect(.09, 'weak') + '</td><td>' + chip('underpowered', sign='nil') + '''</td></tr>
 </tbody>
</table>'''), steps=2, time='0:50', provenance='Illustrative effect sizes',
       notes='0: two supported hypotheses. 1: the honest row. Badges open the full hypothesis on click.',
       src='Results table with effect-size bars, badges with popovers, honest row on its own step')

# Comparison: two things row by row, one column per step.
onecol(K('Comparison', 'A point forecast hides what an interval shows'),
       middle(versus('Point forecast', 'Interval forecast',
              [('54 salads', 'Output', '40 to 80 salads'),
               ('none', 'Uncertainty', 'shown as a range'),
               ('stock 54', 'Decision', 'stock for the cost-balancing quantile')],
              left_ico='target', right_ico='sliders', left_color='gray', right_color='teal', rstep=1)),
       steps=2, time='0:40', src='Mirror comparison, right column on the second step')

# Positioning: every option visible, the chosen one lit.
twocol(K('Positioning', 'The study explains and predicts'),
       middle(selector(['I · Analysis', 'II · Explanation', 'III · Prediction', 'IV · Explanation and prediction',
                        'V · Design and action'], 3)),
       middle(tile('Why type IV', ['a causal account of reliance', 'testable predictions for each design'],
                   kick='Theory type', ico='layers') +
              '<p style="margin-top:18px;font-size:17px">Classification after ' +
              cite('Gregor 2006', 'Gregor, S. (2006). The nature of theory in information systems. MIS Quarterly, 30(3), 611-642.') + '.</p>'),
       time='0:30', src='Selector with a citation')

# Counts as units, and the sentence the room should keep.
onecol(K('Adoption', '38 of 50 stores kept the model after the pilot'),
       middle(units([(38, 'teal', 'kept the model'), (9, 'gray', 'returned to spreadsheets'), (3, 'orange', 'still deciding')], size=28) +
              '<div style="height:48px"></div>' + callout('Adoption held where planners could <b>override with a reason</b>.')),
       time='0:40', provenance='Illustrative numbers', src='Unit chart and callout band')

# An instrument: the argument is a parameter the audience watches move. Presets are the rehearsed values.
onecol(K('Instrument', 'The interval narrows with the square root of the sample'),
       lab('<svg id="curve" viewBox="0 0 700 300" style="width:100%;height:300px"><path id="curve-fill" fill="rgba(77,154,170,.18)"/>'
           '<path id="curve-line" fill="none" stroke="#2F7A89" stroke-width="2.5"/><line x1="0" y1="270" x2="700" y2="270" stroke="#DCE2ED"/>'
           '<line x1="350" y1="20" x2="350" y2="270" stroke="#153F87" stroke-dasharray="4 4"/></svg>',
           slider('n', 'Visitors per arm', 500, 20000, 2000, step=500, presets=(500, 2000, 8000),
                  note='Each preset quadruples the sample; watch the width halve.') +
           readout(('Half-width', 'hw', ''), ('Detectable lift', 'mde', '')),
           cap='Sampling distribution of the difference in conversion, baseline 5 %'),
       time='1:00', notes='Click the presets 500, 2000, 8000: the half-width halves each time.',
       src='Live instrument: slider, presets, readout, a live module')
js(r'''
D3Deck.live('#curve', {
  setup(el) { this.draw(el); document.getElementById('n').addEventListener('input', () => this.draw(el)); },
  draw(el) {
    const n = document.getElementById('n').valueAsNumber, p = 0.05;
    const se = Math.sqrt(2 * p * (1 - p) / n) * 100;          // standard error of the difference, percentage points
    const k = 350 / 1.2, pts = [];                             // 1.2 pp to each side of the centre
    for (let i = 0; i <= 140; i++) {
      const x = -1.2 + 2.4 * i / 140, y = Math.exp(-0.5 * (x / se) ** 2);
      pts.push([(350 + x * k).toFixed(1), (270 - y * 240).toFixed(1)]);
    }
    const d = 'M' + pts.map(q => q.join(' ')).join(' L');
    el.querySelector('#curve-line').setAttribute('d', d);
    el.querySelector('#curve-fill').setAttribute('d', d + ' L700 270 L0 270 Z');
    D3Deck.set('hw', '±' + (1.96 * se).toFixed(2) + ' pp');
    D3Deck.set('mde', '+' + (2.8 * se / 5 * 100).toFixed(0) + ' %');
  }
});''')

# A plan to scale, with today's position and a countdown.
onecol(K('Plan', 'The field study starts before the winter break'),
       middle(milestones('2026-09-01', '2027-03-31',
                  [('2026-09-24', 'This talk', 'feedback', 'done'), ('2026-10-22', 'Pilot', '40 planners'),
                   ('2026-11-30', 'Field study', 'three stores', 'key'), ('2027-02-15', 'Analysis', ''),
                   ('2027-03-31', 'Submission', 'journal')], today='2026-09-24') +
              '<div style="margin:40px 0 0 70px">' + countdown('2026-11-30', 'to the field study', today='2026-09-24') + '</div>'),
       time='0:40', src='To-scale timeline with a today dot and a countdown')

thankyou(time='0:10')

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
<table class="k-table" style="width:auto">
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
