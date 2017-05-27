import praw
import prawcore

reddit = praw.Reddit('k8IA', user_agent='k8IA Telegram bot')


def hot_posts(subreddit, number):
    if number < 1:
        raise ValueError('More than 0 posts must be requested.')

    body = 'Hot posts from /r/%s:\n\n' % subreddit
    num = 1
    num_stickies = 0

    try:
        reddit.subreddit(subreddit).fullname
    except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError, TypeError,
            AssertionError):
        return 'Error. Could not access /r/%s.' % subreddit

    for i in range(1, 3):
        try:
            reddit.subreddit(subreddit).sticky(number=i)
        except prawcore.NotFound:
            pass
        else:
            num_stickies = i

    for true_count, submission in enumerate(reddit.subreddit(subreddit).hot(limit=number + num_stickies)):
        if true_count >= num_stickies:
            body += '#%d: %s - %s\n' % (num, submission.title, submission.shortlink)
            num += 1

    return body


def post_proxy(link):
    try:
        post = reddit.submission(url=link)
    except praw.exceptions.ClientException:
        return 'Invalid URL. URL should be a reddit shortlink.', False, None
    try:
        output = post.title + ' (' + post.subreddit_name_prefixed + ')'
    except prawcore.Forbidden:
        return 'Reddit post: access denied.', False, None

    if post.over_18:
        return 'NSFW. Click it yourself.', False, None

    if post.is_self:
        is_image = False
        output += '\n\n---\n\n' + post.selftext
        return (output, is_image, None)
    elif post.url[:17] in ['https://i.redd.it', 'http://i.redd.it/']:
        is_image = True
        return (output, is_image, post.url)
    else:
        is_image = False
        output += '\n\n' + post.url
        return (output, is_image, None)


if __name__ == '__main__':
    # quick test
    post_proxy('https://www.reddit.com/r/pics/comments/6dkkea/both_my_mom_and_i_are_graduating_today/')
