import datetime
import re
import time
import traceback

import xkcd

import archive_is
import brainfuck_interpreter
import choice
import config
import launchlibrary
import launchreminders
import new_xkcd
import rand_frog
import reddit
import scores
import text_gen
from telegram import Telegram, user_name
from wolfram_alpha import query_wa

tg = Telegram(config.token)
next_launch = None


def restart():
    time.sleep(10)
    global next_launch
    launchlibrary.update_json_on_disk()
    try:
        next_launch = launchreminders.get_next_launch()
    except IndexError:
        # there is no next launch
        pass
    else:
        launchreminders.set_launch_triggers(next_launch)


def main():
    launchlibrary.update_json_on_disk()

    global tg, next_launch
    tg = Telegram(config.token)
    try:
        next_launch = launchreminders.get_next_launch()
    except IndexError:
        # there is no next launch
        pass
    else:
        launchreminders.set_launch_triggers(next_launch)
    last_time = time.time() - (60 * 61)

    while True:
        response = tg.get_updates()
        # noinspection PySimplifyBooleanCheck
        if response['result'] != []:
            handle(response)
        if time.time() - 60 * 60 > last_time:
            last_time = time.time()
            new_comic = new_xkcd.check_update()
            if new_comic is not None:
                tg.send_photo(new_comic[0])
                tg.send_message(new_comic[1])


# Dict to store the commands of the bot
bot_commands = {}


def helloworld(message):
    """Say hello."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Hello World!'}
    tg.send_message(data)


bot_commands["/helloworld"] = helloworld


def source(message):
    """View source."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Inspect my insides! http://github.com/jarhill0/ABot'}
    tg.send_message(data)


bot_commands["/source"] = source


def start(message):
    current_chat = message['chat']['id']
    user = message['from']['first_name']
    bot_message = 'Hello %s! I am A Bot.' % user
    bot_message += "\n\nHere's a list of my commands:\n\n" + build_command_list(bot_commands)
    data = {'chat_id': current_chat,
            'text': bot_message, }
    tg.send_message(data)


bot_commands["/start"] = start


def help_(message):
    """View list of commands."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Commands:\n\n%s' % build_command_list(bot_commands), }
    tg.send_message(data)


bot_commands["/help"] = help_


def settings(message):
    """View available settings."""
    current_chat = message['from']['id']  # respond always in PM
    data = {'chat_id': current_chat,
            'text': "Current settings:\n/redditlimit followed by a number to set limit of reddit posts displayed by"
                    "/redditposts (example usage: /redditlimit 5)"}
    tg.send_message(data)


bot_commands["/settings"] = settings


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
        bot_message = 'Specify a number after /redditlimit (e.g. /redditlimit 5)'
    else:
        limit = min(max(int(command_opt), 1), 20)
        reddit.set_redditposts_limit(from_id, limit)
        bot_message = 'Limit set to %d.' % limit
    data = {'chat_id': from_id,
            'text': bot_message}
    tg.send_message(data)


bot_commands['/redditlimit'] = redditlimit


def shrug(message):
    """¯\_(ツ)_/¯."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '¯\_(ツ)_/¯', }
    tg.send_message(data)


bot_commands["/shrug"] = shrug


