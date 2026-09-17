import os, sys, unittest
import shutil, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import engine
from d3deck import nav, presenter


class Engine(unittest.TestCase):
    def test_tokens(self):
        for needle in ('--navy:#153F87', '--orange:#F29100', '--bar:#004389', '--navy-15:#DCE2ED',
                       '--fs-Large:41px', '--fs-small:28px', '--fs-tiny:17px', '--fs-chrome:13px',
                       '--fs-display:150px'):
            self.assertIn(needle, engine.CSS, needle)

    def test_ghosting_and_modes(self):
        self.assertIn('.gh{opacity:.15;filter:grayscale(1)}', engine.CSS)
        self.assertIn('rgba(255,255,255,.6997)', engine.CSS)
        self.assertIn('body.shot', engine.CSS)
        self.assertIn('@media print', engine.CSS)
        self.assertIn('.stepdots{position:absolute;right:80px;top:140px', engine.CSS)

    def test_js_contract(self):
        for needle in ('__META__', 'function steps(', 'function applyStep(', 'function paint(', 'function show(',
                       'function fwd(', 'function back(', 'function go(', 'function fit(', "new CustomEvent('d3paint'",
                       'function togglePres(', "classList.add('shot')", "addEventListener('hashchange'"):
            self.assertIn(needle, engine.JS, needle)


class Syntax(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_scripts_parse(self):
        d = tempfile.mkdtemp()
        for name, js in (('engine', engine.JS.replace('__META__', '[]')),
                         ('nav', nav.JS.replace('__HUB__', '-1')),
                         ('presenter', presenter.JS)):
            p = os.path.join(d, name + '.js')
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(js)
            r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
