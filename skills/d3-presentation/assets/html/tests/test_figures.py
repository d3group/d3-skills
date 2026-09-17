import base64, os, struct, sys, tempfile, unittest, zlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from d3deck import figures, paths


def png_bytes(w, h):
    raw = b''.join(b'\x00' + b'\xff\x00\x00' * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def jpeg_bytes(w, h):
    sof = b'\xff\xc0' + struct.pack('>H', 11) + b'\x08' + struct.pack('>HH', h, w) + b'\x01' + b'\x01\x11\x00'
    return b'\xff\xd8' + sof + b'\xff\xd9'


class Sizes(unittest.TestCase):
    def test_png(self):
        self.assertEqual(figures.image_size(png_bytes(3, 2), 'png'), (3, 2))

    def test_jpeg(self):
        self.assertEqual(figures.image_size(jpeg_bytes(640, 480), 'jpg'), (640, 480))

    def test_svg_viewbox(self):
        self.assertEqual(figures.image_size(b'<svg xmlns="x" viewBox="0 0 40 20"></svg>', 'svg'), (40.0, 20.0))

    def test_svg_width_height(self):
        self.assertEqual(figures.image_size(b'<svg width="30" height="10"></svg>', 'svg'), (30.0, 10.0))

    def test_bad(self):
        with self.assertRaises(ValueError):
            figures.image_size(b'nope', 'png')

    def test_svg_without_size(self):
        with self.assertRaises(ValueError):
            figures.image_size(b'<svg xmlns="x"></svg>', 'svg')


class Loading(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, 'plot.png'), 'wb') as fh:
            fh.write(png_bytes(4, 2))
        with open(os.path.join(self.d, 'chart.svg'), 'w') as fh:
            fh.write('<svg viewBox="0 0 8 4"></svg>')

    def test_find_by_stem(self):
        self.assertTrue(figures.find_figure('plot', self.d).endswith('plot.png'))

    def test_find_with_extension(self):
        self.assertTrue(figures.find_figure('chart.svg', self.d).endswith('chart.svg'))

    def test_missing(self):
        with self.assertRaises(FileNotFoundError):
            figures.find_figure('nothing', self.d)

    def test_load_png(self):
        uri, w, h = figures.load('plot', self.d)
        self.assertTrue(uri.startswith('data:image/png;base64,'))
        self.assertEqual((w, h), (4, 2))

    def test_load_svg(self):
        uri, w, h = figures.load('chart', self.d)
        self.assertTrue(uri.startswith('data:image/svg+xml;base64,'))
        self.assertEqual(base64.b64decode(uri.split(',', 1)[1]), b'<svg viewBox="0 0 8 4"></svg>')

    def test_fig_html(self):
        figures.FIG_DIR = self.d
        try:
            h = figures.fig('plot', width='60%', cls='big', alt='a plot')
        finally:
            figures.FIG_DIR = None
        self.assertIn('class="fig big"', h)
        self.assertIn('aspect-ratio:4/2;', h)
        self.assertIn('width:60%;', h)
        self.assertIn('alt="a plot"', h)

    @unittest.skipUnless(figures.shutil.which('pdftoppm'), 'pdftoppm not installed')
    def test_pdf_is_rasterized(self):
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           'latex', 'Slide_template.pdf')
        import shutil
        shutil.copy(src, os.path.join(self.d, 'tpl.pdf'))
        uri, w, h = figures.load('tpl', self.d)
        self.assertTrue(uri.startswith('data:image/png;base64,'))
        self.assertTrue(os.path.exists(os.path.join(self.d, '.cache', 'tpl.png')))
        self.assertAlmostEqual(w / h, 1280 / 720, places=2)


class Paths(unittest.TestCase):
    def test_asset_dirs_resolve_in_skill_layout(self):
        self.assertTrue(os.path.isdir(paths.asset_dir('fonts')))
        self.assertTrue(os.path.isdir(paths.asset_dir('logos')))

    def test_unknown_asset_dir(self):
        with self.assertRaises(FileNotFoundError):
            paths.asset_dir('nothing-here')


if __name__ == '__main__':
    unittest.main()
