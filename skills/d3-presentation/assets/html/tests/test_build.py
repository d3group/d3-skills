import os, sys, tempfile, unittest, warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import d3deck
from d3deck import deck as B

SECS = ['Introduction', 'Methodology', 'Results', 'Conclusion']


def small_deck(numbering='all', tracker=False):
    B.meta(title='Title <b>x</b>', subtitle='Sub', presenter='Ada', sections=SECS, numbering=numbering, tracker=tracker)
    B.titleslide()
    B.agenda()
    B.section(1)
    B.onecol('One', '<p>a</p>', steps=3, notes='my secret note', src='summary one')
    B.twocol('Two', 'L', 'R')
    B.thankyou()


class Labels(unittest.TestCase):
    def test_all_mode(self):
        small_deck('all')
        labels = B.page_labels(B.D.slides, 'all', None)
        self.assertEqual(labels, [('', '1 / 6'), ('2/6', '2 / 6'), ('3/6', '3 / 6'), ('4/6', '4 / 6'),
                                  ('5/6', '5 / 6'), ('', '6 / 6')])

    def test_content_mode_with_backup(self):
        small_deck('content')
        B.appendix()
        B.onecol('B1', 'x')
        B.onecol('B2', 'x', num=False)
        B.onecol('B3', 'x')
        labels = B.page_labels(B.D.slides, 'content', B.D.backup_at)
        self.assertEqual(labels[:6], [('', '&mdash; / 2'), ('', '&mdash; / 2'), ('', '&mdash; / 2'),
                                      ('1/2', '1 / 2'), ('2/2', '2 / 2'), ('', '&mdash; / 2')])
        self.assertEqual(labels[6:], [('1/2', 'backup 1 of 2'), ('', 'backup &mdash; of 2'), ('2/2', 'backup 2 of 2')])

    def test_all_mode_backup_foot(self):
        small_deck('all')
        B.appendix()
        B.onecol('B1', 'x')
        labels = B.page_labels(B.D.slides, 'all', B.D.backup_at)
        self.assertEqual(labels[-1], ('7/7', 'backup 1 of 1'))

    def test_all_mode_num_false(self):
        small_deck('all')
        B.onecol('Hidden', 'x', num=False)
        B.appendix()
        B.onecol('B1', 'x', num=False)
        labels = B.page_labels(B.D.slides, 'all', B.D.backup_at)
        self.assertEqual(labels[6], ('', '&mdash; / 6'))
        self.assertEqual(labels[7], ('', 'backup &mdash; of 1'))


class Guards(unittest.TestCase):
    def test_slide_before_meta(self):
        B.D.reset()
        with self.assertRaises(RuntimeError):
            B.onecol('x', 'y')

    def test_section_range(self):
        small_deck()
        with self.assertRaises(ValueError):
            B.section(5)

    def test_section_after_appendix(self):
        small_deck()
        B.appendix()
        with self.assertRaises(ValueError):
            B.section(2)

    def test_duplicate_mark(self):
        small_deck()
        B.mark('x')
        B.onecol('a', 'b')
        with self.assertRaises(ValueError):
            B.mark('x')

    def test_dangling_mark(self):
        small_deck()
        B.mark('late')
        with self.assertRaises(ValueError):
            B.build('t', out=os.path.join(tempfile.mkdtemp(), 't.html'), embed_fonts=False)

    def test_unresolved_jump(self):
        small_deck()
        B.onecol('a', B.link('nowhere', 'go'))
        with self.assertRaises(ValueError) as cm:
            B.build('t', out=os.path.join(tempfile.mkdtemp(), 't.html'), embed_fonts=False)
        self.assertIn('nowhere', str(cm.exception))

    def test_backuphome_needs_appendix(self):
        small_deck()
        with self.assertRaises(ValueError):
            B.backuphome()

    def test_display_none_warns(self):
        small_deck()
        B.onecol('a', '<div style="display: none">x</div>')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            B.build('t', out=os.path.join(tempfile.mkdtemp(), 't.html'), embed_fonts=False)
        self.assertTrue(any('display:none' in str(x.message) for x in w))

    def test_bad_numbering(self):
        with self.assertRaises(ValueError):
            B.meta(title='x', numbering='pages')


