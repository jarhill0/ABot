import logging
import multiprocessing
import re
import sys
import time
import traceback
import urllib.parse
from datetime import timedelta, timezone

import dateparser
import requests
from pawt import InlineKeyboardMarkupBuilder, Telegram
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
import new_xkcd
import parable
import rand_frog
import reminders
import replace_vowels
import startup
import urban_dict
import web_archive
import wolfram_alpha
from chunkdecorator import chunk
from db_handler import db
from html_janitor import Cleaner
from htmlsplit import HTMLsplit
from leet import leet
from music import add
from myxkcdwrapper import Xkcd, XkcdError
from reddit_handler import RedditHandler
from reminders import Reminder
from scheduler import SpecialSched
from statuscheck import StatusChecker, StatusDummy
from youtube import get_nth_result, get_reply_markup


class ABot(MappedCommandBot):
    def __init__(self, token, *, url=None, session=None):
        text_command_map = dict()
        caption_command_map = text_command_map  # IMPORTANT! IT'S THE SAME OBJECT, SO ALL COMMANDS MUST BE COMPATIBLE
        # WITH BOTH!

        text_command_map['/addmusic'] = add
        text_command_map['/angry'] = self.angry
        text_command_map['/archive'] = self.archive
        text_command_map['/archive2'] = self.archive2
        text_command_map['/bf'] = self.bf
        text_command_map['/bitcoin'] = self.btc
        text_command_map['/botfather_commands'] = self.botfather_commands
        text_command_map['/choice'] = self.choice
        text_command_map['/delete'] = self.delete
        text_command_map['/fewh'] = self.fewh
        text_command_map['/frog'] = self.frog
        text_command_map['/frustrated'] = self.frustrated
        text_command_map['/helloworld'] = self.helloworld
        text_command_map['/help'] = self.help
        text_command_map['/hn'] = self.hn_top
        text_command_map['/hn_ask'] = self.hn_ask
        text_command_map['/hn_best'] = self.hn_best
        text_command_map['/hn_item'] = self.hn_item
        text_command_map['/hn_new'] = self.hn_new
        text_command_map['/hn_replies'] = self.hn_replies
        text_command_map['/hn_show'] = self.hn_show
        text_command_map['/hn_top'] = self.hn_top
        text_command_map['/leet'] = self.leet
        text_command_map['/lelxd'] = self.lelxD
        text_command_map['/lenny'] = self.lenny
        text_command_map['/lmddgtfy'] = self.lmddgtfy
        text_command_map['/lmgtfy'] = self.lmgtfy
        text_command_map['/music'] = self.music
        text_command_map['/myreminders'] = self.myreminders
        text_command_map['/myscore'] = self.myscore
        text_command_map['/mysubs'] = self.mysubs
        text_command_map['/nextlaunch'] = self.launch
        text_command_map['/nsfwoff'] = self.nsfwoff
        text_command_map['/nsfwon'] = self.nsfwon
        text_command_map['/parable'] = self.parable
        text_command_map['/reddit'] = self.proxy_posts
        text_command_map['/redditguess'] = self.redditguess
        text_command_map['/redditguessanswer'] = self.redditguessanswer
        text_command_map['/redditguessnsfw'] = self.redditguessnsfw
        text_command_map['/redditlimit'] = self.redditlimit
        text_command_map['/redditposts'] = self.redditposts
        text_command_map['/remindme'] = self.remindme
        text_command_map['/secretcommand'] = self.secretcommand
        text_command_map['/settings'] = self.settings
        text_command_map['/shrug'] = self.shrug
        text_command_map['/source'] = self.source
        text_command_map['/start'] = self.start
        text_command_map['/startup'] = self.startup
        text_command_map['/subscribe'] = self.subscribe
        text_command_map['/timezone'] = self.timezone
        text_command_map['/ud'] = self.ud
        text_command_map['/unsubscribe'] = self.unsubscribe
        text_command_map['/utensil'] = self.utensil
        text_command_map['/wa'] = self.wa
        text_command_map['/whyme'] = self.whyme
        text_command_map['/wtf'] = self.wtf
        text_command_map['/xkcd'] = self.xkcd
        text_command_map['/yt'] = self.youtube
        text_command_map['/yyy'] = self.yyy

        super().__init__(token, text_command_map, caption_command_map, url=url, session=session)

        text_command_list = self.command_list(self.text_command_map)
        self.text_commands = '\n'.join(' - '.join(cmd) for cmd in text_command_list)
        cap_command_list = self.command_list(self.caption_command_map)
        self.cap_commands = '\n'.join(' - '.join(cmd) for cmd in cap_command_list)
        text_command_list = self.command_list(self.text_command_map, strip_slashes=True)
        self._bf_cmds = '\n'.join(' - '.join(cmd) for cmd in text_command_list)

        self.db = db
        self.reddit = RedditHandler(self.tg)
        self._xkcd = Xkcd()
        self.rates = dict()
        self.cq_rates = dict()
        self.subscriptions = helpers.Subscriptions(['xkcd', 'launches'], self.db)
        self.hn = hn.HN(self.db)

        self.reminder_sched = SpecialSched(self.tg, timefunc=time.time)
        self.launch_sched = SpecialSched(self.tg, timefunc=time.time)
        self.xkcd_sched = SpecialSched(self.tg)
        self.schedule_xkcd()
        self.schedule_launches()
        self.schedule_reminders()

        self.cq_map = {'reddit': self.reddit_callback,
                       'hn': self.hn_callback,
                       'reminder': self.reminder_callback,
                       'ud': self.ud_callback,
                       'yt': self.yt_callback,
                       'tz': self.tz_callback}

        self._username = self.tg.get_me().username

    def exception_handled(self, e):
        traceback.print_exc()
        logging.exception('Exception in command.')
        return True

    def schedule_xkcd(self, tg=None):
        # tg is unused but must be accepted to be scheduled
        sched = self.xkcd_sched

        for hour in range(24):
            sched.enter(hour * 60 * 60, 20, self.check_xkcd)
        sched.enter(24 * 60 * 60, 20, self.schedule_xkcd)

    def check_xkcd(self, tg):
        new_comic = new_xkcd.check_update()
        if new_comic:
            img, alt = new_comic
            for chat_id in self.subscriptions.get_subscribers('xkcd'):
                chat = tg.chat(chat_id)
                chat.send_photo(img[0], caption=img[1])
                chat.send_message(alt)

    def alert_launch_channels(self, tg):
        subscribers = self.subscriptions.get_subscribers('launches')
        next_launch = launchlibrary.get_next_launch()
        for chat_id in subscribers:
            self.send_launch_message(tg.chat(chat_id), launch=next_launch)

    def schedule_launches(self, tg=None):
        # tg is unused but must be accepted to be scheduled
        launch_sched = SpecialSched(self.tg, timefunc=time.time)  # wipe it out!

        launchlibrary.refresh()
        next_launch = launchlibrary.get_next_launch()
        if next_launch:
            launch_time = next_launch['start']
            times = [launch_time - 5 * 60 * 60, launch_time - 30 * 60]
            for time_ in times:
                if time_ > time.time():
                    launch_sched.enterabs(time_ - 60, 23, launchlibrary.refresh)
                    launch_sched.enterabs(time_, 21, self.alert_launch_channels)
        launch_sched.enter(24 * 60 * 60, 22, self.schedule_launches)
        self.launch_sched = launch_sched

    def schedule_reminders(self):
        table = self.db['reminders']
        if table.count() != 0:
            for row in table:
                self.set_reminder(row['time'], row['message'], row['user_id'], add_to_db=False)

    def set_reminder(self, timestamp, message, user_id, add_to_db=True):
        user_id = str(user_id)
        reminder = Reminder(message, user_id, timestamp)
        self.reminder_sched.enterabs(timestamp, 1, reminders.remind, (reminder,))
        if add_to_db:
            self.db['reminders'].insert(dict(time=timestamp, message=message, user_id=user_id))

    def validate(self, message):
        message_time = message.date
        id_pair = (str(message.chat.id), str(message.user.id))
        if id_pair not in self.rates.keys():
            # never even gotten a message from this user in this chat. Add them.
            self.rates[id_pair] = [message_time]
            return True
        times = self.rates[id_pair]  # direct reference to a mutable list
        if len(times) < 11:
            # fewer than 11 messages with this ID pair ever. Start tracking and validate
            times.append(message_time)
            return True
        if message_time - times[0] >= 60:  # if it's been at least a minute since 11 messages ago
            del times[0]
            times.append(message_time)  # length of list should always be 11
            return True
        return False  # we had 11 messages within a minute. Don't update the list.

    def validate_cq(self, user_id):
        user_id = str(user_id)
        timestamp = time.monotonic()
        if user_id not in self.cq_rates.keys():
            self.cq_rates[user_id] = [timestamp]
            return True
        times = self.cq_rates[user_id]
        if len(times) < 10:
            times.append(timestamp)
            return True
        if timestamp - times[0] >= 60:
            del times[0]
            times.append(timestamp)
            return True
        return False

    def perform_extra_task(self):
        self.reminder_sched.run(blocking=False)
        self.xkcd_sched.run(blocking=False)
        self.launch_sched.run(blocking=False)

    def callback_query_handler(self, callback_query):
        name, _, data = callback_query.data.partition(':')
        if not self.validate_cq(callback_query.user.id):
            return
        func = self.cq_map.get(name)
        if func:
            func(data, callback_query)

    @staticmethod
    def _plaintext_helper(message, text, *args, **kwargs):
        message.chat.send_message(text, *args, **kwargs)

    def start(self, message, unused):
        if message.chat.type.value == 'private':
            resp = "Hello {}! I am A Bot.\nHere's a list of my commands:\n\n{}".format(message.user.first_name,
                                                                                       self.text_commands)
            self._plaintext_helper(message, resp)

    @chunk
    def help(self, message, unused):
        """View list of commands."""
        try:
            message.user.chat.send_message('Commands:\n\n' + self.text_commands)
        except APIException:
            # can't message that user…
            pass

    @chunk
    def botfather_commands(self, message, unused):
        self._plaintext_helper(message, self._bf_cmds)

    def angry(self, message, unused):
        """Translate some vocabulary."""
        self._plaintext_helper(message, '"frustrated"')

    def frustrated(self, message, unused):
        """Reveal true meaning."""
        self._plaintext_helper(message, "He's angry.")

    def fewh(self, message, unused):
        """Learn appropriate spelling."""
        self._plaintext_helper(message, 'phew*')

    def helloworld(self, message, unused):
        """Say hello."""
        self._plaintext_helper(message, 'Hello World!')

    def source(self, message, unused):
        """View source."""
        self._plaintext_helper(message, 'Inspect my insides! https://github.com/jarhill0/ABot')

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
        message.reply.send_message("Doesn't work anymore, you cheeky devil :)")

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

    @chunk
    def wa(self, message, command_text):
        """Evaluate query with WolframAlpha."""
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
        """Let me Google that for you…"""
        search = command_text.partition(' ')[2].strip()
        if search:
            result = 'https://lmgtfy.com/?q=' + urllib.parse.quote_plus(search)
            self._plaintext_helper(message, result)
        else:
            message.reply('You gotta gimme something to search!')

    def lmddgtfy(self, message, command_text):
        """Let me DuckDuckGo that for you…"""
        search = command_text.partition(' ')[2].strip()
        if search:
            result = 'https://lmddgtfy.net/?q=' + urllib.parse.quote_plus(search)
            self._plaintext_helper(message, result)
        else:
            message.reply('You gotta gimme something to search!')

    @chunk
    def ud(self, message, command_text):
        """Define a word using Urban Dictionary."""
        term = command_text.partition(' ')[2].strip()
        if term:
            urban_dict.send_message(message.chat, term)
        else:
            self._plaintext_helper(message, 'Please follow the command with a search term.')

    def startup(self, message, unused):
        """Get a disruptive tech startup idea."""
        self._plaintext_helper(message, startup.generate())

    @staticmethod
    def delete(message, unused):
        """Delete this bot message."""
        rep = message.reply_to_message
        if rep:
            try:
                rep.delete()
            except APIException:
                # can't delete — not mine, too old, whatever
                pass

    def btc(self, message, unused):
        """Bitcoin exchange rate and transaction fees."""
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
        """View latest xkcd comic, or view comic specified by number."""
        words = command_text.partition(' ')[2].lower().strip().split()
        opt = words[0] if len(words) > 0 else None
        valid = True
        if not opt:
            comic = self._xkcd.latest()
        elif opt.startswith('rand'):
            comic = self._xkcd.random()
        elif opt.isdigit():
            try:
                comic = self._xkcd.comic(int(opt))
            except XkcdError:
                valid = False
        else:
            comic = self._xkcd.latest()

        if valid:
            title = '{} (#{})'.format(comic.title, comic.num)[:200]
            alt_text = comic.alt
            img_url = comic.img

            if img_url:
                message.chat.send_photo(img_url, caption=title)
            else:
                self._plaintext_helper(message, 'No image found for comic {}.'.format(title))
            self._plaintext_helper(message, alt_text)
        else:
            self._plaintext_helper(message, '{} is not a valid comic number.'.format(opt))

    @staticmethod
    @chunk
    def send_launch_message(chat, launch=None):
        if not launch:
            launch = launchlibrary.get_next_launch()
        messages = launchlibrary.build_launch_message(launch)

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

    # handles chunking on its own
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
                    self._plaintext_helper(message, '/reddit all can only be used in private chat.')
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
        """Get the answer to the previous /redditguess."""
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
        if count and count.isdigit():
            num = int(count)
        else:
            num = 5

        reply_markup = func(num, str(message.chat.id))
        self._plaintext_helper(message, 'Posts from Hacker News:',
                               disable_web_page_preview=True,
                               parse_mode='Markdown', reply_markup=reply_markup)

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

    def _html_chunker(self, chat_id, text, reply_markup=None):
        text = Cleaner.clean(text)

        splitter = HTMLsplit()
        pieces = []

        this_piece = []
        for line in text.split('\n'):
            this_piece.append(line)
            splitter.feed(line)

            if splitter.can_split:
                pieces.append('\n'.join(this_piece))
                this_piece = []

        pieces.append('\n'.join(this_piece))

        if not all(len(p) < 4096 for p in pieces):
            self.tg.chat(chat_id).send_message('That content is too long to be sent here.')
            return

        # helper -- better than copy-paste!
        def send(markup=None):
            content = '\n'.join(this_chunk)
            self.tg.chat(chat_id).send_message(content, parse_mode='HTML', reply_markup=markup)

        this_chunk = []
        total_len = -1  # -1 to account for one extra space
        for part in pieces:
            part_len = len(part)
            if total_len + part_len + 1 > 4096:
                send()
                this_chunk = []
                total_len = -1
            this_chunk.append(part)
            total_len += 1 + part_len  # the 1 for the space
        send(reply_markup)

    def hn_item(self, message, opts):
        """View HN item with specified ID."""
        words = opts.partition(' ')[2].split()
        opt = words[0].lower() if words else None
        if opt and opt.isdigit():
            response = self.hn.view(opt)
        elif opt:
            response = self.hn.view(item_letter=opt, chat_id=str(message.chat.id))
            opt = self.hn.get_posts(str(message.chat.id))[opt.upper()]
        else:
            response = 'Enter a HN item ID or a HN listing letter.'
            self._plaintext_helper(message, response)
            return
        reply_markup = self.hn.replies_button(message.chat.id, opt)
        self._html_chunker(message.chat.id, response, reply_markup=reply_markup)

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
            self._plaintext_helper(message, response)
            return
        self._html_chunker(message.chat.id, response)

    @chunk
    def remindme(self, message, opts):
        """Get a reminder about a topic."""
        remind_reg = re.compile(r'/remindme(?:@{un})? ([^"“”/]+) ?(["“][^"“”]+["”])?'.format(un=self._username),
                                re.IGNORECASE)
        remind_search = remind_reg.search(opts)
        if remind_search is None:
            self._plaintext_helper(message, 'Please provide a date for the reminder.')
            return
        time_str = remind_search.group(1)
        if remind_search.group(2):
            message_text = remind_search.group(2)[1:-1]
        elif message.reply_to_message:
            message_text = message.reply_to_message.get_text_content()
        else:
            message_text = 'Do the thing!'
        user_tz = reminders.get_timezone(message.user.id)
        if not user_tz:
            user_tz = timezone(timedelta(hours=-8))  # incredibly silly default -- doesn't account for DST
        ev_time = dateparser.parse(date_string=time_str.strip(),
                                   settings={'PREFER_DATES_FROM': 'future',
                                             'TIMEZONE': user_tz.tzname(None),
                                             'RETURN_AS_TIMEZONE_AWARE': True})
        if ev_time is None:
            self._plaintext_helper(message, "Sorry, I couldn't understand that time.")
            return
        timestamp = ev_time.timestamp()
        self.set_reminder(timestamp, message_text, message.user.id)
        fmtted_time = reminders.format_time(ev_time)
        response = 'I will remind you about "{}" at {}.'.format(message_text, fmtted_time)
        self._plaintext_helper(message, response)

    @chunk
    def myreminders(self, message, unused):
        """View your reminders."""
        my_remrs = []

        for reminder in db['reminders'].find(user_id=str(message.user.id)):
            my_remrs.append((reminder['time'], reminder['message']))

        my_remrs.sort()
        # build response with time and message of each event.
        user_tz = reminders.get_timezone(message.user.id)
        response = 'Your reminders:\n' + '\n'.join('{}: {}'.format(reminders.format_time(r[0], user_tz), r[1]) for r in
                                                   my_remrs)
        self._plaintext_helper(message, response)

    def leet(self, message, text):
        """1337."""
        text = text.partition(' ')[2]
        if text:
            self._plaintext_helper(message, leet(text))
        else:
            self._plaintext_helper(message, 'Please enter a phrase (e.g. /leet haxor)')

    def music(self, message, text):
        """See a video from https://telegramusic.appspot.com."""
        words = text.partition(' ')[2].split()
        if words:
            word = words[0]

            if word.lower().startswith('new') or word.lower() == 'latest':
                # get the newest number
                url = 'https://telegramusic.appspot.com/api/latest'
            else:
                try:
                    num = int(word)
                    assert num > 0
                except (ValueError, AssertionError):
                    self._plaintext_helper(message, '{!r} is not a valid number.'.format(word))
                    return
                else:
                    url = 'https://telegramusic.appspot.com/api/{num}'.format(num=num)

        else:
            url = 'https://telegramusic.appspot.com/api/random'

        try:
            response = requests.get(url)
        except requests.exceptions.RequestException:
            message.reply.send_message('Unable to get that item.')
            return

        content = response.json()
        if content:
            t = content.get('type', 'youtube')
            if t == 'youtube':
                link = '{num}: https://www.youtube.com/watch?v={id} (from {name})'.format(**content)
            elif t == 'bandcamp':
                link = '{num}: {id} (from {name})'.format(**content)
            else:
                link = 'Unknown item type.'
            self._plaintext_helper(message, link)
        else:
            self._plaintext_helper(message, 'Cannot get number {!r}.'.format(num))

    def youtube(self, message, text):
        """Get the first youtube result for a certain query."""
        query = text.partition(' ')[2]
        if not query:
            return message.reply('Follow the /yt command with a query.')
        self.youtube_helper(query, message.chat)

    @staticmethod
    def youtube_helper(query, chat, n=0):
        link = get_nth_result(query, n)
        if not link:
            chat.send_message('No result for search {!r}.'.format(query))
        else:
            markup = get_reply_markup(chat.id, query, n + 1)
            chat.send_message(link, reply_markup=markup)

    def timezone(self, message, text):
        """Set your offset from UTC."""
        arg = text.partition(' ')[2]
        if arg:
            try:
                offset = int(arg)
            except ValueError:
                self._plaintext_helper(message, 'Timezone offsets must be valid integers.')
            else:
                reminders.set_timezone(message.user.id, offset)
                self._plaintext_helper(message, 'Your timezone has been set to {}.'.format(
                    reminders.get_timezone(message.user.id)))
        else:
            keyboard_builder = InlineKeyboardMarkupBuilder()
            keyboard_builder.add_button(text='Pacific', callback_data='tz:-8')
            keyboard_builder.add_button(text='DST Pacific', callback_data='tz:-7')
            keyboard_builder.new_row()
            keyboard_builder.add_button(text='Eastern', callback_data='tz:-5')
            keyboard_builder.add_button(text='DST Eastern', callback_data='tz:-4')
            keyboard_builder.new_row()
            keyboard_builder.add_button(text='Amsterdam', callback_data='tz:1')
            keyboard_builder.add_button(text='DST Amsterdam', callback_data='tz:2')
            keyboard_builder.new_row()
            keyboard_builder.add_button(text='Jerusalem', callback_data='tz:2')
            keyboard_builder.add_button(text='DST Jerusalem', callback_data='tz:3')

            message.chat.send_message('Your current time zone setting is {}. To change it, use /timezone followed by '
                                      'your offset from UTC in hours, or tap one of these '
                                      'suggestions:'.format(reminders.get_timezone(message.user.id)),
                                      reply_markup=keyboard_builder.build())

    def reddit_callback(self, data, cq):
        post_id, _, chat_id = data.partition(':')
        cq.answer('Here you go: ', cache_time=0)
        chat = self.tg.chat(chat_id)
        link = 'https://redd.it/' + post_id
        self.reddit.post_proxy(link, chat)

    def hn_callback(self, data, cq):
        post_info, _, chat_id = data.partition(':')
        cq.answer('Here you go: ', cache_time=0)
        post_id, _, method = post_info.partition(';')

        reply_markup = None

        if method == 'view':
            response = self.hn.view(item_id=post_id, chat_id=str(chat_id))
            reply_markup = self.hn.replies_button(chat_id, post_id)
        elif method == 'replies':
            response = self.hn.replies(5, item_id=post_id, chat_id=str(chat_id))
        self._html_chunker(chat_id, response, reply_markup=reply_markup)

    def reminder_callback(self, data, cq):
        userchat_id = cq.user.id
        message = cq.message.text.partition(':')[2].strip()  # "Reminder: Whatever"
        try:
            delay = int(data.partition(':')[0].strip())
        except ValueError:
            delay = 10
        self.set_reminder(time.time() + delay * 60, message, userchat_id)
        cq.answer('Snoozed {!r}.'.format(message))

    def ud_callback(self, data, cq):
        chat_id, _, data = data.partition(':')
        index, _, term = data.partition(':')
        index = int(index)
        urban_dict.send_message(self.tg.chat(chat_id), term, index)
        cq.answer("Here's the next definition for {!r}:".format(term))

    def yt_callback(self, data, cq):
        chat_id, _, data = data.partition(':')
        n, _, query = data.partition(':')
        n = int(n)
        self.youtube_helper(query, self.tg.chat(chat_id), n)
        cq.answer('Next result for {!r}:'.format(query))

    @staticmethod
    def tz_callback(data, cq):
        offset = int(data)
        reminders.set_timezone(cq.user.id, offset)
        cq.answer('Offset set to {}.'.format(offset))


def main():
    if config.check_online_status:
        status = StatusChecker(Telegram(config.token), config.status_channel_id)
    else:
        status = StatusDummy()

    if status.already_running():
        print('Bot already running.')
        sys.exit(1)

    status.claim_status()

    logging.basicConfig(filename='bot.log', level=logging.WARNING)

    bot = ABot(config.token)

    try:
        while True:
            try:
                bot.run(timeout=15)
            except Exception:  # bot catches keyboardinterrupts and exits gracefully
                logging.exception('Exception in bot meta.')
                time.sleep(5)
            else:
                # the bot has decided to stop running
                break
    finally:
        status.reliquish_status()


if __name__ == '__main__':
    main()
