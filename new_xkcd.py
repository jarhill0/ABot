import html

import feedparser

from db_handler import db


def get_submitted():
    table = db['xkcd']
    if table.count() == 0:
        table.insert(dict(comic_id=0))
    return [c['comic_id'] for c in table]


def check_update():
    new_comic = get_newest_comic()
    submitted = get_submitted()
    if new_comic['id'] not in submitted:
        text = new_comic['title']
        if len(text) > 200:
            text = text[:199] + '…'

        pic = (new_comic['img_url'], text)
        alt_text = new_comic['alt_text']

        table = db['xkcd']
        table.insert(dict(comic_id=new_comic['id']))

        return pic, alt_text

    else:
        return None


def get_newest_comic():
    feed = feedparser.parse('https://xkcd.com/rss.xml')
    output = {'id': feed['entries'][0]['id'], 'title': feed['entries'][0]['title']}

    summary = feed['entries'][0]['summary']
    img_url = summary[summary.index('<img src="') + 10:]
    output['img_url'] = img_url[:img_url.index('"')]

    alt_text = summary[summary.index(' alt="') + 6:]
    output['alt_text'] = html.unescape(alt_text[:alt_text.index('"')])

    return output
