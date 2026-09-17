import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import deck as B, presenter

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None


class Static(unittest.TestCase):
    def test_contract(self):
        self.assertIn("'?presenter'", presenter.JS)
        self.assertIn("type:'sync'", presenter.JS)
        self.assertIn('body.presenter', presenter.CSS)
        self.assertIn('#ndrawer', presenter.CSS)


def deck_file():
    B.meta(title='T', sections=['A'])
    B.titleslide()
    B.section(1)
    B.onecol('S1', '<p>x</p><p data-s="1">y</p>', steps=2, notes='first note')
    B.onecol('S2', '<div id="anchor">x</div>', notes='second note')
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

    def test_presenter_window_syncs_both_ways(self):
        ctx = self.browser.new_context(viewport={'width': 1320, 'height': 830})
        page = ctx.new_page()
        page.goto(self.url + '#3')
        page.wait_for_timeout(300)
        with page.expect_popup() as pi:
            page.keyboard.press('n')
        pop = pi.value
        pop.wait_for_load_state()
        pop.wait_for_timeout(600)
        self.assertTrue(pop.evaluate('document.body.classList.contains("presenter")'))
        self.assertEqual(pop.evaluate('cur'), 2)
        self.assertEqual(pop.evaluate('document.getElementById("pnotes").textContent'), 'first note')
        self.assertEqual(pop.evaluate('document.querySelectorAll("#pnext .sl").length'), 1)
        pop.evaluate('show(2, 1)')
        pop.wait_for_timeout(150)
        self.assertEqual(pop.evaluate('document.querySelectorAll("#pnext [id]").length'), 0)
        self.assertEqual(pop.evaluate('document.querySelectorAll("#pnext .sl").length'), 1)
        pop.keyboard.press('ArrowRight')            # presenter drives the main window
        page.wait_for_timeout(300)
        self.assertEqual(page.evaluate('[cur, st]'), [2, 1])
        self.assertEqual(pop.evaluate('[cur, st]'), [2, 1])
        page.keyboard.press('ArrowRight')           # main window drives the presenter
        pop.wait_for_timeout(300)
        self.assertEqual(pop.evaluate('cur'), 3)
        self.assertEqual(pop.evaluate('document.getElementById("pnotes").textContent'), 'second note')
        self.assertIn(':', pop.evaluate('document.getElementById("pclock").textContent'))
        pop.keyboard.press('f')
        pop.wait_for_timeout(150)
        self.assertFalse(pop.evaluate('document.body.classList.contains("pres")'))
        self.assertFalse(page.evaluate('document.body.classList.contains("pres")'))
        ctx.close()

    def test_drawer_fallback_when_popup_blocked(self):
        page = self.browser.new_page(viewport={'width': 1320, 'height': 830})
        page.goto(self.url + '#3')
        page.wait_for_timeout(300)
        page.evaluate('window.open = () => null')
        page.keyboard.press('n')
        self.assertTrue(page.evaluate('document.body.classList.contains("notes")'))
        self.assertEqual(page.evaluate('document.getElementById("ndrawer").textContent'), 'first note')
        page.keyboard.press('n')
        self.assertFalse(page.evaluate('document.body.classList.contains("notes")'))
        page.close()


if __name__ == '__main__':
    unittest.main()
