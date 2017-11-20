import html

import feedparser


def get_submitted(db):
    table = db['xkcd']
    return [c['comic_id'] for c in table]


def check_update(db):
    new_comic = get_newest_comic()
    submitted = get_submitted(db)
    if new_comic['id'] not in submitted:
        data_1 = {'chat_id': None,
                  'photo': new_comic['img_url']}
        text = new_comic['title']
        if len(text) >= 200:
            text = text[:199] + '…'
        data_1['caption'] = text

        data_2 = {'chat_id': None,
                  'text': new_comic['alt_text'], }

        table = db['xkcd']
        table.insert(dict(comic_id=new_comic['id']))

        return data_1, data_2

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
