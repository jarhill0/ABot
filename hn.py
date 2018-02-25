import hnpy

from html_janitor import Cleaner

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class HN:
    def __init__(self, db):
        self.hn = hnpy.HackerNews()
        self.table = db['hn']

    def ask(self, limit, chat_id):
        return self._listing_helper(self.hn.ask, limit, chat_id)

    def best(self, limit, chat_id):
        return self._listing_helper(self.hn.best, limit, chat_id)

    def new(self, limit, chat_id):
        return self._listing_helper(self.hn.new, limit, chat_id)

    def show(self, limit, chat_id):
        return self._listing_helper(self.hn.show, limit, chat_id)

    def top(self, limit, chat_id):
        return self._listing_helper(self.hn.top, limit, chat_id)

    def view(self, item_id=None, item_obj=None, item_letter=None, *args, chat_id=None, comm_link_parent=True):
        """Returns an HTML string of the item. item_obj overrides item_id, which in turn overrides item_letter"""
        if item_letter is not None:
            item_id = self.get_posts(chat_id)[item_letter.upper()]
            if item_id is -1:
                return 'Invalid reference.'
        if item_id is not None:
            item = self.hn.item(item_id)
        else:
            item = item_obj

        if item.type == 'poll':
            options = '\n'.join('(+{}) {}'.format(o.score, o.text.replace('<p>', '\n')) for o in item.parts())
            return '<a href="{}">{}</a> (+{})\n' \
                   '{}\nOptions:\n{}'.format(item.title,
                                             item.link,
                                             item.score,
                                             Cleaner.clean(item.text) if hasattr(item, 'text') else '',
                                             options)

        if item.type == 'pollopt':
            poll = item.poll
            return 'Option (+{}) {} from <a href="{}">{}</a>'.format(item.score,
                                                                     Cleaner.clean(item.text.replace('<p>', '\n')),
                                                                     poll.title, poll.link)

        if item.type == 'comment':
            main = '^ <a href="{}">{}</a> [-]\n{}'.format(item.link, item.by.name,
                                                          Cleaner.clean(item.text.replace('<p>', '\n')))
            if comm_link_parent:
                main += '\nReply to: {}'.format(item.parent.link)
            return main

        if item.type in ('story', 'job'):
            return '(+{}) <a href="{}">{}</a>\n{}'.format(item.score, item.link, item.title,
                                                          item.content.replace('<p>', '\n'))

        return item.link

    def replies(self, limit, item_id=None, item_letter=None, chat_id=None):
        """View replied to an item"""
        limit = self._constrain(limit)

        if item_id is None:
            item_id = self.get_posts(chat_id)[item_letter.upper()]
            if item_id == -1:
                return 'Invalid reference.'

        item = self.hn.item(item_id)
        children = []
        for kid in item.kids(limit=limit):
            children.append(self.view(item_obj=kid, comm_link_parent=False))
        return '\n\n'.join(children)

    def store_posts(self, posts, chat_id):
        posts['chat'] = str(chat_id)
        self.table.upsert(posts, ['chat'])

    def get_posts(self, chat_id):
        return self.table.find_one(chat=chat_id)

    @staticmethod
    def _constrain(limit):
        """Force a limit to be within a certain range."""
        return max(1, min(25, limit))

    def _listing_helper(self, listing, limit, chat_id):
        limit = self._constrain(limit)
        text = []

        posts = {l: -1 for l in ALPHABET}

        for n, post in enumerate(listing(limit)):
            text.append('**{}**: [{}]({}) (+{})'.format(ALPHABET[n], post.title, post.link, post.score))
            posts[ALPHABET[n]] = post.id
        self.store_posts(posts, chat_id)

        return '\n'.join(text)
