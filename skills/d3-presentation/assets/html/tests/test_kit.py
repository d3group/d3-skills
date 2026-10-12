import os, re, sys, tempfile, unittest, warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import deck as B
from d3deck import kit as K

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None


def nums(s):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', s)]


class Model(unittest.TestCase):
    def setUp(self):
        B.meta(title='T', sections=['A'])

    def test_region_size_follows_the_look(self):
        html = K.model([K.node('a', 'A', x=0, y=0)], [])
        self.assertIn('width:1108px;height:400px', html)
        B.meta(title='T', look='beamer')
        self.assertIn('width:1133px;height:432px', K.model([K.node('a', 'A', x=0, y=0)], []))
        self.assertIn('width:547px;height:432px', K.model([K.node('a', 'A', x=0, y=0)], [], box='col'))
        self.assertIn('width:300px;height:200px', K.model([K.node('a', 'A', x=0, y=0, w=100)], [], box=(300, 200)))
        B.meta(title='T', look='uni')
        self.assertIn('width:1137px;height:420px', K.model([K.node('a', 'A', x=0, y=0)], []))

    def test_arrow_tip_touches_the_target_border(self):
        html = K.model([K.node('a', 'A', x=0, y=100, w=200, h=60), K.node('b', 'B', x=500, y=100, w=200, h=60)],
                       [K.edge('a', 'b', 'pos')])
        head = re.search(r'class="k-eh" d="M([\d.]+) ([\d.]+)', html)
        self.assertEqual((float(head.group(1)), float(head.group(2))), (500.0, 130.0))   # left border of b, mid height
        shaft = re.search(r'class="k-ep" pathLength="1" d="M([\d.]+) ([\d.]+) C.* ([\d.]+) ([\d.]+)"', html)
        self.assertEqual((float(shaft.group(1)), float(shaft.group(2))), (200.0, 130.0))  # leaves the right border of a
        self.assertEqual(float(shaft.group(3)), 500.0 - K.HEAD_L)                        # and stops where the head begins

    def test_vertical_edges_use_top_and_bottom(self):
        html = K.model([K.node('a', 'A', x=100, y=0), K.node('b', 'B', x=100, y=250)], [K.edge('a', 'b')])
        head = re.search(r'class="k-eh" d="M([\d.]+) ([\d.]+)', html)
        self.assertEqual(float(head.group(2)), 250.0)

    def test_edges_on_one_side_spread_without_crossing(self):
        html = K.model([K.node('a', 'A', x=0, y=150, h=80), K.node('hi', 'H', x=500, y=0), K.node('lo', 'L', x=500, y=300)],
                       [K.edge('a', 'lo'), K.edge('a', 'hi')])
        starts = [nums(m)[:2] for m in re.findall(r'class="k-ep" pathLength="1" d="(M[\d. ]+)', html)]
        ys = {round(y) for x, y in starts}
        self.assertEqual(len(ys), 2)                                   # two anchors on a's right side
        by_target = dict(zip(['lo', 'hi'], [y for x, y in starts]))
        self.assertLess(by_target['hi'], by_target['lo'])              # the upper edge leaves higher

    def test_lanes_centre_nodes(self):
        html = K.model([K.node('a', 'A', col=0, y=60, w=200), K.node('b', 'B', col=3, y=60, w=200)], [], lanes=['1', '2', '3', '4'])
        lefts = [float(x) for x in re.findall(r'k-node[^>]*left:([\d.]+)px', html)]
        lane_w = (1108 - 3 * 40) / 4
        self.assertAlmostEqual(lefts[0], (lane_w - 200) / 2, places=1)
        self.assertAlmostEqual(lefts[1] + 200, 1108 - (lane_w - 200) / 2, places=1)

    def test_guards(self):
        with self.assertRaises(ValueError):
            K.model([K.node('a', 'A', x=1000, y=0, w=200)], [])        # leaves the region
        with self.assertRaises(ValueError):
            K.model([K.node('a', 'A', x=0)], [K.edge('a', 'zz')])      # unknown node
        with self.assertRaises(ValueError):
            K.model([K.node('a', 'A', col=1, y=0)], [])                # col without lanes
        with self.assertRaises(ValueError):
            K.edge('a', 'b', 'plus')
        with self.assertRaises(ValueError):
            K.node('a', 'A')                                           # neither x nor col

    def test_moderator_points_at_the_middle_of_a_relation(self):
        html = K.model([K.node('a', 'A', x=0, y=200, w=200, h=60), K.node('b', 'B', x=600, y=200, w=200, h=60),
                        K.node('m', 'M', x=300, y=0, w=200, h=60)],
                       [K.edge('a', 'b', 'pos'), K.edge('m', ('a', 'b'), 'mod')])
        heads = re.findall(r'class="k-eh" d="M([\d.]+) ([\d.]+)', html)
        self.assertEqual(len(heads), 2)
        mx, my = float(heads[1][0]), float(heads[1][1])
        self.assertAlmostEqual(mx, 400 - K.HEAD_L / 2, delta=6)        # the straight a-b edge's midpoint, shaft shortened by the head
        self.assertAlmostEqual(my, 230 - 3, delta=0.5)                # from above, stopping 3 px short of the line
        with self.assertRaises(ValueError):
            K.model([K.node('a', 'A', x=0, y=0), K.node('b', 'B', x=500, y=0)], [K.edge('a', ('a', 'b'))])

    def test_steps_legend_tags_and_keys(self):
        html = K.model([K.node('a', 'A', x=0, y=0), K.node('b', 'B', x=500, y=0, s=1)],
                       [K.edge('a', 'b', 'neg', tag='H2', s=1, k='H2'), K.edge('b', 'a', 'mod')])
        self.assertIn('class="k-e neg draw" data-s="1" data-k="H2"', html)
        self.assertIn('class="k-etag neg" data-s="1" data-k="H2"', html)
        self.assertIn('>negative<', html)
        self.assertIn('>moderates<', html)
        self.assertNotIn('pathLength="1" d="M500', html)               # the dashed edge keeps px dashes


