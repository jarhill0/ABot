import praw
import prawcore
from pawt.exceptions import APIException
from pawt.models.reply_markup import InlineKeyboardMarkupBuilder

import config
import db_handler
from imgur import direct_link

IMAGE_ENDINGS = ('.jpg', '.png', '.tif', '.tiff', '.bmp')


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
            body = 'Hot posts from a random subreddit. Take a guess!'
        else:
            name = 'r/' + sub.display_name if magic else sub.display_name_prefixed
            body = 'Hot posts from {}:'.format(name)

        builder = InlineKeyboardMarkupBuilder()

        posts_dict = dict()
        n = 1

        for submission in sub.hot(limit=number + 5):
            if len(posts_dict) < number:
                if not submission.stickied or magic:  # don't exclude stickies from r/all and r/popular
                    text = '#{}: {}'.format(n, submission.title)
                    builder.add_button(text, callback_data='reddit:{}:{}'.format(submission.id, chat.id))
                    builder.new_row()
                    posts_dict[str(n)] = submission.shortlink
                    n += 1

        self.add_posts_to_dict(chat.id, posts_dict)
        if guessing_game:
            self.db['redditguessanswer'].upsert(dict(chat=str(chat.id), sub=sub.display_name_prefixed), ['chat'])

        chat.send_message(body, reply_markup=builder.build())
        return

    def post_proxy(self, link, chat):
        try:
            post = self.reddit.submission(url=link)
        except praw.exceptions.ClientException:
            chat.send_message('Invalid URL. URL should be a reddit shortlink.')
            return

        try:
            title_info = '{} ({})\n\n{}'.format(post.title, post.subreddit_name_prefixed, post.shortlink)
        except prawcore.Forbidden:
            chat.send_message('Reddit post: access denied.')
            return

        if post.over_18 and chat.type.value != 'private':
            nsfw_setting = self.db['nsfw'].find_one(chat=str(chat.id))
            nsfw_setting = nsfw_setting['setting'] if nsfw_setting else False
            if not nsfw_setting:
                chat.send_message('NSFW. Click it yourself.')
                return

        if post.is_self:
            title_info = '[{}]({}) ({})'.format(post.title, post.shortlink, post.subreddit_name_prefixed)
            chat.send_message(title_info, disable_web_page_preview=True, parse_mode='Markdown')
            text = post.selftext
            while text:
                # in case the message is longer than 4000 chars
                try:
                    chat.send_message(text[:4000], parse_mode='Markdown')
                except APIException:
                    chat.send_message(text[:4000])
                text = text[4000:]
            return

        elif post.url[:17] in ['https://v.redd.it', 'http://v.redd.it/']:
            if post.media['reddit_video']['is_gif']:
                url = post.media['reddit_video']['fallback_url']
                caption = title_info[:200]
                chat.send_video(url, caption=caption)
            else:
                url = post.media['reddit_video']['fallback_url']
                extra_part = ' (Silent preview. Full video available at {})'.format(post.url)
                caption = title_info[:200 - len(extra_part)] + extra_part  # make sure extra part is added
                chat.send_video(url, caption=caption)
            return
        else:
            url = direct_link(post.url) or post.url  # convert imgur/gfycat links to direct links
            if url.endswith('.gifv'):
                url = url[:-4] + 'mp4'  # strip the v

            if url.endswith('.mp4'):
                try:
                    chat.send_video(url, caption=title_info[:200])
                    return
                except APIException:
                    # it ain't a gif
                    pass
            elif url.endswith('.gif'):
                try:
                    chat.send_document(url, caption=title_info[:200])
                    return
                except APIException:
                    # it ain't a gif
                    pass
            elif any(url.lower().endswith(ie) for ie in IMAGE_ENDINGS):
                try:
                    chat.send_photo(url, caption=title_info[:200])
                    return
                except APIException:
                    # it ain't a photo
                    pass

            chat.send_message(title_info, disable_web_page_preview=True)
            chat.send_message(post.url)
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
