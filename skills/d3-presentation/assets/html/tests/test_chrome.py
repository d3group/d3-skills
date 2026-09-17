import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import chrome, paths


class Logos(unittest.TestCase):
    def test_uni_svg_gets_viewbox_and_loses_size(self):
        s = chrome.inline_svg(os.path.join(paths.asset_dir('logos'), chrome.UNI_SVG))
        head = s[:s.index('>') + 1]
        self.assertIn('viewBox="0 0 347.41 151.9375"', head)
        self.assertNotIn(' width="', head)
        self.assertNotIn('<?xml', s)

    def test_d3_svg_loses_text_and_prefixes_classes(self):
        s = chrome.inline_svg(os.path.join(paths.asset_dir('logos'), chrome.D3_SVG))
        self.assertNotIn('<text', s)
        self.assertNotIn('cls-1', s)
        self.assertIn('#f39200', s.lower())

    def test_seal_exists(self):
        self.assertTrue(os.path.exists(chrome.SEAL))
        self.assertTrue(chrome.seal_uri().startswith('data:image/png;base64,'))

    def test_single_quoted_svg_and_scoped_class_prefix(self):
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'x.svg')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write("<svg xmlns='http://www.w3.org/2000/svg' id='a' width='10' height='5'>"
                     "<style>.cls-1{fill:#000}</style><path class='cls-1' d='M0 0h1'/>"
                     "<text>cls-1 in text</text><desc>subclass-2 keeps</desc></svg>")
        s = chrome.inline_svg(p)
        head = s[:s.index('>') + 1]
        self.assertIn('viewBox="0 0 10 5"', head)
        self.assertNotIn(" id=", head)
        self.assertNotIn("width='", head)
        self.assertNotIn('<text', s)
        self.assertNotIn('.cls-1', s)
        self.assertIn('subclass-2 keeps', s)


class Frames(unittest.TestCase):
    def test_content_frame(self):
        h = chrome.content_frame('T', '<div class="body">B</div>', page='3/9', foot='Chair | Me', dots='<i>d</i>')
        for cls in ('fr-uni', 'fr-bar', 'fr-tab', 'fr-d3', 'fr-num', 'fr-foot', 'fr-title'):
            self.assertIn(f'class="{cls}"', h)
        self.assertIn('<div class="fr-num">3/9</div>', h)
        self.assertTrue(h.endswith('<div class="body">B</div><i>d</i>'))

    def test_content_frame_without_page_or_foot(self):
        h = chrome.content_frame('', 'x')
        self.assertNotIn('fr-num', h)
        self.assertNotIn('fr-foot', h)
        self.assertNotIn('fr-title', h)

    def test_title_frame(self):
        h = chrome.title_frame(chrome.title_inner('Big', 'small'))
        for cls in ('fr-uni', 'fr-tbar', 'fr-d3t', 'fr-seal', 'fr-ttitle', 'fr-tsub'):
            self.assertIn(f'class="{cls}"', h)
        self.assertNotIn('fr-bar"', h)

    def test_thankyou_inner(self):
        h = chrome.thankyou_inner('Ada')
        self.assertIn('Thank You!', h)
        self.assertIn('<div class="fr-tname">Ada</div>', h)


class Agenda(unittest.TestCase):
    S = ['Intro', 'Method', 'Results', 'Outlook']

    def test_positions_for_four_items(self):
        h = chrome.agenda_list(self.S)
        self.assertEqual(h.count('<div class="ag"'), 4)
        self.assertIn('top:234.8px', h)   # 360 - 3*32.4 - 28
        self.assertIn('top:299.6px', h)
        self.assertIn('top:429.2px', h)

    def test_current_and_links(self):
        h = chrome.agenda_list(self.S, current=2, links={1: 'sec-1', 2: 'sec-2'})
        self.assertEqual(h.count('class="ag off"'), 3)
        self.assertEqual(h.count('data-jump="@@sec-1@@"'), 2)
        self.assertIn('<div class="agn">3</div>', h)


class Tracker(unittest.TestCase):
    def test_states(self):
        h = chrome.tracker(['A', 'B', 'C'], 1)
        self.assertEqual(h, '<div class="trk"><div class="ti done">A</div><div class="ti cur">B</div><div class="ti">C</div></div>')


class Geometry(unittest.TestCase):
    def test_measured_constants_in_css(self):
        for needle in ('.fr-uni{position:absolute;left:45px;top:54px;width:173px;height:76px}',
                       '.fr-bar{position:absolute;left:1190px;top:54px;width:15px;height:75px',
                       '.fr-tab{position:absolute;left:45px;top:679px;width:79px;height:15px',
                       '.fr-d3{position:absolute;left:1054px;top:671px;width:151px;height:31px}',
                       '.fr-tbar{position:absolute;left:107px;top:190px;width:16px;height:224px',
                       '.fr-seal{position:absolute;left:882px;top:332px;width:398px;height:388px}',
                       '.fr-title{position:absolute;left:243px;top:65px;width:922px',
                       '.body{position:absolute;left:73px;top:173px;width:1133px;height:432px;overflow:hidden}',
                       '.col.r{left:653px}', '.col.short{height:274px}',
                       '.fr-ttitle{position:absolute;left:173px;top:238px;width:934px',
                       '.trk{position:absolute;left:147px;top:676px;width:883px;height:22px'):
            self.assertIn(needle, chrome.CSS, needle)


if __name__ == '__main__':
    unittest.main()
