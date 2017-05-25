import json

import feedparser

import config


def get_submitted():
    with open('data/xkcd.json', 'r') as f:
        submitted = json.load(f)
    return submitted


def check_update():
    new_comic = get_newest_comic()
    submitted = get_submitted()
    if new_comic['id'] not in submitted:
        data_1 = {'chat_id': config.a_group_id,
                  'photo': new_comic['img_url'],
                  }
        text = new_comic['title']
        if len(text) >= 200:
            text = text[:199] + '…'
        data_1['caption'] = text

        data_2 = {'chat_id': config.a_group_id,
                  'text': new_comic['alt_text'], }

        submitted.append(new_comic['id'])

        with open('data/xkcd.json', 'w') as f:
            json.dump(submitted, f)

        return (data_1, data_2)

    else:
        return None


def get_newest_comic():
    feed = feedparser.parse('https://xkcd.com/rss.xml')
    output = {'id': feed['entries'][0]['id'], }

    output['title'] = feed['entries'][0]['title']

    summary = feed['entries'][0]['summary']
    img_url = summary[summary.index('<img src="') + 10:]
    output['img_url'] = img_url[:img_url.index('"')]

    alt_text = summary[summary.index(' alt="') + 6:]
    output['alt_text'] = alt_text[:alt_text.index('"')]

    return output


if __name__ == '__main__':
    check_update()
