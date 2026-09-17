import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import init


class Scaffold(unittest.TestCase):
    def test_tree_and_build(self):
        dest = tempfile.mkdtemp()
        target = init.scaffold('my_talk', dest)
        for rel in ('slides.py', 'figures', 'd3deck/__init__.py', 'd3deck/deck.py', 'd3deck/engine.py',
                    'd3deck/seal.png', 'd3deck/fonts/Inter_18pt-Regular.ttf', 'd3deck/fonts/Inter_18pt-BoldItalic.ttf',
                    'd3deck/logos/Universitaet_Wuerzburg_Logo.svg', 'd3deck/logos/DataDrivenDecisions_2c.svg'):
            self.assertTrue(os.path.exists(os.path.join(target, rel)), rel)
        self.assertFalse(os.path.exists(os.path.join(target, 'd3deck', 'tests')))
        r = subprocess.run([sys.executable, 'slides.py'], cwd=target, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = os.path.join(target, 'dist', 'my_talk.html')
        self.assertTrue(os.path.exists(out))
        with open(out, encoding='utf-8') as fh:
            doc = fh.read()
        self.assertEqual(doc.count('@font-face'), 5)
        self.assertIn('data:image/png;base64', doc)
        self.assertIn('<title>', doc)
        self.assertGreater(len(doc), 2_000_000)

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
