from random import choice

from .const import INSPIRATIONS, JOINERS, MARKETS


def generate():
    words = []
    inspiration = choice(INSPIRATIONS)
    joiner = choice(JOINERS)
    if joiner in ('of',):
        words.append('the')
    market = choice(MARKETS)
    words += [inspiration, joiner, market]
    return 'New startup idea: {}!'.format(' '.join(words))
