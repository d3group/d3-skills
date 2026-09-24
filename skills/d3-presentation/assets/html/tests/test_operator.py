import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import deck as B, engine, nav, presenter

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None


class Static(unittest.TestCase):
    def test_contract(self):
        for key in ("k==='o'", "k==='?'", "coverKey('b')", "coverKey('w')", "classList.toggle('laser')"):
            self.assertIn(key, engine.JS)
        self.assertIn('let navTo=', engine.JS)
        self.assertIn('.opov{', engine.CSS)
        self.assertIn('.opov,#otoast,#ocover,#olaser{display:none!important}', engine.CSS)   # never printed
        self.assertIn('psnip', nav.JS)
        self.assertIn("type:'relay'", presenter.JS)
        self.assertIn('#ppace', presenter.CSS)


def deck_file(timed=False):
    t = {'time': '0:30'} if timed else {}
    B.meta(title='T', sections=['A', 'B'])
    B.titleslide(**t)
    B.section(1, **t)
    B.onecol('Alpha claim', '<p>x</p><p data-s="1">y</p>', steps=2, notes='mention the zebrafish result here', **t)
    B.onecol('Beta claim', '<button id="bt" class="probe">press</button><input id="rg" type="range" min="0" max="10" value="2">',
             notes='second note', **t)
    B.section(2, **t)
    B.onecol('Gamma claim', 'x', **t)
    B.js("document.getElementById('bt').addEventListener('click',e=>{e.currentTarget.dataset.hits=(+(e.currentTarget.dataset.hits||0)+1)});"
         "document.getElementById('rg').addEventListener('input',e=>{e.currentTarget.dataset.seen=e.currentTarget.value});")
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    B.build('deck', out=out, embed_fonts=False)
    return 'file://' + out


