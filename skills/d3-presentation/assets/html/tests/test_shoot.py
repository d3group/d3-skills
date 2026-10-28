import json, os, subprocess, sys, tempfile, unittest, warnings
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from d3deck import deck as B

try:
    import playwright  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False


def deck(overflow, negative=False):
    B.meta(title='T', sections=['A'])
    B.titleslide()
    B.section(1)
    B.onecol('Fine', '<p>short</p><p data-s="1">two</p>', steps=2)
    if overflow:
        B.onecol('Too tall', '<p style="height:900px">tall</p>')
    if negative:
        B.onecol('Too high', '<p style="margin-top:-60px">up</p>')
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    B.build('deck', out=out, embed_fonts=False)
    return out


class Runner:
    def run_shoot(self, deck_path, *args):
        out = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, os.path.join(HERE, 'd3deck', 'shoot.py'), deck_path, '--out', out, *args],
                           capture_output=True, text=True)
        return r, out


@unittest.skipUnless(HAVE_PW, 'playwright not installed')
class Shoot(Runner, unittest.TestCase):

    def test_clean_deck_shoots_every_step(self):
        r, out = self.run_shoot(deck(False), '--contact', '--pdf', os.path.join(tempfile.mkdtemp(), 'd.pdf'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(f for f in os.listdir(out) if f[0].isdigit()), ['001_1.png', '002_1.png', '003_1.png', '003_2.png'])
        self.assertIn('overflow audit: clean', r.stdout)
        self.assertTrue(any(f.startswith('contact_') for f in os.listdir(out)))
        self.assertIn('PDF ->', r.stdout)

    def test_overflow_is_reported(self):
        r, out = self.run_shoot(deck(True))
        self.assertEqual(r.returncode, 1)
        self.assertIn('OVERFLOW', r.stdout)
        self.assertIn('content taller than its box', r.stdout)
        self.assertNotIn('p.  "tall"', r.stdout)
        self.assertEqual(r.stdout.count('content taller than its box'), 1)

    def test_range(self):
        r, out = self.run_shoot(deck(False), '--from', '3', '--to', '3')
        self.assertEqual(sorted(f for f in os.listdir(out) if f[0].isdigit()), ['003_1.png', '003_2.png'])

    def test_negative_overflow_is_reported(self):
        r, out = self.run_shoot(deck(False, negative=True))
        self.assertEqual(r.returncode, 1)
        self.assertIn('content above or left of its box', r.stdout)
        self.assertIn('top', r.stdout)


def lint_deck(*slides, css='', meta=None):
    """A deck with a title slide and the given (title, body, kwargs) content slides. meta: extra meta() arguments."""
    m = B.meta(**dict(dict(title='T', sections=['A']), **(meta or {})))
    B.titleslide()
    if m['tracker']:                     # the tracker shows on the slides of a section
        B.section(1)
    for title, body, kw in slides:
        B.onecol(title, body, **kw)
    if css:
        B.css(css)
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        B.build('deck', out=out, embed_fonts=False)
    return out


FILLED = '<div style="height:300px;background:#EEF"><p>fills the region</p></div>'   # + a line of text below still ends near the bottom
CENTRED = '<div style="height:100%;display:flex;align-items:center"><p>one centred line</p></div>'


@unittest.skipUnless(HAVE_PW, 'playwright not installed')
class Lint(Runner, unittest.TestCase):
    def test_hole_on_glued_slide_only(self):
        r, out = self.run_shoot(lint_deck(('Glued', '<p>one line at the top</p>', {}),
                                          ('Filled', FILLED + '<p>one line below</p>', {}), ('Centred', CENTRED, {})))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('LINT:', r.stdout)
        holes = [l for l in r.stdout.splitlines() if 'hole:' in l]
        self.assertEqual(len(holes), 1, r.stdout)
        self.assertTrue(holes[0].strip().startswith('2.1'), holes)

    def test_emoji_fails_and_names_the_slide(self):
        r, out = self.run_shoot(lint_deck(('Fine', FILLED, {}), ('Emoji', FILLED + '<p>done ✓</p>', {})))
        self.assertEqual(r.returncode, 1)
        line = next(l for l in r.stdout.splitlines() if 'emoji' in l)
        self.assertTrue(line.strip().startswith('3.1'), line)
        self.assertIn("icon('check')", line)

    def test_arrows_are_not_emoji(self):
        r, out = self.run_shoot(lint_deck(('Arrows', FILLED + '<p>a → b ↑</p>', {})))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn('emoji', r.stdout)

    def test_greek_in_uppercase_label(self):
        r, out = self.run_shoot(lint_deck(('Caps', FILLED + '<div style="text-transform:uppercase">level α = .05</div>', {})))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('α prints as Α', r.stdout)
        self.assertIn('nocaps', r.stdout)

    def test_provenance_cut_only_when_too_long(self):
        long = ' · '.join(['Eigene Rechnung mit vielen Details'] * 6)
        r, out = self.run_shoot(lint_deck(('Long', FILLED, {'provenance': long}), ('Short', FILLED, {'provenance': 'Table 3 · N = 38'})))
        self.assertEqual(r.stdout.count('provenance cut'), 1, r.stdout)
        self.assertRegex(r.stdout, r'2\.1 +warn +provenance cut')            # the long one on slide 2, not the short one

    def test_provenance_keeps_clear_of_the_beamer_tracker(self):
        # beamer: the tracker takes the footer line up to x 834, so the source line keeps the 300 px right of it
        mid = 'Own calculation, survey wave 2 (N = 412), weighted, 2025'     # about 480 px: fits half the line, not 300 px
        r, out = self.run_shoot(lint_deck(('Mid', FILLED, {'provenance': mid}), meta={'look': 'beamer', 'tracker': True}))
        self.assertRegex(r.stdout, r'3\.1 +warn +provenance cut', r.stdout)  # slide 3, after the section divider

    def test_wordy(self):
        words = ' '.join(['word'] * 120)
        r, out = self.run_shoot(lint_deck(('Wordy', f'<p style="font-size:9px;line-height:1">{words}</p>' + FILLED, {})))
        self.assertIn('wordy: ', r.stdout)
        self.assertIn('words on the slide', r.stdout)

    def test_references_fit_in_every_look(self):
        ref = 'Arrow, K. J., Harris, T., & Marschak, J. (1951). Optimal inventory policy. Econometrica, 19(3), 250-272.'
        for look in ('klar', 'beamer', 'uni'):
            B.meta(title='T', sections=['A'], look=look)
            B.titleslide()
            B.references([ref] * 14)
            out = os.path.join(tempfile.mkdtemp(), 'deck.html')
            B.build('deck', out=out, embed_fonts=False)
            r, _ = self.run_shoot(out)
            self.assertEqual(r.returncode, 0, f'{look}: ' + r.stdout + r.stderr)
            self.assertIn('overflow audit: clean', r.stdout, look)
            self.assertNotIn('wordy', r.stdout, look)

    def test_signature_and_report(self):
        r, out = self.run_shoot(lint_deck(('Object', '<div class="k-tile" style="height:380px">tile</div>', {}),
                                          ('Button', FILLED + '<button>go</button>', {}),
                                          ('Text', FILLED.replace('background:#EEF', ''), {})))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('signature  3 content slides · 0 with builds · 0 with motion · 1 with a designed object · '
                      '1 interactive elements on 1 slides', r.stdout)
        self.assertIn('text only: 3, 4', r.stdout)
        with open(os.path.join(out, 'report.json'), encoding='utf-8') as fh:
            rep = json.load(fh)
        self.assertEqual(rep['signature']['text_only'], [3, 4])
        self.assertEqual(rep['signature']['objects'], 1)
        self.assertIn('lint', rep)
        self.assertEqual(rep['console'], [])

    def test_slot_budget(self):
        r, out = self.run_shoot(lint_deck(('One', FILLED, {'time': '4:30'}), ('Two', FILLED, {'time': '6:00'}),
                                          ('Three', FILLED, {})), '--slot', '10')
        self.assertIn('budget 10:30 of 10:00 slot', r.stdout)
        self.assertIn('over the slot by 0:30', r.stdout)
        self.assertIn('no time= on content slides 4 while others carry one', r.stdout)

    def test_console_errors_fail(self):
        B.meta(title='T', sections=['A'])
        B.titleslide()
        B.onecol('Broken', FILLED)
        B.js('console.error("boom from the deck")')
        path = os.path.join(tempfile.mkdtemp(), 'deck.html')
        B.build('deck', out=path, embed_fonts=False)
        r, out = self.run_shoot(path)
        self.assertEqual(r.returncode, 1)
        self.assertIn('CONSOLE:', r.stdout)
        self.assertIn('boom from the deck', r.stdout)

    def test_animations_are_finished_unless_live(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        block = '<div class="blk" style="width:300px;height:200px;background:#000;animation:fadein 6s linear both"></div>'
        path = lint_deck(('Moving', block + FILLED.replace('300px', '160px'), {}),
                         css='@keyframes fadein{from{opacity:0}}')
        r, out = self.run_shoot(path)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('1 with motion', r.stdout)
        px = Image.open(os.path.join(out, '002_1.png')).convert('L').getpixel((150, 260))
        self.assertLess(px, 40, 'finished animation should show the opaque end state')
        r, out = self.run_shoot(path, '--live')
        px = Image.open(os.path.join(out, '002_1.png')).convert('L').getpixel((150, 260))
        self.assertGreater(px, 150, '--live should catch the fade early')


class Helpers(unittest.TestCase):
    def test_chrome_binary_type(self):
        sys.path.insert(0, os.path.join(HERE, 'd3deck'))
        import shoot
        b = shoot.chrome_binary()
        self.assertTrue(b is None or os.path.exists(b))

    def test_missing_deck_exits(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, 'd3deck', 'shoot.py'), '/nonexistent/deck.html'],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('no such deck', r.stdout + r.stderr)

    def test_contact_sheets_from_pngs(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        sys.path.insert(0, os.path.join(HERE, 'd3deck'))
        import shoot
        d = tempfile.mkdtemp()
        shots = []
        for i in range(3):
            p = os.path.join(d, f'00{i + 1}_1.png')
            Image.new('RGB', (128, 72), 'white').save(p)
            shots.append(p)
        shoot.make_contact_sheets(shots, d, cols=2, rows=1, thumb_w=64)
        sheets = sorted(f for f in os.listdir(d) if f.startswith('contact_'))
        self.assertEqual(sheets, ['contact_01.png', 'contact_02.png'])


if __name__ == '__main__':
    unittest.main()
