import requests
from pawt.models.reply_markup import InlineKeyboardMarkupBuilder

import config


def get_nth_result(query, n=0):
    """Get the nth result for a query, where n=0 is the first result.

    Returns None if the index is out of range or there is no result, or if there isn't proper authentication.
    """
    if not config.yt_token:
        return None
    if n + 1 > 50:  # limit (technically we can make multiple paged requests, but we're not doing that)
        return None
    if not query:
        return None
    response = requests.get('https://www.googleapis.com/youtube/v3/search',
                            params={
                                'key': config.yt_token,
                                'type': 'video',
                                'part': 'snippet',
                                'maxResults': n + 1,
                                'q': query,
                            })
    if response.status_code != 200:
        return None
    items = response.json()['items']
    if len(items) <= n:  # not enough results
        return None
    video = items[n]
    return 'https://www.youtube.com/watch?v={}'.format(video['id']['videoId'])


def get_reply_markup(chat_id, query, n):
    builder = InlineKeyboardMarkupBuilder()
    builder.add_button('Next result', callback_data='yt:{}:{}:{}'.format(chat_id, n, query))
    return builder.build()