def lenny(message):
    """( ͡° ͜ʖ ͡°)."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '( ͡° ͜ʖ ͡°)', }
    tg.send_message(data)


bot_commands['/lenny'] = lenny


def redditposts(message):
    """View posts from the specified subreddit."""
    current_chat = message['chat']['id']
    message_text = message.get('text', None).lower()
    posts_regex = re.compile(r'/redditposts(?:@a_group_bot)?(?:\s(\w+))?(?:\s|$)')
    command_opt = posts_regex.search(message_text).group(1)

    from_id = message['from']['id']
    num_posts = reddit.get_redditposts_limit(from_id)
    if command_opt is None:
        bot_message = 'Specify a subreddit after /redditposts (e.g. /redditposts funny)'
    else:
        subreddit = command_opt
        bot_message, posts_dict = reddit.hot_posts(subreddit, num_posts)
    # noinspection PyUnboundLocalVariable
    data = {'chat_id': current_chat,
            'text': bot_message,
            'disable_web_page_preview': True}
    tg.send_message(data)
    try:
        # noinspection PyUnboundLocalVariable
        if posts_dict is not None:
            # noinspection PyUnboundLocalVariable
            reddit.add_posts_to_dict(current_chat, posts_dict)
    except NameError:
        pass


bot_commands["/redditposts"] = redditposts


def launch_(message):
    """View information about the next SpaceX launch."""
    current_chat = message['chat']['id']
    send_launch_message(next_launch, current_chat)


bot_commands["/nextlaunch"] = launch_


def secretcommand(message):
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    data = {'chat_id': current_chat,
            'text': "Doesn't work any more, you cheeky devil :)",
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


bot_commands["/secretcommand"] = secretcommand


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
            bot_message = query_wa(command_opt)
        except:
            bot_message = 'Error processing query.'

    data = {'chat_id': current_chat,
            'text': bot_message,
            'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands["/wa"] = wa


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
                'disable_web_page_preview': True,
                }
        tg.send_message(data)
    else:
        if command_opt.isdigit():
            valid_id, tentative_url = reddit.get_post_from_dict(current_chat, int(command_opt))
            if valid_id and tentative_url is not None:
                url = tentative_url
                reddit.post_proxy(url, chat_type, current_chat, tg)
            else:
                if not valid_id:
                    bot_message = 'Use /redditposts followed by a subreddit name to use /reddit [number] syntax',
                elif tentative_url is None:
                    bot_message = 'Invalid number.'
                data = {'chat_id': current_chat,
                        'text': bot_message,
                        'disable_web_page_preview': True
                        }
                tg.send_message(data)
        elif command_opt == 'all' and chat_type == 'private':
            for i in range(1, len(reddit.reddit_posts_dict[current_chat]) + 1):
                valid_id, tentative_url = reddit.get_post_from_dict(current_chat, i)
                if valid_id and tentative_url is not None:
                    url = tentative_url
                reddit.post_proxy(url, chat_type, current_chat, tg)

        else:
            url = command_opt
            reddit.post_proxy(url, chat_type, current_chat, tg)


bot_commands["/reddit"] = reddits


def frog(message):
    """View an image of a frog."""
    current_chat = message['chat']['id']
    image_url = rand_frog.main()
    data = {'chat_id': current_chat,
            'photo': image_url, }
    tg.send_photo(data)


bot_commands["/frog"] = frog


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


bot_commands["/choice"] = choices


def bf(message):
    """Execute Brainfuck, including optional input after an optional semicolon."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']

    message_text = message.get('text', None)
    bf_regex = re.compile(r'/bf(?:@a_group_bot)?(?:\s([\w+-\.,<>\[\]]+))?;?(.+)?(?:\s|$)?', re.I)
    results = bf_regex.search(message_text)
    code = results.group(1)
    user_input = results.group(2)

    if user_input is None:
        input_ = ''
    else:
        input_ = user_input
    response = brainfuck_interpreter.main(code, input_=input_)
    data = {'chat_id': current_chat,
            'text': response,
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


bot_commands["/bf"] = bf


def myscore(message):
    """View or change your score."""
    current_chat = message['chat']['id']
    from_id = str(message['from']['id'])
    orig_message_id = message['message_id']
    message_text = message.get('text', None).lower()
    myscore_regex = re.compile(r'/myscore(?:@a_group_bot)?(?:\s([+-]\d+))?(?:\s|$)?')
    score_change = myscore_regex.search(message_text).group(1)

    if score_change is None:
        bot_message = 'Your score is %d. To change it, follow /myscore with a number that starts ' \
                      'with "+" or "-".' % scores.get_score(from_id)
    else:
        change = int(score_change)
        if abs(change) > 1000:
            bot_message = 'Absolute change value should be no greater than 1000.'
        else:
            scores.change_score(from_id, change)
            bot_message = 'Your score has been updated to %d.' % scores.get_score(from_id)

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
    bot_message, posts_dict = reddit.hot_posts(subreddit, num_posts, guessing_game=True)
    data = {'chat_id': current_chat,
            'text': bot_message,
            'disable_web_page_preview': True}
    tg.send_message(data)
    try:
        if posts_dict is not None:
            reddit.add_posts_to_dict(current_chat, posts_dict)
    except NameError:
        pass


bot_commands['/redditguess'] = redditguessing


def redditguessing_nsfw(message):
    redditguessing(message, nsfw=True)


bot_commands['/redditguessnsfw'] = redditguessing_nsfw


def archive(message):
    """View an archived version of a webpage."""
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    message_text = message.get('text', None)

    proxy_re = re.compile(r'/archive(?:@a_group_bot)? (\S+) ?', re.I)
    url_search = proxy_re.search(message_text)
    if url_search is not None:
        url = url_search.group(1)
    else:
        # will be handled in the uploading function.
        url = None

    data = {'chat_id': current_chat,
            'text': archive_is.archive_message(url),
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


bot_commands['/archive'] = archive


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

                for command in bot_commands_in_message:
                    if not tg.is_limited(current_chat):
                        try:
                            if command.lower() in bot_commands:
                                # call the function stored in bot_commands with message
                                bot_commands[command.lower()](message)
                        except BaseException as e:
                            traceback.print_exc()
                            print(type(e))
                            print(e)
                            pass


def build_command_list(commands):
    commands_list = []
    for command in commands:
        if commands[command].__doc__ is not None:
            commands_list.append((command, commands[command].__doc__))

    commands_list = sorted(commands_list)
    return '\n'.join(['%s - %s' % (name, job) for name, job in commands_list])


def test():
    print(build_command_list(bot_commands))


def send_launch_message(launch, chat_id):
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
        except Exception as e:
            if e is KeyboardInterrupt:
                raise e
            else:
                traceback.print_exc()
                time.sleep(60)
