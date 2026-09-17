# -*- coding: utf-8 -*-
"""d3deck: D3-branded HTML slide decks written as Python.

    from d3deck import *
    meta(title=..., sections=[...]); titleslide(); agenda(); section(1)
    onecol('Action title', '<ul><li>...</li></ul>'); thankyou(); build('my_talk')
"""
from .deck import (K, statement, facts, meta, titleslide, agenda, section, onecol, twocol, twocoltakeaway, slide, thankyou,
                    appendix, backuphome, mark, jump, link, css, build, D)
from .components import (columnheader, highlight, codebox, errorbox, terminalbox, chevrons, timeline,
                         takeaway, stat, bignum, step, scrim, crumb, mix)
from .figures import fig

__all__ = ['K', 'statement', 'facts', 'meta', 'titleslide', 'agenda', 'section', 'onecol', 'twocol', 'twocoltakeaway', 'slide', 'thankyou',
           'appendix', 'backuphome', 'mark', 'jump', 'link', 'css', 'build', 'D',
           'columnheader', 'highlight', 'codebox', 'errorbox', 'terminalbox', 'chevrons', 'timeline',
           'takeaway', 'stat', 'bignum', 'step', 'scrim', 'crumb', 'mix', 'fig']
