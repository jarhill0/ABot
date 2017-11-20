import datetime
import multiprocessing
import os.path
import re
import sys
import time
import traceback
import urllib.parse

import dataset
import xkcd

import archive_is
import brainfuck_interpreter
import choice
import config
import helpers
import homemade_scheduler
import launchlibrary
import launchreminders
import memesseges
import new_xkcd
import rand_frog
import reddit
import reminders
import replace_vowels
import startup
import statuscheck
import urban_dict
import web_archive
import wolfram_alpha
from parable import text_gen
from telegram import Telegram, user_name

tg = Telegram(config.token)
next_launch = None
bot_scheduler = homemade_scheduler.Scheduler()
db = dataset.connect('sqlite:///{}'.format(os.path.join(helpers.folder_path(), 'data', 'mydatabase.db')))
subscriptions = helpers.Subscriptions(['xkcd', 'launches'], db)
memesseges.globalize_tg(tg)

already_running = False


def main():
    global already_running
    if config.check_online_status:
        if statuscheck.already_running(tg):
            print('Bot already running.')
            already_running = True
            sys.exit(1)
        statuscheck.claim_status(tg)
    schedule_events(bot_scheduler)
    counter = 0
    while True:
        response = tg.get_updates()
        counter += 1
        # noinspection PySimplifyBooleanCheck
        if response['result'] != []:
            handle(response)
        if counter == 50:
            bot_scheduler.check_events()
            counter = 0


def schedule_launches(calendar):
    launchlibrary.update_json_on_disk()

    global next_launch
    try:
        next_launch = launchreminders.get_next_launch()
    except launchreminders.NoLaunchFoundError:
        # there is no next launch
        pass
    else:
        launchreminders.set_launch_triggers(next_launch, calendar, subscriptions)
    finally:
        # let's schedule another check in 24h
        calendar.add_event(time.time() + 24 * 60 * 60 + 30, schedule_launches, args=[calendar])


def schedule_xkcd(calendar):
    now = time.time()

    def check_xkcd():
        new_comic = new_xkcd.check_update(db)
        if new_comic is not None:
            for chat_id in subscriptions.get_subscribers('xkcd'):
                new_comic[0]['chat_id'] = chat_id
                new_comic[1]['chat_id'] = chat_id
                tg.send_photo(new_comic[0])
                tg.send_message(new_comic[1])

    for hour in range(24):
        calendar.add_event(now + 60 * 60 * hour, check_xkcd)
    calendar.add_event(now + 60 * 60 * 24, schedule_xkcd, args=[calendar])


def schedule_events(calendar):
    schedule_launches(calendar)
    schedule_xkcd(calendar)
    reminders.initialize_from_disk(calendar, tg)


# Dict to store the commands of the bot
bot_commands = {}


def start(message):
    current_chat = message['chat']['id']
    user = message['from']['first_name']
    bot_message = 'Hello %s! I am A Bot.' % user
    bot_message += "\n\nHere's a list of my commands:\n\n" + build_command_list(bot_commands)
    data = {'chat_id': current_chat,
            'text': bot_message, }
    tg.send_message(data)


bot_commands['/start'] = start


def help_(message):
    """View list of commands."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Commands:\n\n%s' % build_command_list(bot_commands), }
    tg.send_message(data)


bot_commands['/help'] = help_


def botfather_commands(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': build_command_list(bot_commands, for_botfather=True), }
    tg.send_message(data)


bot_commands['/botfather_commands'] = botfather_commands


def parable(message):
    """Generate reassuring parable."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat, 'text': text_gen.text_gen(1)}
    tg.send_message(data)


bot_commands['/parable'] = parable


