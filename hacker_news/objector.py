from .const import ITEM_BASE_URL


class Attributes:
    """A class to hold attributes returned by the API."""

    def __getattr__(self, item):
        return None


class Item:
    """Base class for all items."""

    def __init__(self, data, hn):
        self._hn = hn
        self._data = data

        self.id = data['id']
        self.deleted = data.get('deleted', False)
        self.dead = data.get('dead', False)

        self.attrs = Attributes()
        for key, value in data.items():
            setattr(self.attrs, key, value)

        self._kids = data.get('kids', [])

    def __repr__(self):
        return '{} with ID {}.'.format(self.__class__.__name__, self.id)

    def kids(self):
        for id_ in self._kids:
            yield self._hn.item(id_)

    @property
    def link(self):
        """Get a link to the item on HN."""
        return ITEM_BASE_URL.format(id=self.id)

    @property
    def content(self):
        """Attempt to find and return the relevant content from any type of item."""
        if isinstance(self, Text) and self.text is not None:
            return self.text
        if isinstance(self, Linkable) and self.url is not None:
            return self.url
        return ''

    @property
    def time(self):
        return self.attrs.time


class Authorable:
    @property
    def by(self):
        return self.attrs.by


class Parentable:
    @property
    def parent(self):
        return self._hn.item(self.attrs.parent)


class Text:
    @property
    def text(self):
        if self.deleted:
            return '[deleted]'
        return self.attrs.text

    def __str__(self):
        return self.text


class Linkable:
    @property
    def url(self):
        return self.attrs.url


class WithDescendants:
    @property
    def descendants(self):
        return self.attrs.descendants


class Titled:
    @property
    def title(self):
        return self.attrs.title if not self.deleted else '[deleted]'

    def __str__(self):
        return self.title


class Scoreable:
    @property
    def score(self):
        return self.attrs.score if self.attrs.score else 0


class Comment(Item, Authorable, Parentable, Text):
    """A Hacker News Comment. May be deleted."""
    pass


class Story(Item, Authorable, Titled, WithDescendants, Scoreable):
    """A Hacker News story. May be deleted."""
    pass


class AskStory(Story, Text):
    """An 'Ask HN:' post. May be deleted."""
    pass


class LinkStory(Story, Linkable):
    """A normal HN post or a 'Show HN:' post. May be deleted."""
    pass


class Job(Item, Authorable, Titled, Scoreable, Linkable, Text):
    """A HN job. May be deleted."""
    pass


class Poll(Item, Authorable, WithDescendants, Scoreable, Titled, Text):
    """A HN poll. May be deleted."""

    def parts(self):
        options = [self._hn.item(part) for part in self.attrs.parts]
        options.sort()
        return iter(options)


class PollOpt(Item, Authorable, Scoreable, Text):
    """An option in a HN poll. Unknown if it may be deleted."""

    @property
    def poll(self):
        """Find the poll this item this belongs to."""
        return self._hn.item(self.attrs.poll)


def objectify(data, hn):
    kind = data.get('type', None)
    if kind == 'comment':
        return Comment(data, hn)

    if kind == 'story':
        if 'url' in data.keys():
            return LinkStory(data, hn)
        if 'text' in data.keys():
            return AskStory(data, hn)
        return Story(data, hn)

    if kind == 'job':
        return Job(data, hn)

    if kind == 'poll':
        return Poll(data, hn)

    if kind == 'pollopt':
        return PollOpt(data, hn)

    return Item(data, hn)
