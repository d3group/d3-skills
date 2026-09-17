import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import deck as B, nav

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None


class Static(unittest.TestCase):
    def test_contract(self):
        self.assertIn('__HUB__', nav.JS)
        self.assertIn("e.key==='/'", nav.JS)
        self.assertIn('.hub{', nav.CSS)
        self.assertIn('#pal{', nav.CSS)
        self.assertIn('[data-jump]{cursor:pointer}', nav.CSS)


def deck_file():
    B.meta(title='T', sections=['Alpha', 'Beta'])
    B.titleslide()
    B.section(1)
    B.onecol('First things', 'x', src='opening')
    B.section(2)
    B.onecol('Second things', 'x')
    B.appendix()
    B.backuphome()
    B.onecol('Deep dive on gamma', 'x')
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    B.build('deck', out=out, embed_fonts=False)
    return 'file://' + out


@unittest.skipUnless(sync_playwright, 'playwright not installed')
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = deck_file()
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

    def test_tabs_and_hub(self):
        p = self.page()
        p.click('.jt >> text=Beta')
        self.assertEqual(p.evaluate('cur'), 3)
        self.assertTrue(p.evaluate('document.querySelector(".jt.on").textContent') == 'Beta')
        p.keyboard.press('h')
        self.assertEqual(p.evaluate('cur'), 5)
        p.click('.hub .hi')
        self.assertEqual(p.evaluate('cur'), 6)
        p.close()

    def test_palette(self):
        p = self.page()
        p.keyboard.press('/')
        self.assertTrue(p.evaluate('document.getElementById("pal").classList.contains("on")'))
        p.keyboard.type('gamma')
        self.assertEqual(p.evaluate('document.querySelectorAll("#pall .pr").length'), 1)
        p.keyboard.press('Enter')
        self.assertFalse(p.evaluate('document.getElementById("pal").classList.contains("on")'))
        self.assertEqual(p.evaluate('cur'), 6)
        p.keyboard.press('/')
        p.keyboard.press('Escape')
        self.assertFalse(p.evaluate('document.getElementById("pal").classList.contains("on")'))
        p.keyboard.press('/')
        p.keyboard.type('zzz-no-match')
        p.keyboard.press('ArrowDown')
        self.assertEqual(p.evaluate('psel'), 0)
        p.keyboard.press('Escape')
        p.evaluate('const i=document.createElement("input"); i.id="other"; document.body.appendChild(i); i.focus()')
        p.keyboard.press('/')
        self.assertFalse(p.evaluate('document.getElementById("pal").classList.contains("on")'))
        p.close()


if __name__ == '__main__':
    unittest.main()
