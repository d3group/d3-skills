import base64, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import chrome, paths


class Logos(unittest.TestCase):
    def test_uni_svg_gets_viewbox_and_loses_size(self):
        s = chrome.inline_svg(os.path.join(paths.asset_dir('logos'), chrome.UW_LOGO['navy']))
        head = s[:s.index('>') + 1]
        self.assertIn('viewBox="0 0 692 205"', head)
        self.assertNotIn(' width="', head)
        self.assertNotIn('<?xml', s)
        self.assertIn('#02246C', s)                       # the official screen navy, not the CMYK conversion

    def test_d3_svg_loses_text_and_prefixes_classes(self):
        s = chrome.inline_svg(os.path.join(paths.asset_dir('logos'), chrome.D3_SVG))
        self.assertNotIn('<text', s)
        self.assertNotIn('cls-1', s)
        self.assertIn('#f39200', s.lower())

    def test_svg_uri_and_negative_d3_logo(self):
        uri = chrome.svg_uri(chrome.D3_SVG)
        self.assertTrue(uri.startswith('data:image/svg+xml;base64,'))
        raw = base64.b64decode(uri.split(',', 1)[1]).decode()
        self.assertNotIn('<text', raw)
        self.assertIn('#1f2043', raw.lower())
        neg = base64.b64decode(chrome.svg_uri(chrome.D3_SVG, chrome.D3_NEG).split(',', 1)[1]).decode()
        self.assertNotIn('#1f2043', neg.lower())
        self.assertIn('#f39200', neg.lower())             # the orange stays on navy

    def test_seals_exist(self):
        for name in chrome.UW_SEAL.values():
            self.assertTrue(os.path.exists(os.path.join(paths.asset_dir('logos'), name)), name)

    def test_assets_css_per_look(self):
        d3 = chrome.assets_css('klar')
        self.assertIn('.d3-co{background-image:url(data:image/svg+xml', d3)
        self.assertIn('.uw-seal{background-image:url(' + chrome.svg_uri(chrome.UW_SEAL['blue']), d3)
        self.assertNotIn('.uw-photo', d3)
        uni = chrome.assets_css('uni', photo=True)
        self.assertNotIn('.d3-co', uni)
        self.assertIn('.uw-seal{background-image:url(' + chrome.svg_uri(chrome.UW_SEAL['coral']), uni)
        self.assertIn('.uw-photo{background-image:url(data:image/jpeg', uni)

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
    def test_d3_frame(self):
        h = chrome.frame('T', '<div class="body">B</div>', page='3', foot='Me | Chair | Talk', dots='<i>d</i>')
        for cls in ('uw-logo uw-logo-navy', 'uw-rule', 'd3-co', 'uw-title', 'uw-foot', 'uw-num'):
            self.assertIn(f'class="{cls}"', h)
        self.assertIn('<div class="uw-num">3</div>', h)
        self.assertTrue(h.endswith('<div class="uw-num">3</div><i>d</i>'))

    def test_uni_frame_has_no_d3_logo(self):
        h = chrome.uni_frame('T', 'x', page='1')
        self.assertNotIn('d3-co', h)
        self.assertIn('uw-logo', h)

    def test_frame_without_page_or_foot(self):
        h = chrome.frame('', 'x')
        self.assertNotIn('uw-num', h)
        self.assertNotIn('uw-foot', h)
        self.assertNotIn('uw-title', h)

    def test_covers(self):
        band = chrome.cover_slide('Big', 'small', 'Ada', 'Würzburg')
        for cls in ('uw-cover uw-c-band', 'uw-band', 'uw-logo uw-logo-navy', 'uw-seal', 'd3-co cov', 'uw-ttitle', 'uw-tsub', 'uw-tname'):
            self.assertIn(f'class="{cls}"', band)
        navy = chrome.cover_slide('Big', cover='navy')
        self.assertIn('class="d3-co cov neg"', navy)          # white D3 logo on navy
        self.assertIn('uw-logo-white', navy)
        self.assertNotIn('d3-co', chrome.uni_title('Big'))
        self.assertIn('uw-c-navy', chrome.uni_title('Big'))   # the uni default stays navy
        with self.assertRaises(ValueError):
            chrome.cover_slide('Big', cover='pink')

    def test_divider_with_part_list(self):
        part = [(4, '1', 'First claim'), (5, '2', 'Second claim')]
        h = chrome.divider(1, ['Intro', 'Method'], 'Why?', 'en', part)
        self.assertIn('<div class="uw-sk">Part 1 of 2</div>', h)
        self.assertIn('<div class="uw-sn">01</div>', h)
        self.assertIn('<div class="uw-sq">Why?</div>', h)
        self.assertEqual(h.count('class="spi"'), 2)
        self.assertIn('data-jump="4"', h)
        self.assertNotIn('uw-part', chrome.divider(2, ['Intro', 'Method'], '', 'de'))
        self.assertIn('Teil 2 von 2', chrome.divider(2, ['Intro', 'Method'], '', 'de'))
        many = [(i, str(i), f'c{i}') for i in range(8)]
        self.assertIn('and 2 more', chrome.divider(1, ['A'], '', 'en', many))

    def test_thankyou(self):
        h = chrome.uni_thankyou('', ['Ada', 'ada@uni-wuerzburg.de'], 'de', d3=True)
        self.assertIn('Vielen Dank', h)
        self.assertIn('<b>Kontakt</b><div>Ada</div>', h)
        self.assertIn('class="d3-co cov"', h)
        self.assertNotIn('d3-co', chrome.uni_thankyou('Danke', ['Ada'], 'de'))


