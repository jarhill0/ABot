import praw
import prawcore

import config
import db_handler


class RedditHandler:
    def __init__(self, tg):
        self.reddit = praw.Reddit(config.reddit_username, user_agent='/u/{} Telegram bot'.format(
            config.reddit_username))
        self.db = db_handler.db
        self.tg = tg

    def hot_posts(self, subreddit, number, chat, *, guessing_game=False):
        if number < 1:
            raise ValueError('More than 0 posts must be requested.')

        sub = self.reddit.subreddit(subreddit)
        magic = False

        try:
            sub.fullname
        except (prawcore.Forbidden, prawcore.NotFound, prawcore.Redirect, prawcore.BadRequest, AttributeError,
                TypeError, AssertionError):
            if subreddit.lower() in ('all', 'popular'):  # special subreddits
                magic = True
            else:
                chat.send_message('Error. Could not access r/{}.'.format(subreddit))
                return

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

        self.add_posts_to_dict(chat.id, posts_dict)
        if guessing_game:
            self.db['redditguessanswer'].upsert(dict(chat=str(chat.id), sub=sub.display_name_prefixed), ['chat'])

        chat.send_message('\n'.join(body), disable_web_page_preview=True)
        return

    def post_proxy(self, link, chat):
        try:
            post = self.reddit.submission(url=link)
        except praw.exceptions.ClientException:
            chat.send_message('Invalid URL. URL should be a reddit shortlink.')
            return

        try:
            output = '{} ({})'.format(post.title, post.subreddit_name_prefixed)
        except prawcore.Forbidden:
            chat.send_message('Reddit post: access denied.')
            return

        nsfw_setting = self.db['nsfw'].find_one(chat=str(chat.id))
        nsfw_setting = nsfw_setting['setting'] if nsfw_setting else False

        if post.over_18 and chat.type.value != 'private' and not nsfw_setting:
            chat.send_message('NSFW. Click it yourself.')
            return

        if post.is_self:
            output += '\n\n---\n\n' + post.selftext
            while output:
                # in case the message is longer than 4000 chars
                chat.send_message(output[:4000])
                output = output[4000:]
            return

        elif post.url[:17] in ('https://i.redd.it', 'http://i.redd.it/'):
            chat.send_photo(post.url, caption=output[:200])
            return

        elif post.url[:17] in ['https://v.redd.it', 'http://v.redd.it/']:
            if post.media['reddit_video']['is_gif']:
                url = post.media['reddit_video']['fallback_url']
                caption = output[:200]
                chat.send_video(url, caption=caption)
            else:
                url = post.media['reddit_video']['scrubber_media_url']
                extra_part = ' (Silent preview. Full video available at {})'.format(post.url)
                caption = output[:200 - len(extra_part)] + extra_part  # make sure extra part is added
                chat.send_video(url, caption=caption)
            return
        else:
            output += '\n\n' + post.url
            chat.send_message(output)
            return

    def get_subreddit_from_post(self, link):
        return self.reddit.submission(url=link).subreddit_name_prefixed

    def add_posts_to_dict(self, chat_id, posts):
        posts_table = self.db['redditposts']
        posts['chat'] = str(chat_id)

        for n in range(1, 21):  # 20 is the maximum redditlimit
            if str(n) not in posts.keys():
                posts[str(n)] = None  # make all invalid numbers None when we update the db

        posts_table.upsert(posts, ['chat'])

    def set_redditposts_limit(self, user, limit):
        limits = self.db['redditlimit']
        limits.upsert(dict(user=str(user.id), limit=limit), ['user'])

    def get_redditposts_limit(self, user):
        limits = self.db['redditlimit']
        user = limits.find_one(user=str(user.id))
        if user is None:
            return 5
        return user['limit']
