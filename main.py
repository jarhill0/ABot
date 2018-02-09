import multiprocessing
import traceback
import urllib.parse

import xkcd
from pawt.bots import MappedCommandBot
from pawt.exceptions import *

import archive_is
import bitcoin
import brainfuck_interpreter
import choice
import config
import helpers
import hn
import launchlibrary
import memetext
import parable
import rand_frog
import replace_vowels
import startup
import urban_dict
import web_archive
import wolfram_alpha
from db_handler import db
from reddit_handler import RedditHandler


class ABot(MappedCommandBot):
    def __init__(self, token, *, url=None, session=None):
        text_command_map = dict()
        caption_command_map = dict()

        text_command_map['/helloworld'] = self.helloworld
        text_command_map['/source'] = self.source
        text_command_map['/settings'] = self.settings
        text_command_map['/shrug'] = self.shrug
        text_command_map['/lenny'] = self.lenny
        text_command_map['/utensil'] = self.utensil
        text_command_map['/wtf'] = self.wtf
        text_command_map['/yyy'] = self.yyy
        text_command_map['/secretcommand'] = self.secretcommand
        text_command_map['/lelxd'] = self.lelxD
        text_command_map['/parable'] = self.parable
        text_command_map['/whyme'] = self.whyme
        text_command_map['/wa'] = self.wa
        text_command_map['/frog'] = self.frog
        text_command_map['/choice'] = self.choice
        text_command_map['/bf'] = self.bf
        text_command_map['/archive'] = self.archive
        text_command_map['/archive2'] = self.archive2
        text_command_map['/lmgtfy'] = self.lmgtfy
        text_command_map['/lmddgtfy'] = self.lmddgtfy
        text_command_map['/ud'] = self.ud
        text_command_map['/startup'] = self.startup
        text_command_map['/delete'] = self.delete
        text_command_map['/bitcoin'] = self.btc
        text_command_map['/start'] = self.start
        text_command_map['/help'] = self.help
        text_command_map['/botfather_commands'] = self.botfather_commands
        text_command_map['/xkcd'] = self.xkcd
        text_command_map['/nextlaunch'] = self.launch
        text_command_map['/redditlimit'] = self.redditlimit
        text_command_map['/nsfwon'] = self.nsfwon
        text_command_map['/nsfwoff'] = self.nsfwoff
        text_command_map['/redditposts'] = self.redditposts
        text_command_map['/reddit'] = self.proxy_posts
        text_command_map['/redditguess'] = self.redditguess
        text_command_map['/redditguessnsfw'] = self.redditguessnsfw
        text_command_map['/redditguessanswer'] = self.redditguessanswer
        text_command_map['/myscore'] = self.myscore
        text_command_map['/subscribe'] = self.subscribe
        text_command_map['/unsubscribe'] = self.unsubscribe
        text_command_map['/mysubs'] = self.mysubs
        text_command_map['/hn_ask'] = self.hn_ask
        text_command_map['/hn_best'] = self.hn_best
        text_command_map['/hn_new'] = self.hn_new
        text_command_map['/hn_show'] = self.hn_show
        text_command_map['/hn'] = self.hn_top
        text_command_map['/hn_top'] = self.hn_top
        text_command_map['/hn_item'] = self.hn_item
        text_command_map['/hn_replies'] = self.hn_replies

        super().__init__(token, text_command_map, caption_command_map, url=url, session=session)

        text_command_list = self.command_list(self.text_command_map)
        self.text_commands = '\n'.join(' - '.join(cmd) for cmd in text_command_list)
        cap_command_list = self.command_list(self.caption_command_map)
        self.cap_commands = '\n'.join(' - '.join(cmd) for cmd in cap_command_list)
        text_command_list = self.command_list(self.text_command_map, strip_slashes=True)
        self._bf_cmds = '\n'.join(' - '.join(cmd) for cmd in text_command_list)

        launchlibrary.refresh()

        self.db = db
        self.reddit = RedditHandler(self.tg)
        self.rates = dict()
        self.subscriptions = helpers.Subscriptions(['xkcd', 'launches'], self.db)
        self.hn = hn.HN(self.db)

    def validate(self, message):
        message_time = message.date
        id_pair = (str(message.chat.id), str(message.user.id))
        if id_pair not in self.rates.keys():
            # never even gotten a message from this user in this chat. Add them.
            self.rates[id_pair] = [message_time]
            return True
        times = self.rates[id_pair]  # direct reference to a mutable list
        if len(times) < 10:
            # fewer than 10 messages with this ID pair ever. Start tracking and validate
            times.append(message_time)
            return True
        if message_time - times[0] >= 60:  # if it's been at least a minute since 10 messages ago
            del times[0]
            times.append(message_time)  # length of list should always be 10
            return True
        return False  # we had 10 messages within a minute. Don't update the list.

    @staticmethod
    def _plaintext_helper(message, text, *args, **kwargs):
        message.chat.send_message(text, *args, **kwargs)

    def start(self, message, unused):
        resp = "Hello {}! I am A Bot.\nHere's a list of my commands:\n\n{}".format(message.user.first_name,
                                                                                   self.text_commands)
        self._plaintext_helper(message, resp)

    def help(self, message, unused):
        """View list of commands."""
        self._plaintext_helper(message, 'Commands:\n\n' + self.text_commands)

    def botfather_commands(self, message, unused):
        self._plaintext_helper(message, self._bf_cmds)

    def helloworld(self, message, unused):
        """Say hello."""
        self._plaintext_helper(message, 'Hello World!')

    def source(self, message, unused):
        """View source."""
        self._plaintext_helper(message, 'Inspect my insides! http://github.com/jarhill0/ABot')

    def settings(self, message, unused):
        """View available settings."""
        self._plaintext_helper(message, memetext.settings, parse_mode='Markdown')

    def shrug(self, message, unused):
        """¯\_(ツ)_/¯."""
        self._plaintext_helper(message, '¯\_(ツ)_/¯')

    def lenny(self, message, unused):
        """( ͡° ͜ʖ ͡°)."""
        self._plaintext_helper(message, '( ͡° ͜ʖ ͡°)')

    def utensil(self, message, unused):
        """Holds up spork."""
        self._plaintext_helper(message, memetext.spork)

    def wtf(self, message, unused):
        """What the hell."""
        self._plaintext_helper(message, memetext.marines)

    def yyy(sylf, myssygy, ynysyd):
        """Whyt thy hyll."""
        sylf._plaintext_helper(myssygy, memetext.myrynys)

    @staticmethod
    def secretcommand(message, unused):
        message.reply.send_message("Doesn't work any more, you cheeky devil :)")

    # noinspection PyPep8Naming
    def lelxD(self, message, unused):
        """lel xD."""
        self._plaintext_helper(message, memetext.xD)

    def parable(self, message, unused):
        """Generate reassuring parable."""
        self._plaintext_helper(message, parable.text_gen.text_gen(1))

    def whyme(self, message, command_text):
        """Replace all vowels with the letter y."""
        text = command_text.partition(' ')[2].strip()
        if text:
            message.reply.send_message(replace_vowels.replace(text))
        else:
            self._plaintext_helper(message, 'Say something after /whyme (e.g. /whyme What the hell?!)')

    def wa(self, message, command_text):
        query = command_text.partition(' ')[2]
        if not query:
            self._plaintext_helper(message, 'Specify a query after /wa (e.g. /wa calories in a bagel)')
        else:
            try:
                ans = wolfram_alpha.query_wa(query)
            except wolfram_alpha.WolframAlphaException:
                ans = 'Error processing query.'
            message.reply.send_message(ans, parse_mode='Markdown')

    @staticmethod
    def frog(message, unused):
        """View an image of a frog."""
        image_url = rand_frog.main()
        message.chat.send_photo(image_url)

    def choice(self, message, command_text):
        """Choose between two or more options, separated by a semicolon."""
        options = command_text.partition(' ')[2]
        if not options or ';' not in options:
            self._plaintext_helper(message, 'List two or more options separated by a semicolon.')
        else:
            chosen = choice.choice(options)
            self._plaintext_helper(message, '{}\n\n(chosen for {})'.format(chosen, message.user.full_name))

    def bf(self, message, command_text):
        """Execute Brainfuck, including optional input after an optional semicolon."""
        options = command_text.partition(' ')[2]
        code, semi, user_inp = options.partition(';')

        def bf_helper():
            response = brainfuck_interpreter.main(code, input_=user_inp)
            self.tg.copy().chat(message.chat.id).send_message(response)

        multiprocessing.Process(target=bf_helper).start()

    @staticmethod
    def archive_helper(opts, archiver):
        url = opts.partition(' ')[2].split()[0]
        if url:
            return archiver(url)
        return 'Please provide a URL to archive.'

    def archive(self, message, command_text):
        """Archive a page with the archive.is service."""
        message.reply.send_message(self.archive_helper(command_text, archive_is.archive_message))

    def archive2(self, message, command_text):
        """Archive a page with the web.archive.org service."""
        message.reply.send_message(self.archive_helper(command_text, web_archive.archive))

    def lmgtfy(self, message, command_text):
        """Let me Google that for you please..."""
        search = command_text.partition(' ')[2].strip()
        if search:
            result = 'https://lmgtfy.com/?q=' + urllib.parse.quote_plus(search)
            self._plaintext_helper(message, result)
        else:
            message.reply('You gotta gimme something to search!')

    def lmddgtfy(self, message, command_text):
        """Let me Google that for you please..."""
        search = command_text.partition(' ')[2].strip()
        if search:
            result = 'https://lmddgtfy.net/?q=' + urllib.parse.quote_plus(search)
            self._plaintext_helper(message, result)
        else:
            message.reply('You gotta gimme something to search!')

    def ud(self, message, command_text):
        term = command_text.partition(' ')[2].strip()
        if term:
            reply = urban_dict.build_message(term)
            self._plaintext_helper(message, reply, parse_mode='Markdown')
        else:
            self._plaintext_helper(message, 'Please follow the command with a search term.')

    def startup(self, message, unused):
        self._plaintext_helper(message, startup.generate())

    @staticmethod
    def delete(message, unused):
        try:
            message.reply_to_message.delete()
        except APIException:
            # can't delete — not mine, too old, whatever
            pass

    def btc(self, message, unused):
        self._plaintext_helper(message, bitcoin.btc_message())

    @staticmethod
    def command_list(cmd_dict, strip_slashes=False):
        cmd_list = []
        for command_name, command_func in cmd_dict.items():
            if command_func.__doc__:
                if strip_slashes:
                    command_name = command_name.lstrip('/')
                cmd_list.append((command_name, command_func.__doc__))

        return sorted(cmd_list)

    def xkcd(self, message, command_text):
        words = command_text.partition(' ')[2].lower().strip().split()
        opt = words[0] if len(words) > 0 else None
        if not opt:
            comic = xkcd.getLatestComic()
        elif opt.startswith('rand'):
            comic = xkcd.getRandomComic()
        elif opt.isdigit():
            comic = xkcd.getComic(int(opt))
        else:
            comic = xkcd.getLatestComic()

        if comic.number != -1:
            title = '{} (#{})'.format(comic.getTitle(), comic.number)[:200]
            alt_text = comic.getAltText()
            img_url = comic.getImageLink()

            message.chat.send_photo(img_url, caption=title)
            self._plaintext_helper(message, alt_text)
        else:
            self._plaintext_helper(message, '{} is not a valid comic number.'.format(opt))

    @staticmethod
    def send_launch_message(chat, messages=None, launch=None):
        if not messages:
            if launch:
                messages = launchlibrary.build_launch_message(launch)
            else:
                messages = launchlibrary.build_launch_message(launchlibrary.get_next_launch())

        pic, text = messages

        if pic is not None:  # pic will be None if there is no next message
            chat.send_photo(*pic)

        chat.send_message(**text)

    def launch(self, message, unused):
        """View information about the next SpaceX launch."""
        self.send_launch_message(message.chat)

    def reddnsfwhelper(self, message, on):
        current_chat = message.chat.id
        table = self.db['nsfw']
        row = dict(chat=current_chat, setting=on)
        table.upsert(row, ['chat'])
        response = 'NSFW Reddit content is now {} for this chat.'.format('on' if on else 'off')
        self._plaintext_helper(message, response)

    def nsfwon(self, message, unused):
        self.reddnsfwhelper(message, True)

    def nsfwoff(self, message, unused):
        self.reddnsfwhelper(message, False)

    def redditlimit(self, message, opts):
        """Set limit for /redditposts."""
        words = opts.partition(' ')[2].split()
        num = words[0] if len(words) > 0 else ''
        if num.isdigit():
            limit = min(max(int(num), 1), 20)
            self.reddit.set_redditposts_limit(message.user, limit)
            response = 'Limit set to {}.'.format(limit)
        else:
            response = 'Your current limit is {}. To change, specify a number after /redditlimit (e.g. /redditlimit ' \
                       '5).'.format(self.reddit.get_redditposts_limit(message.user))
        self._plaintext_helper(message, response)

    def redditposts(self, message, opts):
        """View posts from the specified subreddit."""
        num_posts = self.reddit.get_redditposts_limit(message.user)
        words = opts.partition(' ')[2].split()
        opt = words[0] if words else None
        if opt:
            self.reddit.hot_posts(opt, num_posts, message.chat)
        else:
            self._plaintext_helper(message, 'Specify a subreddit after /redditposts (e.g. /redditposts funny)')

    def proxy_posts(self, message, opts):
        """View Reddit post specified by link or number."""
        words = opts.partition(' ')[2].split()
        opt = words[0].lower() if words else None
        if not opt:
            self._plaintext_helper(message, 'Specify a url after /reddit (e.g. /reddit https://redd.it/robin)',
                                   disable_web_page_preview=True)
        elif opt.isdigit() or opt == 'all':
            posts = self.db['redditposts']
            chat_row = posts.find_one(chat=str(message.chat.id))
            if not chat_row:
                self._plaintext_helper(message, 'First use /redditposts followed by a subreddit name to use /reddit ['
                                                'number] syntax')
                return
            if opt.isdigit():
                post = chat_row[opt]
                if post:
                    self.reddit.post_proxy(post, message.chat)
                else:
                    self._plaintext_helper(message, 'Invalid number.')
            elif opt == 'all':
                if message.chat.type.value == 'private':
                    for i in range(1, 21):
                        post = chat_row[str(i)]
                        if not post:
                            break
                        self.reddit.post_proxy(post, message.chat)
                else:
                    self._plaintext_helper(message, '/redditposts all call only be used in private chat.')
        else:
            url = opt
            self.reddit.post_proxy(url, message.chat)

    def _redditguess(self, message, nsfw=False):
        nsfw_setting = self.db['nsfw'].find_one(chat=str(message.chat.id))
        nsfw_setting = nsfw_setting['setting'] if nsfw_setting else False

        if nsfw and message.chat.type.value != 'private' and not nsfw_setting:
            self._plaintext_helper(message, 'NSFW material is not allowed in this chat.')
            return
        subreddit = 'randnsfw' if nsfw else 'random'
        self.reddit.hot_posts(subreddit, 6, message.chat, guessing_game=True)

    def redditguess(self, message, unused):
        """View posts from a random subreddit without the name and try to guess where they're from."""
        self._redditguess(message, nsfw=False)

    def redditguessnsfw(self, message, unused):
        self._redditguess(message, nsfw=True)

    def redditguessanswer(self, message, unused):
        answer_row = self.db['redditguessanswer'].find_one(chat=str(message.chat.id))
        answer = answer_row['sub'] if answer_row else 'nonexistent'
        response = 'The answer for the last /redditguess is {}.'.format(answer)
        self._plaintext_helper(message, response)

    def myscore(self, message, opts):
        """View or change your score."""
        words = opts.partition(' ')[2].split()
        opt = words[0].lower() if words else None

        score_table = self.db['scores']
        user_score_row = score_table.find_one(user=str(message.user.id))
        score = user_score_row['score'] if user_score_row else 0

        num = None
        if opt and opt[0] in ('-', '+') and opt[1:].isdigit():
            num = int(opt)

        if num is not None:
            change = int(num)
            if abs(change) > 1000:
                message.reply.send_message('Absolute change value should be no greater than 1000.')
                return
            new_score = score + change
            score_table.upsert(dict(user=str(message.user.id), score=new_score), ['user'])
            message.reply.send_message('Your score has been updated to {}.'.format(new_score))
        else:
            resp = 'Your score is {}. To change it, follow /myscore with a number that starts with "+" or ' \
                   '"-".'.format(score)
            message.reply.send_message(resp)

    def subscribe(self, message, opts):
        """Subscribe to announcements about a topic (launches, xkcd, etc.)."""
        words = opts.partition(' ')[2].split()
        topic = words[0].lower() if words else None
        if topic:
            try:
                self.subscriptions.subscribe(topic, str(message.chat.id))
            except helpers.SubscriptionNotFoundError:
                topics = ', '.join('`{}`'.format(t) for t in self.subscriptions.topics)
                resp = 'Invalid subscription ID. Valid subscriptions: ' + topics
            else:
                resp = 'This chat will recieve messages related to `{}`.'.format(topic)
        else:
            resp = 'Please follow /subscribe with a topic ID like `xkcd` or `launches`.',
        self._plaintext_helper(message, resp, parse_mode='Markdown')

    def unsubscribe(self, message, opts):
        """Unsubscribe from announcements about a topic (launches, xkcd, etc.)."""
        words = opts.partition(' ')[2].split()
        topic = words[0].lower() if words else None
        if topic:
            try:
                self.subscriptions.unsubscribe(topic, str(message.chat.id))
            except helpers.SubscriptionNotFoundError:
                topics = ', '.join('`{}`'.format(t) for t in self.subscriptions.topics)
                resp = 'Invalid subscription ID. Valid subscriptions: ' + topics
            else:
                resp = 'This chat will not recieve messages related to `{}`.'.format(topic)
        else:
            resp = 'Please follow /unsubscribe with a topic ID like `xkcd` or `launches`.',
        self._plaintext_helper(message, resp, parse_mode='Markdown')

    def mysubs(self, message, unused):
        """Get your subscriptions."""
        topics = self.subscriptions.my_subscriptions(str(message.chat.id))
        response = 'Your subscriptions: ' + ', '.join('`{}`'.format(t) for t in topics)
        self._plaintext_helper(message, response, parse_mode='Markdown')

    def _hn_helper(self, message, opts, func):
        words = opts.partition(' ')[2].split()
        count = words[0].lower() if words else None
        if not count and count.isdigit():
            num = int(count)
        else:
            num = 5
        response = func(num, str(message.chat.id))
        self._plaintext_helper(message, response,
                               disable_web_page_preview=True,
                               parse_mode='Markdown')

    def hn_ask(self, message, opts):
        """View Ask HN posts."""
        self._hn_helper(message, opts, self.hn.ask)

    def hn_best(self, message, opts):
        """View best HN posts."""
        self._hn_helper(message, opts, self.hn.best)

    def hn_new(self, message, opts):
        """View new HN posts."""
        self._hn_helper(message, opts, self.hn.new)

    def hn_show(self, message, opts):
        """View Show HN posts."""
        self._hn_helper(message, opts, self.hn.show)

    def hn_top(self, message, opts):
        """View top HN posts."""
        self._hn_helper(message, opts, self.hn.top)

    def hn_item(self, message, opts):
        """View HN item with specified ID."""
        words = opts.partition(' ')[2].split()
        opt = words[0].lower() if words else None
        if opt and opt.isdigit():
            response = self.hn.view(opt)
        elif opt:
            response = self.hn.view(item_letter=opt, chat_id=str(message.chat.id))
        else:
            response = 'Enter a HN item ID or a HN listing letter.'
        self._plaintext_helper(message, response, parse_mode='HTML')

    def hn_replies(self, message, opts):
        """View replies to HN item with specified ID or letter code."""
        words = opts.partition(' ')[2].split()
        opt = words[0].lower() if words else None
        lim_opt = words[1] if len(words) > 1 else ''
        lim = int(lim_opt) if lim_opt.isdigit() else 5
        if opt and opt.isdigit():
            response = self.hn.replies(lim, opt)
        elif opt:
            response = self.hn.replies(lim, item_letter=opt, chat_id=str(message.chat.id))
        else:
            response = 'Enter a HN item ID or short name.'
        self._plaintext_helper(message, response, parse_mode='HTML')


def main():
    bot = ABot(config.token)
    while True:
        try:
            bot.run()
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
