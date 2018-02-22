import re

import requests

HEADERS = {'User-Agent': 'Telegram Bot (https://github.com/jarhill0/abot)'}


def upload(url):
    response = requests.post("http://archive.is/submit/", {'url': url}, headers=HEADERS)
    found = re.findall("http[s]?://archive.is/[0-z]{1,6}", response.text)[0]
    return found


# noinspection PyBroadException
def archive_message(url):
    try:
        arc_url = upload(url)
    except Exception:
        return 'Archiving error or invalid URL.'
    else:
        if arc_url is not None:
            return arc_url
