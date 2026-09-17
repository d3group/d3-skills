import os, subprocess, sys, tempfile, unittest
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


@unittest.skipUnless(HAVE_PW, 'playwright not installed')
class Shoot(unittest.TestCase):
    def run_shoot(self, deck_path, *args):
        out = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, os.path.join(HERE, 'd3deck', 'shoot.py'), deck_path, '--out', out, *args],
                           capture_output=True, text=True)
        return r, out

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
