# -*- coding: utf-8 -*-
"""Where things are.

A talk folder holds slides.py next to a copied d3deck/ package that carries
fonts/ and logos/. Inside the skill repository the package has no such
subfolders; there the shared assets/fonts and assets/logos two levels up are
used, which is what lets example-slides.py build from the skill itself.
"""
import os
import sys

PKG = os.path.dirname(os.path.abspath(__file__))


def talk_dir():
    """Directory of the script being run (slides.py), or the cwd as a fallback."""
    main = sys.modules.get('__main__')
    f = getattr(main, '__file__', None)
    return os.path.dirname(os.path.abspath(f)) if f else os.getcwd()


def asset_dir(kind):
    """Folder for 'fonts' or 'logos': d3deck/<kind>, else the skill's assets/<kind>."""
    candidates = (os.path.join(PKG, kind),
                  os.path.normpath(os.path.join(PKG, '..', '..', kind)))
    for c in candidates:
        if os.path.isdir(c):
            return c
    raise FileNotFoundError(
        f'{kind}/ not found next to d3deck (looked in {candidates}); run init.py to scaffold a talk folder')
