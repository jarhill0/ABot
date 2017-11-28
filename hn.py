import hacker_news

hn = hacker_news.HackerNews()


def ask(limit):
    return _listing_helper(hn.ask, limit)


def best(limit):
    return _listing_helper(hn.best, limit)


def new(limit):
    return _listing_helper(hn.new, limit)


def show(limit):
    return _listing_helper(hn.show, limit)


def top(limit):
    return _listing_helper(hn.top, limit)


def view(item_id=None, item_obj=None):
    """Returns an HTML string of the item"""
    if item_id is not None:
        item = hn.item(item_id)
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
        return '^ {} [-]\n{}\nReply to: {}'.format(item.by, item.text.replace('<p>', '\n'), item.parent.link)

    if isinstance(item, (hacker_news.Story, hacker_news.Job)):
        return '(+{}) <a href="{}">{}</a>\n{}'.format(item.score, item.link, item.title,
                                                      item.content.replace('<p>', '\n'))

    return item.link


def replies(item_id, limit):
    """View replied to an item"""
    limit = _constrain(limit)
    item = hn.item(item_id)
    children = []
    for i, kid in enumerate(item.kids()):
        if i >= limit:
            break
        children.append(view(item_obj=kid))
    return '\n\n'.join(children)


def _constrain(limit):
    """Force a limit to be within a certain range."""
    return max(1, min(25, limit))


def _listing_helper(listing, limit):
    limit = _constrain(limit)
    text = []
    for n, post in enumerate(listing(limit)):
        text.append('[{}]({}) (+{})'.format(post.title, post.link, post.score))
    return '\n'.join(text)
