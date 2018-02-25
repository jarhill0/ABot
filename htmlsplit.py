from html.parser import HTMLParser


class HTMLsplit(HTMLParser):
    @property
    def can_split(self):
        return not self._tag_path

    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)

        self._tag_path = []

    def handle_starttag(self, tag, attrs):
        self._tag_path.append(tag)

    def handle_endtag(self, tag):
        assert self._tag_path[-1] == tag, "Mismatched tags"
        del self._tag_path[-1]
