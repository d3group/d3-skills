import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import components as C


class Mix(unittest.TestCase):
    def test_token(self):
        self.assertEqual(C.mix('navy'), '#153F87')

    def test_percentages_match_xcolor(self):
        self.assertEqual(C.mix('navy!15'), '#DCE2ED')
        self.assertEqual(C.mix('navy!5'), '#F3F5F9')
        self.assertEqual(C.mix('navy!50'), '#8A9FC3')
        self.assertEqual(C.mix('navy!90'), '#2C5293')

    def test_hex_passthrough(self):
        self.assertEqual(C.mix('#ABCDEF'), '#ABCDEF')

    def test_unknown(self):
        with self.assertRaises(ValueError):
            C.mix('mauve!30')


class Fragments(unittest.TestCase):
    def test_columnheader_and_highlight(self):
        self.assertEqual(C.columnheader('Left'), '<div class="colhead">Left</div>')
        self.assertEqual(C.highlight('key'), '<b class="hl">key</b>')

    def test_code_boxes_escape(self):
        self.assertEqual(C.codebox('\nif a < b:\n    pass\n'), '<pre class="code">if a &lt; b:\n    pass</pre>')
        self.assertTrue(C.errorbox('x').startswith('<pre class="code err">'))
        self.assertTrue(C.terminalbox('$ ls').startswith('<pre class="code term">'))

    def test_chevrons(self):
        h = C.chevrons(2, [('Phase 1:', 'Plan'), ('Phase 2:', 'Build'), 'Ship'])
        self.assertEqual(h.count('<div class="ct">'), 3)
        self.assertIn('<div class="c cur"><div class="cl">Phase 2:</div><div class="ct">Build</div></div>', h)
        self.assertIn('<div class="c"><div class="cl"></div><div class="ct">Ship</div></div>', h)

    def test_chevrons_limits(self):
        with self.assertRaises(ValueError):
            C.chevrons(1, ['only'])
        with self.assertRaises(ValueError):
            C.chevrons(1, ['a', 'b', 'c', 'd', 'e', 'f'])
        with self.assertRaises(ValueError):
            C.chevrons(3, ['a', 'b'])

    def test_timeline(self):
        h = C.timeline(2025, 2028, [('WP1', 'teal!60', 0, 0.5, 1, 'M1'), ('WP2', 'yellow!80', 0.25, 1.0, 2, 'M2')])
        self.assertIn('class="tl-year" style="left:33.33%">2026<', h)
        self.assertIn('left:0.00%;width:50.00%;bottom:38px;background:#94C2CC', h)
        self.assertIn('left:25.00%;width:75.00%;bottom:90px', h)
        self.assertIn('<div class="tl-msl"', h)

    def test_timeline_validation(self):
        with self.assertRaises(ValueError):
            C.timeline(2025, 2025, [('a', 'teal', 0, 1, 1, '')])
        with self.assertRaises(ValueError):
            C.timeline(2025, 2026, [('a', 'teal', 0.5, 0.2, 1, '')])

    def test_takeaway_stat_bignum(self):
        self.assertEqual(C.takeaway('Do it'), '<div class="take"><b>Key Takeaway:</b> Do it</div>')
        self.assertIn('class="stat o"', C.stat('42', 'answers', accent=True))
        self.assertIn('<div class="bv">1.6M</div>', C.bignum('1.6M', 'matches'))

    def test_step_and_scrim(self):
        self.assertEqual(C.step(2, 'x'), '<div data-s="2">x</div>')
        self.assertEqual(C.step(1, 'x', soft=True, until=3, tag='li', cls='q'),
                         '<li data-s="1" data-soft="1" data-until="3" class="q">x</li>')
        self.assertEqual(C.scrim(2, '50%', 0, 0, '50%'),
                         '<div class="scrim" data-off="2" style="left:50%;top:0px;right:0px;bottom:50%"></div>')

    def test_crumb(self):
        h = C.crumb(('Ch. 5', 'ch5'), ('Descriptives', None))
        self.assertIn('<span class="cstep" data-jump="@@bhome@@">Backup</span>', h)
        self.assertIn('<span class="cstep" data-jump="@@ch5@@">Ch. 5</span>', h)
        self.assertIn('<span class="cstep cur">Descriptives</span>', h)


if __name__ == '__main__':
    unittest.main()
