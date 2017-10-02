import requests
import time


# noinspection PyBroadException
def archive(url):
    """
    Archives to archive.org. The website gives a 403 Forbidden when the
    archive cannot be generated (because it follows robots.txt rules)
    """
    try:
        requests.get('https://web.archive.org/save/' + url)
    except BaseException as e:
        return 'Archiving error or invalid URL.'
    date = time.strftime('%Y%m%d%H%M%S', time.gmtime())

    return 'https://web.archive.org/' + date + '/' + url