class Helpers(unittest.TestCase):
    def test_icons(self):
        self.assertIn('<svg class="ico"', K.icon('check'))
        self.assertIn('width:28px', K.icon('alert', size=28))
        with self.assertRaises(ValueError):
            K.icon('smiley')

    def test_bars_share_one_scale(self):
        html = K.bars(K.bar('a', 50), K.bar('b', 100, 'orange', grow_from=50), K.bar('c', 25, text='25 k'))
        self.assertEqual(re.findall(r'width:([\d.]+)%', html), ['50.00', '100.00', '25.00'])
        self.assertIn('--s0:0.5000', html)
        self.assertIn('>25 k<', html)
        self.assertIn('>1,000<', K.bars(K.bar('a', 1000)))
        with self.assertRaises(ValueError):
            K.bars(K.bar('a', 120), scale=100)
        with self.assertRaises(ValueError):
            K.bar('a', 1, 'purple')

    def test_gauge_and_effect(self):
        html = K.gauge(140, 180, [(150, '150 AI', 'red'), (165, '165 USDA', 'teal')], zone=(140, 165))
        self.assertIn('left:25.00%', html)
        self.assertIn('left:62.50%', html)
        with self.assertRaises(ValueError):
            K.gauge(0, 10, [(12, 'x', 'navy')])
        self.assertIn('width:72.0%', K.effect(.72))
        self.assertIn('width:31.0%', K.effect(-.31, 'neg'))

    def test_pop_and_cite_escape(self):
        html = K.cite('Doe 2024', 'Doe, J. (2024). "Title" & more.', 'p. 7')
        # attribute-escaped once: the popover's innerHTML gets <b>Doe, J. (2024). "Title" &amp; more.</b>
        self.assertIn('data-pop="&lt;b&gt;Doe, J. (2024). &quot;Title&quot; &amp;amp; more.&lt;/b&gt;&lt;span class=&quot;k-where&quot;&gt;p. 7', html)
        self.assertIn('<button class="k-pop x" data-pop="a &quot;b&quot;">P1</button>', K.pop('P1', 'a "b"', cls='x'))

    def test_milestones_to_scale(self):
        html = K.milestones('2026-01-01', '2026-01-11', [('2026-01-01', 'Start', '', 'done'), ('2026-01-06', 'Mid', 'x', 'key')],
                            today='2026-01-03')
        self.assertIn('class="k-mi done" style="left:0.00%"', html)
        self.assertIn('class="k-mi key" style="left:50.00%"', html)
        self.assertIn('k-mfill" style="width:20.00%"', html)
        with self.assertRaises(ValueError):
            K.milestones('2026-01-01', '2026-01-11', [('2026-02-01', 'late')])
        self.assertIn('<b>3</b>', K.countdown('2026-01-06', today='2026-01-03'))

    def test_proof_selector_versus_units(self):
        html = K.proof(K.line('$a=b$', 'definition'), K.line('$b=c$', 'wrong step', 'wrong', s=1))
        self.assertIn('class="k-prow wrong" data-s="1"', html)
        self.assertIn('<span class="k-pn">1</span>', html)
        with self.assertRaises(ValueError):
            K.line('x', kind='maybe')
        self.assertIn('--sel:2', K.selector(['a', 'b', 'c'], 2))
        with self.assertRaises(ValueError):
            K.selector(['a'], 3)
        vs = K.versus('A', 'B', [('l', 'mid', 'r')], lstep=1, rstep=2)
        self.assertIn('<div class="l" data-s="1">l</div>', vs)
        self.assertIn('<div class="r" data-s="2">r</div>', vs)
        self.assertEqual(K.units([(3, 'teal', 'yes'), (2, 'gray', 'no')]).count('<i class="teal" style'), 3)

    def test_slider_and_readout(self):
        html = K.slider('n', 'Sample size', 10, 1000, 40, presets=(40, 160))
        self.assertIn('id="n-val"', html)
        self.assertIn('data-kit-set="#n=160"', html)
        self.assertIn('id="half"', K.readout(('Half-width', 'half', '0.31')))


