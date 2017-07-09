import re

import requests


def upload(url):
    response = requests.post("http://archive.is/submit/", {'url': url}, verify=False)
    found = re.findall("http[s]?://archive.is/[0-z]{1,6}", response.text)[0]
    return found


def archive_message(url):
    if url is not None and type(url) is str:
        try:
            arc_url = upload(url)
        except:
            return 'Archiving error or invalid URL.'
        else:
            if arc_url is not None:
                return arc_url
    return 'Command must be followed with a space and then a valid URL.'
