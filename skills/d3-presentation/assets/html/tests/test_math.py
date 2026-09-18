import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from d3deck import deck as B

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def deck(body, **meta):
    B.meta(title='T', sections=['A'], **meta)
    B.titleslide()
    B.section(1)
    B.onecol('First', '<p>plain</p>')
    B.onecol('Math', body)
    out = os.path.join(tempfile.mkdtemp(), 'deck.html')
    B.build('deck', out=out, embed_fonts=False)
    with open(out, encoding='utf-8') as fh:
        return out, fh.read()


class Detect(unittest.TestCase):
    def test_math_is_found(self):
        for s in (r'<p>$x^2$</p>', r'<p>\(x\)</p>', r'$$a=b$$', r'\[a=b\]', r'<li>cost $c_{\max}$, then</li>'):
            self.assertTrue(B.has_math(s), s)

    def test_dollars_and_code_are_not_math(self):
        for s in ('<p>costs $5 and $7 more</p>', '<pre>$ python main.py\n$ ls</pre>', '<code>$a$</code>', '<p>a $ b</p>',
                  '<p title="$x$">t</p>'):
            self.assertFalse(B.has_math(s), s)

    def test_mathjax_only_embedded_when_needed(self):
        _, html = deck('<p>no formulas, $5</p>')
        self.assertNotIn('window.MathJax', html)
        self.assertLess(len(html), 500_000)
        _, html = deck(r'<p>$x^2$</p>')
        self.assertIn('window.MathJax', html)
        _, html = deck(r'<p>$x^2$</p>', math=False)
        self.assertNotIn('window.MathJax', html)
        _, html = deck('<p>none</p>', math=True)
        self.assertIn('window.MathJax', html)

    def test_formula_counts_as_one_word(self):
        import warnings
        tex = r'\[ \hat y_{t+1} = \alpha y_t + (1 - \alpha) \hat y_t + ' + ' + '.join(f'x_{i}' for i in range(80)) + r' \]'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            deck('<p>short text</p>' + tex)
        self.assertFalse([x for x in w if 'words in the body' in str(x.message)])

    def test_macros(self):
        self.assertEqual(B.mathjax_macros({'E': r'\mathbb{E}', r'\norm': r'\lVert #1 \rVert', 'c': r'\textcolor{##1B3A8C}{#1}'}),
                         {'E': r'\mathbb{E}', 'norm': [r'\lVert #1 \rVert', 1], 'c': [r'\textcolor{##1B3A8C}{#1}', 1]})
        with self.assertRaises(ValueError):
            B.mathjax_macros({'a1': 'x'})


@unittest.skipUnless(sync_playwright, 'playwright not installed')
class Browser(unittest.TestCase):
    def test_typesets_offline_on_hidden_slides(self):
        out, _ = deck(r'<p>Risk $\E[x] \le \norm{w}$</p>\[ \hat\beta = \arg\min_\beta \norm{y - X\beta}^2 \]',
                      macros={'E': r'\mathbb{E}', 'norm': r'\lVert #1 \rVert'})
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_context(offline=True).new_page()
            page.goto('file://' + out)
            page.wait_for_function('window.D3_MATH_READY === true', timeout=30000)
            r = page.evaluate("""() => { const s = document.querySelectorAll('.sl')[3];
              return {on: s.classList.contains('on'), n: s.querySelectorAll('mjx-container svg').length,
                      err: document.querySelectorAll('[data-mjx-error]').length, raw: /\\\\norm|\\$/.test(s.innerText)}; }""")
            self.assertEqual(r, {'on': False, 'n': 2, 'err': 0, 'raw': False})
            page.evaluate('show(3, 0)')
            h = page.evaluate("document.querySelector('.sl.on mjx-container svg').getBoundingClientRect().height")
            self.assertGreater(h, 8)
            b.close()

    def test_shoot_reports_broken_formula(self):
        out, _ = deck(r'<p>$\frac{a}$ and $\nosuchcommand$</p>')
        r = subprocess.run([sys.executable, os.path.join(HERE, 'd3deck', 'shoot.py'), out, '--out', tempfile.mkdtemp()],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('MATH: 2 formula(s)', r.stdout)
        self.assertIn('Undefined control sequence', r.stdout)


if __name__ == '__main__':
    unittest.main()