class Output(unittest.TestCase):
    def build(self, **kw):
        out = os.path.join(tempfile.mkdtemp(), 'deck.html')
        B.build('deck', out=out, embed_fonts=False, **kw)
        with open(out, encoding='utf-8') as fh:
            return fh.read()

    def test_sections_steps_and_kinds(self):
        small_deck()
        doc = self.build()
        self.assertEqual(doc.count('<section class="sl '), 6)
        self.assertIn('<section class="sl k-content" data-steps="3" data-i="3">', doc)
        self.assertIn('<div class="stepdots"><i></i><i></i><i></i></div>', doc)
        self.assertIn('<title>Title x</title>', doc)

    def test_notes_only_in_manifest(self):
        small_deck()
        doc = self.build()
        self.assertEqual(doc.count('my secret note'), 1)
        body = doc[doc.index('<div id="stage">'):doc.index('<div id="foot">')]
        self.assertNotIn('my secret note', body)

    def test_manifest_escaping(self):
        B.meta(title='T', sections=SECS)
        B.titleslide()
        B.onecol('a', 'b', src='closes </script> early')
        doc = self.build()
        self.assertIn('closes \\u003c/script> early', doc)
        self.assertEqual(doc.count('</script>'), 3)

    def test_marks_and_tabs(self):
        small_deck()
        B.section(3)
        B.mark('deep')
        B.onecol('Deep', 'x')
        B.onecol('Back', B.link('deep', 'to deep') + ' ' + B.link('sec-1', 'intro'))
        B.appendix()
        B.backuphome()
        B.onecol('Extra', 'x', group='Ch. 5')
        doc = self.build()
        self.assertIn('<span class="jl" data-jump="7">to deep</span>', doc)
        self.assertIn('data-jump="2">intro</span>', doc)
        self.assertIn('<button class="jt" data-go="2">Introduction</button>', doc)
        self.assertIn('<button class="jt" data-go="6">Results</button>', doc)
        self.assertNotIn('>Methodology</button>', doc)
        self.assertIn('<button class="jt" data-go="9">Backup</button>', doc)
        self.assertIn('<h4>Ch. 5</h4>', doc)
        self.assertIn('<div class="hi" data-jump="10"><span class="hn">B1</span><span>Extra</span></div>', doc)
        self.assertNotIn('@@', doc)

    def test_agenda_links_only_to_existing_dividers(self):
        small_deck()
        doc = self.build()
        agenda = doc[doc.index('k-agenda'):doc.index('k-section')]
        self.assertEqual(agenda.count('data-jump="2"'), 2)
        self.assertEqual(agenda.count('data-jump='), 2)

    def test_tracker_replaces_footer_on_content_slides(self):
        small_deck(tracker=True)
        doc = self.build()
        one = doc[doc.index('data-i="3"'):doc.index('data-i="4"')]
        self.assertIn('<div class="trk">', one)
        self.assertNotIn('fr-foot', one)
        sec = doc[doc.index('data-i="2"'):doc.index('data-i="3"')]
        self.assertIn('fr-foot', sec)
        self.assertNotIn('class="trk"', sec)

    def test_footer_and_numbers_by_kind(self):
        small_deck()
        doc = self.build()
        title = doc[doc.index('data-i="0"'):doc.index('data-i="1"')]
        self.assertNotIn('fr-num', title)
        self.assertNotIn('fr-foot', title)
        self.assertIn('fr-seal', title)
        two = doc[doc.index('data-i="4"'):doc.index('data-i="5"')]
        self.assertIn('<div class="fr-num">5/6</div>', two)
        self.assertIn('<div class="fr-foot">Chair of Information Systems and Business Analytics | Ada</div>', two)
        self.assertIn('<div class="col l">L</div><div class="col r">R</div>', two)

    def test_takeaway_and_css(self):
        small_deck()
        B.twocoltakeaway('T', 'L', 'R', 'Do this')
        B.css('.mine{color:red}')
        doc = self.build()
        self.assertIn('<div class="col l short">L</div><div class="col r short">R</div><div class="fr-take"><div class="take"><b>Key Takeaway:</b> Do this</div></div>', doc)
        self.assertIn('.mine{color:red}', doc)

    def test_fonts(self):
        with self.assertRaises(FileNotFoundError):
            B.fonts_css(tempfile.mkdtemp())
        css = B.fonts_css()
        self.assertEqual(css.count('@font-face'), 5)
        self.assertIn("font-weight:700;font-style:italic", css)

    def test_public_api(self):
        for name in ('meta', 'titleslide', 'agenda', 'section', 'onecol', 'twocol', 'twocoltakeaway', 'slide',
                     'thankyou', 'appendix', 'backuphome', 'mark', 'jump', 'link', 'css', 'build', 'columnheader',
                     'highlight', 'codebox', 'errorbox', 'terminalbox', 'chevrons', 'timeline', 'takeaway', 'stat',
                     'bignum', 'step', 'scrim', 'crumb', 'fig', 'mix'):
            self.assertTrue(hasattr(d3deck, name), name)
            self.assertIn(name, d3deck.__all__)

    def test_notes_can_be_stripped(self):
        small_deck()
        doc = self.build(notes=False)
        self.assertNotIn('my secret note', doc)

    def test_no_network_references(self):
        small_deck()
        doc = self.build()
        import re
        self.assertEqual(re.findall(r'(?:src|href)="https?://', doc), [])
        self.assertEqual(re.findall(r'url\(\s*["\']?https?://', doc), [])
        self.assertNotIn('@import', doc)


if __name__ == '__main__':
    unittest.main()
