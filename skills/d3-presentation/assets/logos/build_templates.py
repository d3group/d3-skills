"""
Rebuild the D3 Beamer slide/title template PDFs with SHARP logos.

The shipped templates baked the University of Wuerzburg logo and the D3
"DATA DRIVEN DECISIONS" logo in as low-res raster bitmaps (Uni: 396x174 JPEG;
D3: 346x69 PNG), so they blurred when projected/scaled. This script keeps the
original template artwork (navy bars, watermark, footer) but masks the old
logos with white and overlays TRUE VECTOR replacements at the EXACT same
rectangles:

  * Uni logo  -> logos/logo-uni.pdf   (VECTOR; from Universitaet_Wuerzburg_Logo.svg via svglib)
  * D3 logo   -> logos/logo-d3.pdf    (VECTOR; from DataDrivenDecisions_2c.svg via svglib)

Both logos are placed with show_pdf_page(), so they stay vector in the output.
Both sit on white in both templates, so the white masks are invisible.

Logo rectangles (page = 959.76 x 540 pt, top-left origin) were measured from the
originals with PyMuPDF get_image_info().

Run:  uv run --with pymupdf python build_templates.py
Outputs overwrite ../latex/Slide_template.pdf and ../latex/Title_template.pdf.
"""
import fitz
import os

HERE = os.path.dirname(os.path.abspath(__file__))   # .../assets/logos
ASSETS = os.path.join(os.path.dirname(HERE), "latex")   # .../assets/latex

UNI_PDF = os.path.join(HERE, "logo-uni.pdf")
D3_PDF = os.path.join(HERE, "logo-d3.pdf")

JOBS = {
    "Slide_template": {
        "orig": os.path.join(HERE, "Slide_template_orig.pdf"),
        "uni": fitz.Rect(33.8, 40.3, 163.4, 97.2),
        "d3": fitz.Rect(790.6, 503.4, 903.6, 526.5),
    },
    "Title_template": {
        "orig": os.path.join(HERE, "Title_template_orig.pdf"),
        "uni": fitz.Rect(33.8, 40.3, 163.4, 97.2),
        "d3": fitz.Rect(715.7, 45.4, 931.7, 88.6),
    },
}


def composite(name, job):
    doc = fitz.open(job["orig"])
    pg = doc[0]
    # 1) mask the old (blurry) logos with white, expanded a little to swallow
    #    JPEG halos / anti-aliased fringes (both logos sit on white here).
    for key, margin in (("uni", 3), ("d3", 2)):
        r = job[key] + (-margin, -margin, margin, margin)
        pg.draw_rect(r, color=(1, 1, 1), fill=(1, 1, 1), width=0)
    # 2) sharp logos, BOTH kept VECTOR via show_pdf_page (aspect preserved/centered)
    with fitz.open(UNI_PDF) as uni, fitz.open(D3_PDF) as d3:
        pg.show_pdf_page(job["uni"], uni, 0, keep_proportion=True)
        pg.show_pdf_page(job["d3"], d3, 0, keep_proportion=True)
    out = os.path.join(ASSETS, name + ".pdf")
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print("wrote", out)


if __name__ == "__main__":
    for name, job in JOBS.items():
        composite(name, job)
