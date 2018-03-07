from html import unescape
from random import randrange
from time import monotonic

import requests

URL = 'https://xkcd.com/{num}/info.0.json'


class Xkcd:
    def __init__(self):
        self._num_comics = None
        self._num_comics_creation = 0

    def latest(self):
        return self.comic('')

    def comic(self, num):
        resp = requests.get(URL.format(num=num))
        if resp.status_code != 200:
            raise XkcdError('Could not get comic with id {!r}.'.format(num))
        return Comic(resp.json())

    def random(self):
        if not self._num_comics or self._num_comics_creation + 60 * 60 < monotonic():  # hour-long cache
            self._num_comics = self.latest().num
            self._num_comics_creation = monotonic()
        comic = None
        while not comic:
            num = randrange(1, self._num_comics)
            try:
                comic = self.comic(num)
            except XkcdError:
                # invalid number, like 404
                pass
        return comic


# copied from https://github.com/MitalAshok/xxkcd/blob/95860ef5fed661abbffe74f936f99158807188a3/xxkcd/xkcd.py#L31-L52
# (MIT licensed)
def magic_decode(s):
    if not isinstance(s, str):
        return s
    for _ in range(10):
        try:
            s = bytearray(map(ord, s)).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            break
    return unescape(s)


class Comic:
    def __init__(self, data):
        self.num = data.pop('num')
        self.title = magic_decode(data.pop('title'))
        self.img = magic_decode(data.pop('img'))
        self.alt = magic_decode(data.pop('alt'))

        for key, value in data.items():
            setattr(self, key, magic_decode(value))

    def __repr__(self):
        return '<Comic {}>'.format(self.num)

    def __str__(self):
        return self.title


class XkcdError(ValueError):
    pass