class Agenda(unittest.TestCase):
    S = ['Intro', 'Method', 'Results', 'Outlook']

    def test_numbers_and_links(self):
        h = chrome.uni_agenda(self.S, links={1: 'sec-1', 2: 'sec-2'})
        self.assertEqual(h.count('<div class="uw-ag">'), 4)
        self.assertIn('>04</span>', h)
        self.assertEqual(h.count('data-jump="@@sec-1@@"'), 2)
        self.assertIn('<div class="uw-title">Agenda</div>', h)


class Tracker(unittest.TestCase):
    def test_states(self):
        h = chrome.tracker(['A', 'B', 'C'], 1)
        self.assertEqual(h, '<div class="trk"><div class="ti done">A</div><div class="ti cur">B</div><div class="ti">C</div></div>')


class Geometry(unittest.TestCase):
    def test_master_constants_in_css(self):
        """The boxes of the master's slide layouts (1 px = 9525 EMU) and the co-branding slot."""
        for needle in ('.uw-logo{position:absolute;left:72px;top:23px;width:186px;height:55px',
                       '.uw-rule{position:absolute;left:73px;top:94px;width:1138px;height:1px;background:#D3D6DC}',
                       '.d3-co{position:absolute;left:1037px;top:35px;width:174px;height:35px',
                       '.uw-title{position:absolute;left:74px;top:111px;width:1137px;font-size:32px;font-weight:600',
                       '.body{position:absolute;left:74px;top:225px;width:1137px;height:420px;overflow:hidden}',
                       '.col.r{left:663px}', '.col.short{height:335px}',
                       '.uw-fl{position:absolute;left:74px;top:680px;width:1076px;height:23px',
                       '.uw-num{position:absolute;left:1169px;top:671px;width:42px;height:49px;background:var(--navy)',
                       '.uw-seal{position:absolute;left:972px;top:412px;width:308px;height:308px',
                       '.uw-band,.uw-box{position:absolute;left:39px;top:425px;height:245px',
                       '.uw-agl{position:absolute;left:73px;top:197px'):
            self.assertIn(needle, chrome.CSS, needle)


if __name__ == '__main__':
    unittest.main()
