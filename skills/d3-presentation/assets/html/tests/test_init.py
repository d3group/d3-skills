import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import init


class Scaffold(unittest.TestCase):
    def test_tree_and_build(self):
        dest = tempfile.mkdtemp()
        target = init.scaffold('my_talk', dest)
        for rel in ('slides.py', 'figures', 'd3deck/__init__.py', 'd3deck/deck.py', 'd3deck/engine.py',
                    'd3deck/fonts/InclusiveSansUW-Regular.ttf', 'd3deck/fonts/InclusiveSansUW-Bold.ttf',
                    'd3deck/fonts/D3Symbols-Regular.ttf', 'd3deck/logos/uw-logo-navy.svg', 'd3deck/logos/uw-seal-blue.svg',
                    'd3deck/logos/DataDrivenDecisions_2c.svg'):
            self.assertTrue(os.path.exists(os.path.join(target, rel)), rel)
        self.assertFalse(os.path.exists(os.path.join(target, 'd3deck', 'tests')))
        r = subprocess.run([sys.executable, 'slides.py'], cwd=target, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = os.path.join(target, 'dist', 'my_talk.html')
        self.assertTrue(os.path.exists(out))
        with open(out, encoding='utf-8') as fh:
            doc = fh.read()
        self.assertEqual(doc.count('@font-face'), 7)                       # Inclusive Sans UW (5) and D3 Symbols (2)
        self.assertIn('data:image/svg+xml;base64', doc)                      # the logos, once per file
        self.assertIn('<title>', doc)
        self.assertGreater(len(doc), 400_000)                                # fonts embedded: the file stands alone

    def test_refuses_existing(self):
        dest = tempfile.mkdtemp()
        init.scaffold('again', dest)
        with self.assertRaises(SystemExit):
            init.scaffold('again', dest)

    def test_name_rule(self):
        with self.assertRaises(SystemExit):
            init.scaffold('My Talk', tempfile.mkdtemp())


if __name__ == '__main__':
    unittest.main()
