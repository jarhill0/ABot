import hacker_news

hn = hacker_news.HackerNews()
table = None
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def ask(limit, db, chat_id):
    return _listing_helper(hn.ask, limit, db, chat_id)


def best(limit, db, chat_id):
    return _listing_helper(hn.best, limit, db, chat_id)


def new(limit, db, chat_id):
    return _listing_helper(hn.new, limit, db, chat_id)


def show(limit, db, chat_id):
    return _listing_helper(hn.show, limit, db, chat_id)


def top(limit, db, chat_id):
    return _listing_helper(hn.top, limit, db, chat_id)


def view(item_id=None, item_obj=None, item_letter=None, *args, chat_id=None, db=None, comm_link_parent=True):
    """Returns an HTML string of the item"""
    if item_id is not None:
        item = hn.item(item_id)
    elif item_letter is not None:
        ensure_table(db)
        item = get_posts(chat_id)[item_letter]
        if item is None:
            return 'Invalid reference.'
    else:
        item = item_obj

    if isinstance(item, hacker_news.Poll):
        options = '\n'.join('(+{}) {}'.format(o.score, o.text.replace('<p>', '\n')) for o in item.parts())
        return '<a href="{}">{}</a> (+{})\n' \
               '{}\nOptions:\n{}'.format(item.title,
                                         item.link,
                                         item.score,
                                         item.text,
                                         options)

    if isinstance(item, hacker_news.PollOpt):
        poll = item.poll
        return 'Option (+{}) {} from <a href="{}">{}</a>'.format(item.score, item.text.replace('<p>', '\n'),
                                                                 poll.title, poll.link)

    if isinstance(item, hacker_news.Comment):
        main = '^ <a href="{}">{}</a> [-]\n{}'.format(item.link, item.by, item.text.replace('<p>', '\n'))
        if comm_link_parent:
            main += '\nReply to: {}'.format(item.parent.link)
        return main

    if isinstance(item, (hacker_news.Story, hacker_news.Job)):
        return '(+{}) <a href="{}">{}</a>\n{}'.format(item.score, item.link, item.title,
                                                      item.content.replace('<p>', '\n'))

    return item.link


def replies(limit, item_id=None, item_letter=None, chat_id=None, db=None):
    """View replied to an item"""
    limit = _constrain(limit)

    if item_id is None:
        ensure_table(db)
        item_id = get_posts(chat_id)[item_letter.upper()]
        if item_id == -1:
            return 'Invalid reference.'

    item = hn.item(item_id)
    children = []
    for i, kid in enumerate(item.kids()):
        if i >= limit:
            break
        children.append(view(item_obj=kid, comm_link_parent=False))
    return '\n\n'.join(children)


def ensure_table(db):
    global table
    if table is None and db is not None:
        table = db['hn']


def store_posts(posts, chat_id):
    posts['chat'] = str(chat_id)
    table.upsert(posts, ['chat'])


def get_posts(chat_id):
    return table.find_one(chat=chat_id)


def _constrain(limit):
    """Force a limit to be within a certain range."""
    return max(1, min(25, limit))


def _listing_helper(listing, limit, db, chat_id):
    limit = _constrain(limit)
    text = []

    posts = {l: -1 for l in ALPHABET}
    ensure_table(db)

    for n, post in enumerate(listing(limit)):
        text.append('#{} [{}]({}) (+{})'.format(ALPHABET[n], post.title, post.link, post.score))
        posts[ALPHABET[n]] = post.id
    store_posts(posts, chat_id)

    return '\n'.join(text)
