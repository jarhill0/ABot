from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = ('b', 'strong', 'i', 'em', 'a', 'code', 'pre')


class Cleaner(HTMLParser):
    @classmethod
    def clean(cls, text):
        cleaner = cls()
        cleaner.feed(text)
        cleaner.close()
        return cleaner.text

    @property
    def level(self):
        return len(self._tag_path)

    @property
    def text(self):
        return ''.join(self._text_parts)

    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self._tag_path = []
        self._text_parts = []

    def handle_starttag(self, tag, attrs):
        # if tag not in ALLOWED_TAGS:
        #     return

        self._tag_path.append(tag)

        if self.level <= 1:  # it will only ever be one, not zero, but this reads more nicely
            items = [tag] + ['{}={!r}'.format(a[0], a[1]) for a in attrs]
            self._text_parts.append('<{}>'.format(' '.join(items)))

    def handle_endtag(self, tag):
        # if tag not in ALLOWED_TAGS:
        #     return

        if self._tag_path[-1] != tag:
            raise ValidationError('Mismatched tags.')

        if self.level <= 1:  # it will only ever be one, not zero, but this reads more nicely
            self._text_parts.append('</{}>'.format(tag))

        del self._tag_path[-1]

    def handle_data(self, data):
        self._text_parts.append(escape(data))


class ValidationError(ValueError):
    pass
