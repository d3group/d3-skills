# -*- coding: utf-8 -*-
"""d3deck: D3-branded HTML slide decks written as Python.

    from d3deck import *
    meta(title=..., sections=[...]); titleslide(); section(1, question='...')
    onecol(K('Kicker', 'Action title'), model([...], [...])); thankyou(); build('my_talk')
"""
from .deck import (K, statement, facts, meta, titleslide, agenda, section, onecol, twocol, twocoltakeaway, slide, thankyou,
                    appendix, backuphome, mark, jump, link, css, js, build, D)
from .components import (columnheader, highlight, codebox, errorbox, terminalbox, chevrons, timeline,
                         takeaway, stat, bignum, step, scrim, crumb, mix)
from .figures import fig
from .kit import (icon, tile, well, middle, callout, chip, sign_badge, badge, stamp, legend, pop, cite, nocaps, count, bar, bars,
                  effect, gauge, units, bub, line, proof, brace, versus, selector, flag, chat, milestones, countdown,
                  node, edge, model, slider, readout, lab)

__all__ = ['K', 'statement', 'facts', 'meta', 'titleslide', 'agenda', 'section', 'onecol', 'twocol', 'twocoltakeaway', 'slide', 'thankyou',
           'appendix', 'backuphome', 'mark', 'jump', 'link', 'css', 'js', 'build', 'D',
           'columnheader', 'highlight', 'codebox', 'errorbox', 'terminalbox', 'chevrons', 'timeline',
           'takeaway', 'stat', 'bignum', 'step', 'scrim', 'crumb', 'mix', 'fig',
           'icon', 'tile', 'well', 'middle', 'callout', 'chip', 'sign_badge', 'badge', 'stamp', 'legend', 'pop', 'cite', 'nocaps',
           'count', 'bar', 'bars', 'effect', 'gauge', 'units', 'bub', 'line', 'proof', 'brace', 'versus', 'selector',
           'flag', 'chat', 'milestones', 'countdown', 'node', 'edge', 'model', 'slider', 'readout', 'lab']
