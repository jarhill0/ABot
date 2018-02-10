from xxkcd import xkcd

from db_handler import db


def get_submitted():
    table = db['xkcd']
    if table.count() == 0:
        table.insert(dict(comic_id=0))
    return [c['comic_id'] for c in table]


def check_update():
    new_comic = xkcd(xkcd.latest())
    submitted = get_submitted()
    if new_comic.num not in submitted:
        text = new_comic.title
        if len(text) > 200:
            text = text[:199] + '…'

        pic = (new_comic.img, text)
        alt_text = new_comic.alt

        table = db['xkcd']
        table.insert(dict(comic_id=new_comic.num))

        return pic, alt_text

    else:
        return None
