from urllib.parse import urlparse

from requests import get


def direct_link(link):
    parsed = urlparse(link)
    if parsed.netloc.lower() == 'i.imgur.com':
        return link
    if parsed.netloc.lower().split('.') == ['gfycat', 'com']:
        gfy_id = parsed.path.rstrip('/').split('/')[-1]
        if '.' not in gfy_id:
            return 'https://thumbs.gfycat.com/{}-size_restricted.gif'.format(gfy_id)
        return None
    if parsed.netloc.lower() not in ('imgur.com', 'www.imgur.com'):
        return None
    if 'a' in parsed.path.split('/'):
        # album, potentially multiple images, hard to know for sure
        return None
    link_id = parsed.path.rstrip('/').split('/')[-1]
    if 'gallery' in parsed.path.split('/'):
        info = get('https://imgur.com/gallery/{}.json'.format(link_id)).json()['data']['image']
        if info['album_images']['count'] != 1:
            # more than one image, return
            return None
        img = info['album_images']['images'][0]
        if img['ext'] in ('.gif', '.gifv'):
            return 'https://i.imgur.com/{}.mp4'.format(img['hash'])
        return 'https://i.imgur.com/{}'.format(img['hash'] + img['ext'])
    return 'https://i.imgur.com/{}.jpg'.format(link_id)