def xkcd_command(message):
    """View latest xkcd comic, or view comic specified by number."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    xkcd_regex = re.compile(r'/xkcd(?:@a_group_bot)?(?:\s(\d+|rand(?:om)?))?(?:\s|$)')
    command_opt = xkcd_regex.search(message_text).group(1)

    if command_opt is None:
        comic = xkcd.getLatestComic()
    elif command_opt.startswith('rand'):
        comic = xkcd.getRandomComic()
    else:
        comic = xkcd.getComic(int(command_opt))

    if comic.number != -1:
        title = (comic.getTitle() + ' (#%d)' % comic.number)[:200]
        alt_text = comic.getAltText()
        img_url = comic.getImageLink()

        data = {'chat_id': current_chat, 'caption': title, 'photo': img_url}
        tg.send_photo(data)
        data = {'chat_id': current_chat, 'text': alt_text}
        tg.send_message(data)
    else:
        data = {'chat_id': current_chat, 'text': '%s is not a valid comic number.' % command_opt}
        tg.send_message(data)


bot_commands['/xkcd'] = xkcd_command


def redditlimit(message):
    """Set limit for /redditposts."""
    from_id = message['from']['id']  # respond always in PM
    message_text = message.get('text', None).lower()
    limit_regex = re.compile(r'/redditlimit(?:@a_group_bot)?(?:\s(\d+))?(?:\s|$)')
    command_opt = limit_regex.search(message_text).group(1)

    if command_opt is None:
        bot_message = 'Your current limit is {}. To change, specify a number after /redditlimit (e.g. /redditlimit ' \
                      '5).'.format(reddit.get_redditposts_limit(from_id, db))
    else:
        limit = min(max(int(command_opt), 1), 20)
        reddit.set_redditposts_limit(from_id, limit, db)
        bot_message = 'Limit set to %d.' % limit
    data = {'chat_id': from_id,
            'text': bot_message}
    tg.send_message(data)


bot_commands['/redditlimit'] = redditlimit


def whyme(message):
    """Replace all vowels with the letter y."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    message_text = message.get('text', None)
    whyme_regex = re.compile(r'/whyme(?:@a_group_bot)?(?:\s(.+))?', re.IGNORECASE)
    raw_text = whyme_regex.search(message_text).group(1)
    if raw_text is None:
        bot_message = 'Say something after /whyme (e.g. /whyme What the hell?!)'
    else:
        bot_message = replace_vowels.replace(raw_text)
    data = {'chat_id': current_chat,
            'reply_to_message_id': orig_message_id,
            'text': bot_message}
    tg.send_message(data)


bot_commands['/whyme'] = whyme


