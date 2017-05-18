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
    except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError, TypeError):
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
    post = reddit.submission(url=link)
    output = '*' post.title
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
    print(hot_posts('funny', 5))
