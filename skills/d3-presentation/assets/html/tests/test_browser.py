import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import deck as B

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None


def deck_file(**meta_kw):
    B.meta(title='T', presenter='Ada', sections=['A', 'B'], **meta_kw)
    B.titleslide()
    B.agenda()
    B.section(1)
    B.onecol('S1', '<p>x</p><p data-s="1">y</p><p data-s="2" data-soft="1">z</p>', steps=3, notes='note one')
    B.section(2)
    B.onecol('S2', 'x')
    B.thankyou()
    B.appendix()
    B.backuphome()
    B.onecol('B1', 'x', notes='backup note')
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    B.build('deck', out=out, embed_fonts=False)
    return 'file://' + out


@unittest.skipUnless(sync_playwright, 'playwright not installed')
class Engine(unittest.TestCase):
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

    def test_steps_and_ghosting(self):
        p = self.page('#4')
        self.assertEqual(p.evaluate('N'), 9)
        self.assertEqual(p.evaluate('cur'), 3)
        self.assertTrue(p.evaluate('document.querySelector(".sl.on [data-s=\\"1\\"]").classList.contains("gh")'))
        p.keyboard.press('ArrowRight')
        self.assertFalse(p.evaluate('document.querySelector(".sl.on [data-s=\\"1\\"]").classList.contains("gh")'))
        self.assertTrue(p.evaluate('document.querySelector(".sl.on [data-s=\\"2\\"]").classList.contains("gh-soft")'))
        self.assertEqual(p.evaluate('location.hash'), '#4.2')
        p.keyboard.press('ArrowRight')
        p.keyboard.press('ArrowRight')
        self.assertEqual(p.evaluate('cur'), 4)
        p.keyboard.press('ArrowLeft')
        self.assertEqual(p.evaluate('[cur, st]'), [3, 2])
        p.close()

    def test_present_and_shot_modes(self):
        p = self.page()
        p.keyboard.press('f')
        self.assertTrue(p.evaluate('document.body.classList.contains("pres")'))
        p.keyboard.press('Escape')
        self.assertFalse(p.evaluate('document.body.classList.contains("pres")'))
        p.close()
        p = self.page('?shot#2')
        self.assertTrue(p.evaluate('document.body.classList.contains("shot")'))
        self.assertEqual(p.evaluate('document.querySelector(".sl.on").style.transform'), 'translate(-50%, -50%) scale(1)')
        p.close()

    def test_foot_labels(self):
        p = self.page('#9')
        self.assertIn('backup 2 of 2', p.evaluate('document.getElementById("fr").textContent'))
        p.close()

    def test_hash_change_navigates_open_page(self):
        p = self.page()
        p.evaluate('location.hash = "#4.2"')
        p.wait_for_timeout(150)
        self.assertEqual(p.evaluate('[cur, st]'), [3, 1])
        p.evaluate('location.hash = "#999"')
        p.wait_for_timeout(150)
        self.assertEqual(p.evaluate('cur'), 8)
        p.close()


if __name__ == '__main__':
    unittest.main()