def redditposts(message):
    """View posts from the specified subreddit."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    posts_regex = re.compile(r'/redditposts(?:@a_group_bot)?(?:\s(\w+))?(?:\s|$)')
    command_opt = posts_regex.search(message_text).group(1)

    from_id = message['from']['id']
    num_posts = reddit.get_redditposts_limit(from_id, db)
    if command_opt is None:
        bot_message = 'Specify a subreddit after /redditposts (e.g. /redditposts funny)'
    else:
        subreddit = command_opt
        bot_message = reddit.hot_posts(subreddit, num_posts, current_chat, db)
    # noinspection PyUnboundLocalVariable
    data = {'chat_id': current_chat,
            'text': bot_message,
            'disable_web_page_preview': True}
    tg.send_message(data)


bot_commands['/redditposts'] = redditposts


def launch_(message):
    """View information about the next SpaceX launch."""
    current_chat = message['chat']['id']
    # noinspection PyTypeChecker
    send_launch_message(next_launch, current_chat)


bot_commands['/nextlaunch'] = launch_


def wa(message):
    """Interpret statement with WolframAlpha."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    wa_regex = re.compile(r'/wa(?:@a_group_bot)?(?:\s(.+))?')
    command_opt = wa_regex.search(message_text).group(1)
    if command_opt is None:
        bot_message = 'Specify a query after /wa (e.g. /wa calories in a bagel)'
    else:
        # noinspection PyBroadException
        try:
            bot_message = wolfram_alpha.query_wa(command_opt)
        except wolfram_alpha.WolframAlphaException:
            bot_message = 'Error processing query.'

    data = {'chat_id': current_chat,
            'text': bot_message,
            'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands['/wa'] = wa


def reddits(message):
    """View Reddit post specified by link or number."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    chat_type = message['chat']['type']
    reddit_regex = re.compile(r'/reddit(?:@a_group_bot)?(?:\s(\d+|all|http(?:s)?://\S+))?(?:\s|$)')
    command_opt = reddit_regex.search(message_text).group(1)

    if command_opt is None:
        bot_message = 'Specify a url after /reddit (e.g. /reddit https://redd.it/robin)'
        data = {'chat_id': current_chat,
                'text': bot_message,
                'disable_web_page_preview': True}
        tg.send_message(data)
    elif command_opt.isdigit() or command_opt == 'all':
        posts = db['redditposts']
        chat_row = posts.find_one(chat=str(current_chat))
        if chat_row is None:
            bot_message = 'Use /redditposts followed by a subreddit name to use /reddit [number] syntax'
            data = {'chat_id': current_chat,
                    'text': bot_message}
            tg.send_message(data)
            return

        if command_opt.isdigit():
            post = chat_row[command_opt]
            if post is None:
                bot_message = 'Invalid number.'
                data = {'chat_id': current_chat,
                        'text': bot_message}
                tg.send_message(data)
                return

            reddit.post_proxy(post, chat_type, current_chat, tg)

        elif command_opt == 'all' and chat_type == 'private':
            for i in range(1, 21):  # max /redditlimit
                post = chat_row[str(i)]
                if post is None:
                    break
                reddit.post_proxy(post, chat_type, current_chat, tg)


    else:
        url = command_opt
        reddit.post_proxy(url, chat_type, current_chat, tg)


bot_commands['/reddit'] = reddits


def frog(message):
    """View an image of a frog."""
    current_chat = message['chat']['id']
    image_url = rand_frog.main()
    data = {'chat_id': current_chat,
            'photo': image_url, }
    tg.send_photo(data)


bot_commands['/frog'] = frog


def choices(message):
    """Choose between two or more options, separated by a semicolon."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    message_text = message.get('text', None)
    choice_regex = re.compile(r'/choice(?:@a_group_bot)?(?:\s(.+))?', re.I)
    command_opt = choice_regex.search(message_text).group(1)

    if command_opt is None or ';' not in command_opt:
        data = {'chat_id': current_chat,
                'text': 'List two or more options separated by a semicolon.',
                'reply_to_message_id': orig_message_id}
    else:
        data = {'chat_id': current_chat,
                'text': choice.choice(command_opt) + '\n\n(chosen for %s)' % user_name(message['from'])}
    tg.send_message(data)


bot_commands['/choice'] = choices


def bf(message):
    """Execute Brainfuck, including optional input after an optional semicolon."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']

    message_text = message.get('text', None).replace('\n', '')
    # noinspection Annotator
    bf_regex = re.compile(r'/bf(?:@a_group_bot)?(?:\s([\w+-\.,<>\[\]]+))?;?(.+)?(?:\s|$)?', re.I)
    results = bf_regex.search(message_text)
    code = results.group(1)
    user_input = results.group(2)

    if user_input is None:
        input_ = ''
    else:
        input_ = user_input

    def bf_helper():
        response = brainfuck_interpreter.main(code, input_=input_)
        data = {'chat_id': current_chat,
                'text': response,
                'reply_to_message_id': orig_message_id}
        tg.send_message(data)

    multiprocessing.Process(target=bf_helper).start()


bot_commands['/bf'] = bf


def myscore(message):
    """View or change your score."""
    current_chat = message['chat']['id']
    from_id = str(message['from']['id'])
    orig_message_id = message['message_id']
    message_text = message.get('text', None).lower()
    myscore_regex = re.compile(r'/myscore(?:@a_group_bot)?(?:\s([+-]\d+))?(?:\s|$)?')
    score_change = myscore_regex.search(message_text).group(1)

    score_table = db['scores']
    user_score_row = score_table.find_one(user=str(from_id))
    score = user_score_row['score'] if user_score_row else 0

    if score_change is None:
        bot_message = 'Your score is {}. To change it, follow /myscore with a number that starts ' \
                      'with "+" or "-".'.format(score)
    else:
        change = int(score_change)
        if abs(change) > 1000:
            bot_message = 'Absolute change value should be no greater than 1000.'
        else:
            new_score = score + change
            score_table.upsert(dict(user=str(from_id), score=new_score), ['user'])
            bot_message = 'Your score has been updated to %d.' % new_score

    data = {'chat_id': current_chat,
            'text': bot_message,
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


bot_commands['/myscore'] = myscore


def redditguessing(message, nsfw=False):
    """View posts from a random subreddit without the name and try to guess where they're from."""
    current_chat = message['chat']['id']
    num_posts = 6

    subreddit = 'random' if not nsfw else 'randnsfw'

    # side effect of setting the answer in the db
    bot_message = reddit.hot_posts(subreddit, num_posts, current_chat, db, guessing_game=True)
    data = {'chat_id': current_chat,
            'text': bot_message,
            'disable_web_page_preview': True}
    response = tg.send_message(data)[0]

    if nsfw:
        # delete it in 10 seconds (roughly; affected by schedule polling)
        message_id = response['result']['message_id']
        data = {'chat_id': current_chat, 'message_id': message_id}
        bot_scheduler.add_event(time.time() + 10, tg.delete_message, args=[data], force=True)


bot_commands['/redditguess'] = redditguessing


def redditguessing_nsfw(message):
    redditguessing(message, nsfw=True)


bot_commands['/redditguessnsfw'] = redditguessing_nsfw


def reddit_answer(message):
    """Get the answer to the previous /redditguess."""
    current_chat = message['chat']['id']
    answer_row = db['redditguessanswer'].find_one(chat=str(current_chat))
    answer = answer_row['sub'] if answer_row else 'nonexistent'
    bot_message = 'The answer for the last /redditguess is {}.'.format(answer)
    data = {'chat_id': current_chat,
            'text': bot_message}
    tg.send_message(data)


bot_commands['/redditguessanswer'] = reddit_answer


def archive_helper(message, command, archiver):
    """View an archived version of a webpage."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    message_text = message.get('text', None)

    proxy_re = re.compile(r'/{}(?:@a_group_bot)? (\S+) ?'.format(command), re.I)
    url_search = proxy_re.search(message_text)
    if url_search is not None:
        url = url_search.group(1)
        text = archiver(url)
    else:
        # will be handled in the uploading function.
        text = 'Please provide a URL to archive.'

    data = {'chat_id': current_chat,
            'text': text,
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


def archive(message):
    """Archive a page with the archive.is service."""
    archive_helper(message, 'archive', archive_is.archive_message)


bot_commands['/archive'] = archive


def archive2(message):
    """Archive a page with the web.archive.org service."""
    archive_helper(message, 'archive2', web_archive.archive)


bot_commands['/archive2'] = archive2


def subscribe(message):
    """Subscribe to announcements about a topic (launches, xkcd, etc.)."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    sub_re = re.compile(r'/subscribe(?:@a_group_bot)? (\w+) ?')
    sub_search = sub_re.search(message_text)
    if sub_search is None:
        data = {'chat_id': current_chat,
                'text': 'Please follow /subscribe with a topic ID like `xkcd` or `launches`.',
                'parse_mode': 'Markdown'}
    else:
        topic = sub_search.group(1)
        try:
            subscriptions.subscribe(topic, current_chat)
        except helpers.SubscriptionNotFoundError:
            data = {'chat_id': current_chat,
                    'text': 'Please follow /subscribe with a valid topic ID like `xkcd` or `launches`.',
                    'parse_mode': 'Markdown'}
        else:
            data = {'chat_id': current_chat,
                    'text': 'This chat will recieve messages related to `{}`.'.format(topic),
                    'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands['/subscribe'] = subscribe


def unsubscribe(message):
    """Unsubscribe from announcements about a topic (launches, xkcd, etc.)."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    unsub_re = re.compile(r'/unsubscribe(?:@a_group_bot)? (\w+) ?')
    unsub_search = unsub_re.search(message_text)
    if unsub_search is None:
        data = {'chat_id': current_chat,
                'text': 'Please follow /unsubscribe with a topic ID like `xkcd` or `launches`.',
                'parse_mode': 'Markdown'}
    else:
        topic = unsub_search.group(1)
        try:
            subscriptions.unsubscribe(topic, current_chat)
        except helpers.SubscriptionNotFoundError:
            data = {'chat_id': current_chat,
                    'text': 'Please follow /unsubscribe with a valid topic ID like `xkcd` or `launches`.',
                    'parse_mode': 'Markdown'}
        else:
            data = {'chat_id': current_chat,
                    'text': 'This chat will not recieve messages related to `{}`.'.format(topic),
                    'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands['/unsubscribe'] = unsubscribe


def mysubs(message):
    """Get your subscriptions."""
    current_chat = message['chat']['id']
    topics = subscriptions.my_subscriptions(current_chat)
    message = 'Your subscriptions: ' + ' '.join('`{}`'.format(t) for t in topics)
    data = {'chat_id': current_chat,
            'text': message,
            'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands['/mysubs'] = mysubs


def let_me_for_you_helper(domain, command, engine_name, message):
    current_chat = message['chat']['id']
    message_text = message.get('text', None)
    search_query = re.compile(r'/{}(?:@a_group_bot)? ([^/]+)'.format(command), re.I)
    url_search = search_query.search(message_text)

    if url_search is None:
        data = {'chat_id': current_chat,
                'text': 'You need to let me {} something at least.'.format(engine_name)}
    else:
        url = url_search.group(1)
        data = {'chat_id': current_chat,
                'text': domain + urllib.parse.quote_plus(url)}
    tg.send_message(data)


def lmgtfy(message):
    """Let me Google that for you please..."""
    let_me_for_you_helper('http://lmgtfy.com/?q=', 'lmgtfy', 'Google', message)


bot_commands['/lmgtfy'] = lmgtfy


def lmddgtfy(message):
    """Let me DuckDuckGo that for you please..."""
    let_me_for_you_helper('http://lmddgtfy.net/?q=', 'lmddgtfy', 'DuckDuckGo', message)


bot_commands['/lmddgtfy'] = lmddgtfy


def remindme(message):
    # todo refactor to use the db.
    """Get a reminder about a topic."""
    message_text = message.get('text', None)
    user_id = message['from']['id']
    current_chat = message['chat']['id']
    remind_reg = re.compile(r'/remindme(?:@a_group_bot)? ([^"“”/]+) ?(["“][^"“”]+["”])?', re.IGNORECASE)
    remind_search = remind_reg.search(message_text)

    if remind_search is None:
        data = {'chat_id': current_chat,
                'text': 'Please provide a date for the reminder.'}
    else:
        time_str = remind_search.group(1)
        message_text = remind_search.group(2)[1:-1] if remind_search.group(2) else 'Do the thing!'
        data = reminders.parse_reminder(time_str, message_text, user_id, bot_scheduler, tg, current_chat)
    tg.send_message(data)


bot_commands['/remindme'] = remindme


def myreminders(message):
    # todo refactor to use the db.
    """View your reminders."""
    current_chat = message['chat']['id']
    user_id = message['from']['id']

    my_reminders = []

    for ev_time, ev in bot_scheduler.events.items():
        if ev.func == reminders.remind:
            reminder = ev.args[0]
            if reminder.user_id == user_id:
                my_reminders.append((ev_time, reminder.message))

    my_reminders.sort()
    # build response with time and message of each event.
    response = 'Your reminders:\n' + '\n'.join('{}: {}'.format(reminders.format_time(r[0]), r[1]) for r in my_reminders)
    data = {'chat_id': current_chat, 'text': response}
    tg.send_message(data)


bot_commands['/myreminders'] = myreminders


def ud(message):
    """Define a word using Urban Dictionary."""
    message_text = message.get('text', None)
    current_chat = message['chat']['id']
    search_query = re.compile(r'/ud(?:@a_group_bot)? ([^/]+)', re.I)
    term_search = search_query.search(message_text)

    if term_search is None:
        data = {'chat_id': current_chat,
                'text': 'Please follow the command with a search term.'}
    else:
        data = {'chat_id': current_chat,
                'text': urban_dict.build_message(term_search.group(1)),
                'parse_mode': 'Markdown'}

    tg.send_message(data)


bot_commands['/ud'] = ud


def startup_(message):
    """Get a disruptive tech startup idea."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat, 'text': startup.generate()}
    tg.send_message(data)


bot_commands['/startup'] = startup_


def delete(message):
    """Delete this bot message."""
    current_chat = message['chat']['id']
    if 'reply_to_message' not in message.keys() or message['reply_to_message']['from'] != tg.get_me()['result']:
        tg.send_message({'chat_id': current_chat, 'text': 'That command must be used as a reply to a message of mine.'})
        return
    delete_id = message['reply_to_message']['message_id']
    data = {'chat_id': current_chat, 'message_id': delete_id}
    tg.delete_message(data)


bot_commands['/delete'] = delete

# static responses
bot_commands['/helloworld'] = memesseges.helloworld
bot_commands['/lelxd'] = memesseges.lelxD
bot_commands['/lenny'] = memesseges.lenny
bot_commands['/secretcommand'] = memesseges.secretcommand
bot_commands['/settings'] = memesseges.settings
bot_commands['/shrug'] = memesseges.shrug
bot_commands['/source'] = memesseges.source
bot_commands['/utensil'] = memesseges.utensil
bot_commands['/wtf'] = memesseges.wtf
bot_commands['/yyy'] = memesseges.yyy


def handle(response):
    for item in response['result']:
        if 'message' in item.keys():

            message = item['message']

            message_text = message.get('text', None)
            current_chat = message['chat']['id']

            if 'entities' in message.keys():
                entities = message['entities']
                bot_commands_in_message = []
                for entity in entities:
                    if entity['type'] == 'bot_command':
                        command = message_text[entity['offset']:entity['offset'] + entity['length']].lower()
                        if '@' in command:
                            if command[-11:] == 'a_group_bot':
                                bot_commands_in_message.append(command[:-12])
                        else:
                            bot_commands_in_message.append(command)

                if len(bot_commands_in_message) == 1:
                    handle_helper(bot_commands_in_message[0], message, current_chat)

                else:
                    submessages = Telegram.make_submessages(message)
                    for sub, command in zip(submessages, bot_commands_in_message):
                        handle_helper(command, sub, current_chat)


def handle_helper(command, message, current_chat):
    if not tg.is_limited(current_chat):
        # noinspection PyBroadException
        try:
            if command.lower() in bot_commands:
                # call the function stored in bot_commands with message
                bot_commands[command.lower()](message)
        except Exception as e:
            traceback.print_exc()
            pass


def build_command_list(commands, for_botfather=False):
    commands_list = []
    for command in commands:
        if commands[command].__doc__ is not None:
            commands_list.append((command, commands[command].__doc__))

    commands_list = sorted(commands_list)
    if not for_botfather:
        return '\n'.join(['%s - %s' % (name, job) for name, job in commands_list])
    return '\n'.join(['%s - %s' % (name[1:], job) for name, job in commands_list])  # remove leading slash


def send_launch_message(launch, chat_id):
    if launch is None:
        data = {'chat_id': chat_id,
                'text': 'Could not find any upcoming launches.', }
        tg.send_message(data)
    window_open = launch['wsstamp']
    human_local_window_open = datetime.datetime.fromtimestamp(window_open).strftime('%B %d, %Y %H:%M:%S')
    human_gmt_window_open = launch['windowstart']

    window_close = launch['westamp']
    human_local_window_close = datetime.datetime.fromtimestamp(window_close).strftime('%B %d, %Y %H:%M:%S')
    human_gmt_window_close = launch['windowend']

    location_name = launch['location']['name']
    vid_urls = launch['vidURLs']
    launch_name = launch['name']
    missions = []
    for mis in launch['missions']:
        missions.append((mis['name'], mis['typeName'], mis['description']))
    agency = launch['rocket']['agencies'][0]['name']
    for agen in launch['rocket']['agencies'][1:]:
        agency += ', %s' % agen['name']

    message = 'Upcoming %s launch at %s – %s (CA time %s - %s):\n\n' % (
        agency, human_gmt_window_open, human_gmt_window_close, human_local_window_open, human_local_window_close)

    message += '*%s*\n%s\n\nMissions:\n' % (launch_name, location_name)
    for mission in missions:
        message += '*%s* (%s): _%s_\n' % (mission[0], mission[1], mission[2])
    message += '\nVideo:'
    for vid_url in vid_urls:
        message += ' ' + vid_url

    data = {'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True, }
    tg.send_message(data)


if __name__ == '__main__':
    while True:
        try:
            main()
        except (Exception, KeyboardInterrupt) as e:
            if isinstance(e, KeyboardInterrupt):
                sys.exit(0)
            else:
                traceback.print_exc()
                time.sleep(60)
        finally:
            if config.check_online_status and not already_running:
                statuscheck.reliquish_status(tg)