@unittest.skipUnless(sync_playwright, 'playwright not installed')
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = deck_file()
        cls.timed = deck_file(timed=True)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def page(self, url=None, suffix=''):
        p = self.browser.new_page(viewport={'width': 1320, 'height': 830})
        p.goto((url or self.url) + suffix)
        p.wait_for_timeout(300)
        return p

    def on(self, p, sel, cls='on'):
        return p.evaluate(f"document.querySelector('{sel}').classList.contains('{cls}')")

    def test_overview_click_and_keys(self):
        p = self.page(suffix='#3.2')
        p.keyboard.press('o')
        self.assertTrue(self.on(p, '#ov'))
        self.assertEqual(p.evaluate('document.querySelectorAll(".ovt").length'), 6)
        self.assertTrue(self.on(p, '.ovt[data-i="2"]', 'cur'))
        self.assertEqual(p.evaluate('document.querySelectorAll("#ovg .sl.is-current").length'), 0)
        self.assertEqual(p.evaluate('document.querySelectorAll("#ovg .gh").length'), 0)       # thumbnails show the final step
        p.keyboard.press('ArrowRight')                 # moves the selection, not the deck
        self.assertEqual(p.evaluate('[cur, st]'), [2, 1])
        p.keyboard.press('/')                          # swallowed while the overview is open
        self.assertFalse(self.on(p, '#pal'))
        p.click('.ovt[data-i="5"]')
        self.assertFalse(self.on(p, '#ov'))
        self.assertEqual(p.evaluate('cur'), 5)
        p.keyboard.press('o')
        p.keyboard.press('ArrowLeft')
        p.keyboard.press('Enter')
        self.assertEqual(p.evaluate('cur'), 4)
        p.keyboard.press('O')
        p.keyboard.press('Escape')
        self.assertFalse(self.on(p, '#ov'))
        self.assertEqual(p.evaluate('cur'), 4)
        p.close()

    def test_digits_enter_jump(self):
        p = self.page()
        p.keyboard.press('4')
        self.assertTrue(self.on(p, '#otoast'))
        self.assertIn('4', p.evaluate('document.getElementById("otoast").textContent'))
        p.keyboard.press('Enter')
        self.assertEqual(p.evaluate('[cur, st]'), [3, 0])
        p.keyboard.press('9')
        p.keyboard.press('9')
        p.keyboard.press('Enter')                      # past the end: last slide
        self.assertEqual(p.evaluate('cur'), 5)
        p.keyboard.press('2')
        p.keyboard.press('Escape')                     # cancels
        p.keyboard.press('Enter')
        self.assertEqual(p.evaluate('cur'), 5)
        p.close()

    def test_black_white_laser_help(self):
        p = self.page()
        body = 'document.body.classList'
        p.keyboard.press('b')
        self.assertTrue(p.evaluate(f'{body}.contains("cover-b")'))
        p.keyboard.press('w')
        self.assertTrue(p.evaluate(f'{body}.contains("cover-w") && !{body}.contains("cover-b")'))
        p.keyboard.press('w')
        self.assertFalse(p.evaluate(f'{body}.contains("cover-w")'))
        p.keyboard.press('B')
        p.keyboard.press('Escape')
        self.assertFalse(p.evaluate(f'{body}.contains("cover-b")'))
        p.keyboard.press('l')
        self.assertTrue(p.evaluate(f'{body}.contains("laser")'))
        p.mouse.move(300, 200)
        self.assertEqual(p.evaluate('document.getElementById("olaser").style.left'), '300px')
        p.keyboard.press('l')
        self.assertFalse(p.evaluate(f'{body}.contains("laser")'))
        p.keyboard.press('?')
        self.assertTrue(self.on(p, '#ohelp'))
        self.assertGreaterEqual(p.evaluate('document.querySelectorAll("#okeys > div").length'), 14)
        p.keyboard.press('ArrowRight')                 # swallowed
        self.assertEqual(p.evaluate('cur'), 0)
        p.keyboard.press('Escape')
        self.assertFalse(self.on(p, '#ohelp'))
        p.close()

    def test_search_finds_notes(self):
        p = self.page()
        p.keyboard.press('/')
        p.keyboard.type('zebrafish')
        self.assertEqual(p.evaluate('document.querySelectorAll("#pall .pr").length'), 1)
        self.assertIn('zebrafish', p.evaluate('document.querySelector("#pall .pr .sn mark").textContent'))
        p.keyboard.press('Enter')
        self.assertEqual(p.evaluate('cur'), 2)
        p.keyboard.press('/')
        p.keyboard.type('alpha')                       # a title hit carries no snippet
        self.assertEqual(p.evaluate('document.querySelectorAll("#pall .pr .sn").length'), 0)
        p.close()

    def test_presenter_pace_pause_relay(self):
        ctx = self.browser.new_context(viewport={'width': 1320, 'height': 830})
        page = ctx.new_page()
        page.goto(self.timed + '#4')
        page.wait_for_timeout(300)
        with page.expect_popup() as pi:
            page.keyboard.press('s')                   # S is an alias of N
        pop = pi.value
        pop.wait_for_load_state()
        pop.wait_for_timeout(700)
        self.assertEqual(pop.evaluate('cur'), 3)
        pace = pop.evaluate('document.getElementById("ppace").textContent')
        self.assertIn('ahead by', pace)                # 1:30 of budget before this slide, a second elapsed
        self.assertIn('budget 03:00', pace)
        pop.keyboard.press('p')
        self.assertIn('paused', pop.evaluate('document.getElementById("ppace").textContent'))
        self.assertFalse(page.evaluate('document.body.classList.contains("pres")'))
        pop.click('#stage .sl.on button.probe')
        page.wait_for_timeout(200)
        self.assertEqual(page.evaluate('document.getElementById("bt").dataset.hits'), '1')
        pop.evaluate("""(() => { const r = document.querySelector('#stage .sl.on input[type=range]');
                                 r.focus(); })()""")
        pop.keyboard.press('ArrowRight')               # a real input event on the range in the presenter window
        page.wait_for_timeout(200)
        self.assertEqual(page.evaluate('document.getElementById("rg").value'), '3')
        self.assertEqual(page.evaluate('document.getElementById("rg").dataset.seen'), '3')
        self.assertEqual(page.evaluate('cur'), 3)      # typing in the input did not navigate
        pop.evaluate('document.activeElement.blur()')
        pop.keyboard.press('2')                        # number jump from the presenter drives the main window
        pop.keyboard.press('Enter')
        page.wait_for_timeout(300)
        self.assertEqual(page.evaluate('cur'), 1)
        self.assertEqual(pop.evaluate('cur'), 1)
        pop.keyboard.press('b')                        # black screen goes to the projected window
        page.wait_for_timeout(200)
        self.assertTrue(page.evaluate('document.body.classList.contains("cover-b")'))
        self.assertFalse(pop.evaluate('document.body.classList.contains("cover-b")'))
        ctx.close()

    def test_no_pace_without_budgets(self):
        ctx = self.browser.new_context(viewport={'width': 1320, 'height': 830})
        page = ctx.new_page()
        page.goto(self.url + '#3')
        page.wait_for_timeout(300)
        with page.expect_popup() as pi:
            page.keyboard.press('n')
        pop = pi.value
        pop.wait_for_load_state()
        pop.wait_for_timeout(500)
        self.assertEqual(pop.evaluate('document.getElementById("ppace").textContent'), '')
        ctx.close()


if __name__ == '__main__':
    unittest.main()