class Build(unittest.TestCase):
    def build(self):
        out = os.path.join(tempfile.mkdtemp(), 'd.html')
        B.build('d', out=out, embed_fonts=False)
        with open(out, encoding='utf-8') as fh:
            return fh.read()

    def test_text_only_slide_warns_and_objects_do_not(self):
        B.meta(title='T', sections=['A'])
        B.section(1)
        B.onecol('Words only', '<ul><li>one</li><li>two</li></ul>')
        B.onecol('A tile', K.tile('Big', ['line']))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.build()
        msgs = [str(x.message) for x in w if 'text only' in str(x.message)]
        self.assertEqual(len(msgs), 1)
        self.assertIn('Words only', msgs[0])

    def test_feel_controls_the_build_ratio_warning(self):
        for feel, expect in (('calm', True), ('rich', False)):
            B.meta(title='T', feel=feel)
            for i in range(6):
                B.onecol(f'S{i}', K.tile('x') + '<p data-s="1">y</p>', steps=2)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                self.build()
            self.assertEqual(any('use step builds' in str(x.message) for x in w), expect, feel)
        with self.assertRaises(ValueError):
            B.meta(title='T', feel='wild')

    def test_time_provenance_js_and_kit_assets(self):
        B.meta(title='T', sections=['A'])
        B.section(1)
        B.onecol(B.K('Result', 'The claim'), K.tile('x'), time='1:30', provenance='Table 3 · N = 38')
        B.js('window.KIT_OK = 1;')
        doc = self.build()
        self.assertIn('"tm": 90', doc)
        self.assertIn('<span class="prov">Table 3 · N = 38</span>', doc)
        self.assertIn('window.KIT_OK = 1;', doc)
        self.assertIn('.k-tile{', doc)
        self.assertIn('D3Deck=Object.assign', doc)
        self.assertIn('"t": "The claim"', doc)                     # the manifest carries the claim, not the kicker
        self.assertIn('"kk": "Result"', doc)                       # the kicker stays searchable
        with self.assertRaises(ValueError):
            B.onecol('x', 'y', time='90s')


