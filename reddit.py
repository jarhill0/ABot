import praw
import prawcore

import config

reddit = praw.Reddit(config.reddit_username, user_agent='%s Telegram bot' % config.reddit_username)


def hot_posts(subreddit, number, chat_id, db, *, guessing_game=False):
    if number < 1:
        raise ValueError('More than 0 posts must be requested.')

    sub = reddit.subreddit(subreddit)
    magic = False

    try:
        sub.fullname
    except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError, TypeError,
            AssertionError):
        if subreddit in ('all', 'popular'):  # special subreddits
            magic = True
        else:
            return 'Error. Could not access r/%s.' % subreddit, None

    if guessing_game:
        body = ['Hot posts from a random subreddit. Take a guess!']
    else:
        name = 'r/' + sub.display_name if magic else sub.display_name_prefixed
        body = ['Hot posts from {}:'.format(name)]
    body.append('')  # add extra newline after header.

    posts_dict = dict()
    n = 1

    for submission in sub.hot(limit=number + 5):
        if len(posts_dict) < number:
            if not submission.stickied or magic:  # don't exclude stickies from r/all and r/popular
                body.append('#{}: {} - {}'.format(n, submission.title, submission.shortlink))
                posts_dict[str(n)] = submission.shortlink
                n += 1

    add_posts_to_dict(chat_id, posts_dict, db)
    if guessing_game:
        db['redditguessanswer'].upsert(dict(chat=str(chat_id), sub=sub.display_name_prefixed), ['chat'])

    return '\n'.join(body)


# noinspection PyPep8Naming
def post_proxy(link, chat_type, chat_id, tg):
    TEXT = 10
    PICTURE = 20
    VIDEO = 30

    def proxy_helper(link_, chat_type_, chat_id_):

        # noinspection PyUnresolvedReferences
        try:
            post = reddit.submission(url=link_)
        except praw.exceptions.ClientException:
            data = {'text': 'Invalid URL. URL should be a reddit shortlink.',
                    'chat_id': chat_id_}
            response_type = TEXT

            return data, response_type

        try:
            output = post.title + ' (' + post.subreddit_name_prefixed + ')'
        except prawcore.Forbidden:
            data = {'text': 'Reddit post: access denied.',
                    'chat_id': chat_id_}
            response_type = TEXT

            return data, response_type

        if post.over_18 and chat_type_ != 'private':
            data = {'text': 'NSFW. Click it yourself.',
                    'chat_id': chat_id_}
            response_type = TEXT

            return data, response_type

        if post.is_self:
            output += '\n\n---\n\n' + post.selftext

            data = {'text': output,
                    'chat_id': chat_id_}
            response_type = TEXT

            return data, response_type

        elif post.url[:17] in ['https://i.redd.it', 'http://i.redd.it/']:
            data = {'chat_id': chat_id_,
                    'photo': post.url,
                    'caption': output}
            response_type = PICTURE

            return data, response_type

        elif post.url[:17] in ['https://v.redd.it', 'http://v.redd.it/']:
            response_type = VIDEO
            data = {'chat_id': chat_id_}
            if post.media['reddit_video']['is_gif']:
                data['video'] = post.media['reddit_video']['fallback_url']
                data['caption'] = output[:200]
            else:
                data['video'] = post.media['reddit_video']['scrubber_media_url']
                data['caption'] = (output + ' (Silent preview. Full video available at %s)' % post.url)[:200]

            return data, response_type
        else:
            response_type = TEXT
            output += '\n\n' + post.url
            data = {'text': output,
                    'chat_id': chat_id_}
            return data, response_type

    data_, response_type_ = proxy_helper(link, chat_type, chat_id)
    if response_type_ == TEXT:
        tg.send_message(data_)
    elif response_type_ == PICTURE:
        tg.send_photo(data_)
    elif response_type_ == VIDEO:
        tg.send_video(data_)


def get_subreddit_from_post(link):
    return reddit.submission(url=link).subreddit_name_prefixed


def add_posts_to_dict(chat_id, posts, db):
    posts_table = db['redditposts']
    posts['chat'] = str(chat_id)

    for n in range(1, 21):  # 20 is the maximum redditlimit
        if str(n) not in posts.keys():
            posts[str(n)] = None  # make all invalid numbers None when we update the db

    posts_table.upsert(posts, ['chat'])


def set_redditposts_limit(user_id, limit, db):
    limits = db['redditlimit']
    limits.upsert(dict(user=str(user_id), limit=limit), ['user'])


def get_redditposts_limit(user_id, db):
    limits = db['redditlimit']
    user = limits.find_one(user=str(user_id))
    if user is None:
        return 5
    return user['limit']
