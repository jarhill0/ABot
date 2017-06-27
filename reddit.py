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


def hot_posts(subreddit, number):
    if number < 1:
        raise ValueError('More than 0 posts must be requested.')
    try:
        reddit.subreddit(subreddit).fullname
    except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError, TypeError,
            AssertionError):
        return 'Error. Could not access r/%s.' % subreddit, None

    sub = reddit.subreddit(subreddit)

    body = 'Hot posts from %s:\n\n' % sub.display_name_prefixed
    num = 1
    num_stickies = 0

    for i in range(1, 3):
        try:
            reddit.subreddit(subreddit).sticky(number=i)
        except prawcore.NotFound:
            pass
        else:
            num_stickies = i

    posts_dict = dict()
    for true_count, submission in enumerate(sub.hot(limit=number + num_stickies)):
        if true_count >= num_stickies:
            body += '#%d: %s - %s\n' % (num, submission.title, submission.shortlink)
            posts_dict[num] = submission.shortlink
            num += 1

    return body, posts_dict


def post_proxy(link, chat_type):
    try:
        post = reddit.submission(url=link)
    except praw.exceptions.ClientException:
        return 'Invalid URL. URL should be a reddit shortlink.', False, None
    try:
        output = post.title + ' (' + post.subreddit_name_prefixed + ')'
    except prawcore.Forbidden:
        return 'Reddit post: access denied.', False, None

    if post.over_18 and chat_type != 'private':
        return 'NSFW. Click it yourself.', False, None

    if post.is_self:
        is_image = False
        output += '\n\n---\n\n' + post.selftext
        return output, is_image, None
    elif post.url[:17] in ['https://i.redd.it', 'http://i.redd.it/']:
        is_image = True
        return output, is_image, post.url
    else:
        is_image = False
        output += '\n\n' + post.url
        return output, is_image, None


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