@unittest.skipUnless(sync_playwright, 'playwright not installed')
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        B.meta(title='T', sections=['A'])
        B.titleslide()
        B.onecol('Live', '<div class="grid2"><div id="box">' + K.tile('x') + '</div><div data-s="1" id="later">' + K.count(7, frm=0) + '</div></div>'
                 + K.pop('P1', '<b>full</b> text') + K.badge('H1', k='h1') + K.badge('again', k='h1')
                 + K.slider('n', 'n', 0, 100, 40, presets=(80,)), steps=2)
        B.onecol('Other', K.tile('y'))
        B.js('''D3Deck.live('#box', {setup(el){el.dataset.log='setup'}, enter(el){el.dataset.log+=',enter'},
                 leave(el){el.dataset.log+=',leave'}, step(el,n){el.dataset.log+=',step'+n}});''')
        out = os.path.join(tempfile.mkdtemp(), 'd.html')
        B.build('d', out=out, embed_fonts=False)
        cls.url = 'file://' + out
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def page(self, suffix=''):
        p = self.browser.new_page(viewport={'width': 1320, 'height': 830})
        p.goto(self.url + suffix)
        p.wait_for_timeout(300)
        return p

    def test_current_and_shown_classes(self):
        p = self.page('#2')
        self.assertEqual(p.evaluate('document.querySelectorAll(".sl.is-current").length'), 1)
        self.assertTrue(p.evaluate('SL[1].classList.contains("is-current")'))
        self.assertFalse(p.evaluate('document.getElementById("later").classList.contains("is-shown")'))
        p.keyboard.press('ArrowRight')
        self.assertTrue(p.evaluate('document.getElementById("later").classList.contains("is-shown")'))
        p.keyboard.press('ArrowRight')
        self.assertFalse(p.evaluate('SL[1].classList.contains("is-current")'))
        p.close()

    def test_live_module_lifecycle(self):
        p = self.page('#1')
        self.assertEqual(p.evaluate('document.getElementById("box").dataset.log'), 'setup')
        p.keyboard.press('ArrowRight')
        p.keyboard.press('ArrowRight')
        p.keyboard.press('ArrowDown')
        self.assertEqual(p.evaluate('document.getElementById("box").dataset.log'), 'setup,enter,step0,step1,leave')
        p.close()

    def test_popover_lighting_presets_and_counter(self):
        p = self.page('#2.2')
        p.click('button.k-pop')
        self.assertEqual(p.evaluate('document.querySelector(".sl.on .k-popover").innerHTML'), '<b>full</b> text')
        p.keyboard.press('Escape')
        self.assertEqual(p.evaluate('document.querySelectorAll(".k-popover").length'), 0)
        p.hover('.k-badge >> nth=0')
        self.assertEqual(p.evaluate('document.querySelectorAll(".sl.on .k-badge.lit").length'), 2)
        self.assertEqual(p.evaluate('document.getElementById("n-val").textContent'), '40')
        p.click('button.k-preset')
        self.assertEqual(p.evaluate('[document.getElementById("n").value, document.getElementById("n-val").textContent]'), ['80', '80'])
        self.assertEqual(p.evaluate('document.querySelector(".k-count").getAnimations().length'), 1)   # it counts on stage
        p.wait_for_timeout(1400)
        self.assertEqual(p.evaluate('getComputedStyle(document.querySelector(".k-count")).getPropertyValue("--v").trim()'), '7')
        p.close()


if __name__ == '__main__':
    unittest.main()
