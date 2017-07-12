import json
import os

import praw
import prawcore

import config
import helpers


reddit = praw.Reddit(config.reddit_username, user_agent='%s Telegram bot' % config.reddit_username)
reddit_posts_dict = dict()
redditposts_path = os.path.join(helpers.folder_path(), 'data', 'redditlimit.json')
try:
    with open(redditposts_path, 'r') as f:
        reddit_limits_dict = json.load(f)
except FileNotFoundError:
    reddit_limits_dict = dict()


def hot_posts(subreddit, number, *, guessing_game=False):
    if number < 1:
        raise ValueError('More than 0 posts must be requested.')

    sub = reddit.subreddit(subreddit)

    try:
        sub.fullname
    except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError, TypeError,
            AssertionError):
        return 'Error. Could not access r/%s.' % subreddit, None

    if guessing_game:
        body = 'Hot posts from a random subreddit. Take a guess!\n\n'
    else:
        body = 'Hot posts from %s:\n\n' % sub.display_name_prefixed

    posts_dict = dict()
    n = 1

    for submission in sub.hot(limit=number + 5):
        while len(posts_dict) < number:
            if not submission.stickied:
                body += '#%d: %s - %s\n' % (n, submission.title, submission.shortlink)
                posts_dict[n] = submission.shortlink
                n += 1

    return body, posts_dict


def post_proxy(link, chat_type, chat_id, tg):
    TEXT = 10
    PICTURE = 20
    VIDEO = 30

    def proxy_helper(link, chat_type, chat_id):

        try:
            post = reddit.submission(url=link)
        except praw.exceptions.ClientException:
            data = {'text': 'Invalid URL. URL should be a reddit shortlink.',
                    'chat_id': chat_id}
            response_type = TEXT

            return data, response_type

        try:
            output = post.title + ' (' + post.subreddit_name_prefixed + ')'
        except prawcore.Forbidden:
            data = {'text': 'Reddit post: access denied.',
                    'chat_id': chat_id}
            response_type = TEXT

            return data, response_type

        if post.over_18 and chat_type != 'private':
            data = {'text': 'NSFW. Click it yourself.',
                    'chat_id': chat_id}
            response_type = TEXT

            return data, response_type

        if post.is_self:
            output += '\n\n---\n\n' + post.selftext

            data = {'text': output,
                    'chat_id': chat_id}
            response_type = TEXT

            return data, response_type

        elif post.url[:17] in ['https://i.redd.it', 'http://i.redd.it/']:
            data = {'chat_id': chat_id,
                    'photo': post.url,
                    'caption': output}
            response_type = PICTURE

            return data, response_type

        elif post.url[:17] in ['https://v.redd.it', 'http://v.redd.it/']:
            response_type = VIDEO
            data = {'chat_id': chat_id}
            if post.media['reddit_video']['is_gif']:
                data['video'] = post.media['reddit_video']['fallback_url']
                data['caption'] = output[:200]
            else:
                data['video'] = post.media['reddit_video']['scrubber_media_url']
                data['caption'] = (output + ' Silent preview. Full video available at %s' % post.url)[:200]

            return data, response_type
        else:
            response_type = TEXT
            output += '\n\n' + post.url
            data = {'text': output,
                    'chat_id': chat_id}
            return data, response_type

    data_, response_type_ = proxy_helper(link, chat_type, chat_id)
    if response_type_ == TEXT:
        tg.send_message(data_)
    elif response_type_ == PICTURE:
        tg.send_photo(data_)
    elif response_type_ == VIDEO:
        tg.send_video(data_)


def add_posts_to_dict(chat_id, posts):
    global reddit_posts_dict
    reddit_posts_dict[chat_id] = posts


def get_post_from_dict(chat_id, post_id):
    section = reddit_posts_dict.get(chat_id, None)
    if section is None:
        return False, None
    else:
        post_url = section.get(post_id, None)
        if post_url is None:
            return True, None
        else:
            return True, post_url


def set_redditposts_limit(user_id, limit):
    global reddit_limits_dict
    reddit_limits_dict[str(user_id)] = limit
    with open(redditposts_path, 'w') as fi:
        json.dump(reddit_limits_dict, fi)


def get_redditposts_limit(user_id):
    return reddit_limits_dict.setdefault(str(user_id), 5)
