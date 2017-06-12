import datetime
import sys
import time
import traceback

import brainfuck_interpreter
import choice
import config
import launchlibrary
import launchreminders
import rand_frog
import reddit
import text_gen
import xkcd
from telegram import Telegram, user_name
from wolfram_alpha import query_wa

tg = Telegram(config.token)
next_launch = None


def restart():
    time.sleep(10)
    global next_launch
    launchlibrary.update_json_on_disk()
    next_launch = launchreminders.get_next_launch()
    launchreminders.set_launch_triggers(next_launch)


def main():
    launchlibrary.update_json_on_disk()

    global tg, next_launch
    tg = Telegram(config.token)
    next_launch = launchreminders.get_next_launch()
    launchreminders.set_launch_triggers(next_launch)
    last_time = time.time() - (60 * 61)

    while True:
        response = tg.get_updates()
        # noinspection PySimplifyBooleanCheck
        if response['result'] != []:
            handle(response)
        if time.time() - 60 * 60 > last_time:
            last_time = time.time()
            new_comic = xkcd.check_update()
            if new_comic is not None:
                tg.send_photo(new_comic[0])
                tg.send_message(new_comic[1])


# Dict to store the commands of the bot
bot_commands = {}


def helloworld(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Hello World!'}
    tg.send_message(data)


bot_commands["/helloworld"] = helloworld


def source(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Inspect my insides! http://github.com/jarhill0/ABot'}
    tg.send_message(data)


bot_commands["/source"] = source


def start(message):
    current_chat = message['chat']['id']
    user = message['from']['first_name']
    bot_message = 'Hello %s! I am A Bot.' % user
    bot_message += "\n\nHere's a list of my commands:" \
                   "\n/redditposts [subreddit] - List 5 hot posts from /r/[subreddit]" \
                   "\n/reddit [shortlink] - Get info on the linked Reddit post." \
                   "\n/wa - Follow with a query to get information from WolframAlpha" \
                   "\n/nextlaunch - Get information on the next SpaceX launch"
    data = {'chat_id': current_chat,
            'text': bot_message, }
    tg.send_message(data)


bot_commands["/start"] = start


def help_(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': "Commands:\n"
                    "\n/redditposts [subreddit] - List 5 hot posts from /r/[subreddit]"
                    "\n/reddit [shortlink] - Get info on the linked Reddit post."
                    "\n/wa - Follow with a query to get information from WolframAlpha"
                    "\n/nextlaunch - Get information on the next SpaceX launch", }
    tg.send_message(data)


bot_commands["/help"] = help_


def settings(message):
    current_chat = message['from']['id']  # respond always in PM
    data = {'chat_id': current_chat,
            'text': "Current settings:\n/redditlimit followed by a number to set limit of reddit posts displayed by /redditposts (example usage: /redditlimit 5)"}
    tg.send_message(data)


bot_commands["/settings"] = settings


def parable(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat, 'text': text_gen.text_gen(1)}
    tg.send_message(data)


bot_commands['/parable'] = parable


def redditlimit(message):
    from_id = message['from']['id']  # respond always in PM
    message_text = message.get('text', None)
    command_block = message_text[message_text.index('/redditlimit'):]
    try:
        limit = max(min(int(command_block.split(' ')[1]), 20), 1)
    except (IndexError, ValueError):
        bot_message = 'Specify a number after /redditlimit (e.g. /redditlimit 5)'
    else:
        reddit.set_redditposts_limit(from_id, limit)
        bot_message = 'Limit set to %d.' % limit
    finally:
        data = {'chat_id': from_id,
                'text': bot_message}
        tg.send_message(data)


bot_commands['/redditlimit'] = redditlimit


def shrug(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '¯\_(ツ)_/¯', }
    tg.send_message(data)


bot_commands["/shrug"] = shrug


def lenny(message):
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '( ͡° ͜ʖ ͡°)', }
    tg.send_message(data)


bot_commands['/lenny'] = lenny


def redditposts(message):
    current_chat = message['chat']['id']
    message_text = message.get('text', None)
    command_block = message_text[message_text.index('/redditposts'):]
    from_id = message['from']['id']
    num_posts = reddit.get_redditposts_limit(from_id)
    try:
        subreddit = command_block.split(' ')[1]
        bot_message, posts_dict = reddit.hot_posts(subreddit, num_posts)
    except IndexError:
        bot_message = 'Specify a subreddit after /redditposts (e.g. /redditposts funny)'
    finally:
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


def stop(message):
    username = message['from'].get('username', None)
    if (username == config.owner_un or username in config.owner_uns) and time.time() - \
            message[
                'date'] < 15:
        sys.exit()


bot_commands["/stop"] = stop


def launch_(message):
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
    current_chat = message['chat']['id']
    message_text = message.get('text', None)
    command_block = message_text[message_text.index('/wa') + 3:].strip()
    if command_block == '':
        bot_message = 'Specify a query after /wa (e.g. /wa calories in a bagel)'
    else:
        # noinspection PyBroadException
        try:
            bot_message = query_wa(command_block)
        except:
            bot_message = 'Error processing query.'
    data = {'chat_id': current_chat,
            'text': bot_message,
            'parse_mode': 'Markdown'}
    tg.send_message(data)


bot_commands["/wa"] = wa


def reddits(message):
    current_chat = message['chat']['id']
    message_text = message.get('text', None)
    chat_type = message['chat']['type']
    command_block = message_text[message_text.index('/reddit'):]

    try:
        input_url = command_block.split(' ')[1]
    except IndexError:
        bot_message = 'Specify a url after /reddit (e.g. /reddit https://redd.it/robin)'
        data = {'chat_id': current_chat,
                'text': bot_message,
                'disable_web_page_preview': True,
                }
        tg.send_message(data)
    else:
        if input_url.isdigit():
            valid_id, tentative_url = reddit.get_post_from_dict(current_chat,
                                                                int(input_url))
            if valid_id and tentative_url is not None:
                url = tentative_url
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
        else:
            url = input_url
        text, is_image, image_url = reddit.post_proxy(url, chat_type)
        if not is_image:
            data = {'chat_id': current_chat,
                    'text': text,
                    'disable_web_page_preview': False,
                    }
            tg.send_message(data)
        else:
            data = {'chat_id': current_chat,
                    'photo': image_url
                    }
            if len(text) >= 200:
                text = text[:199] + '…'
            data['caption'] = text
            tg.send_photo(data)


bot_commands["/reddit"] = reddits


def frog(message):
    current_chat = message['chat']['id']
    image_url = rand_frog.main()
    data = {'chat_id': current_chat,
            'photo': image_url, }
    tg.send_photo(data)


bot_commands["/frog"] = frog
bot_commands["/frogs"] = frog


def choices(message):
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    message_text = message.get('text', None)
    command_block = message_text[message_text.index('/choice') + 8:]
    print(command_block)
    if ';' not in command_block:
        data = {'chat_id': current_chat,
                'text': 'List two or more options separated by a semicolon.',
                'reply_to_message_id': orig_message_id}
    else:
        data = {'chat_id': current_chat,
                'text': choice.choice(command_block) + '\n\n(chosen for ' + user_name(
                    message['from']) + ')', }
    print(data)
    tg.send_message(data)


bot_commands["/choice"] = choices


def bf(message):
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']

    message_text = message.get('text', None)
    command_block = message_text[message_text.index('/bf') + 3:]
    input_ = ''
    if ';' in command_block:
        input_ = command_block[command_block.index(';') + 1:]
        command_block = command_block[:command_block.index(';')]
    response = brainfuck_interpreter.main(command_block, input_=input_)
    data = {'chat_id': current_chat,
            'text': response,
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


bot_commands["/bf"] = bf


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
                            if command in bot_commands:
                                # call the function stored in bot_commands with message
                                bot_commands[command.lower()](message)
                        except BaseException as e:
                            traceback.print_exc()
                            print(type(e))
                            print(e)
                            pass


def send_launch_message(launch, chat_id):
    launch_time = launch['wsstamp']
    human_local_launch_time = datetime.datetime.fromtimestamp(launch_time).strftime('%B %d, %Y %H:%M:%S')
    human_gmt_launch_time = launch['windowstart']
    location_name = launch['location']['name']
    vid_urls = launch['vidURLs']
    launch_name = launch['name']
    missions = []
    for mis in launch['missions']:
        missions.append((mis['name'], mis['typeName'], mis['description']))
    agency = launch['rocket']['agencies'][0]['name']
    for agen in launch['rocket']['agencies'][1:]:
        agency += ', %s' % agen['name']

    message = 'Upcoming %s launch at %s (CA time %s):\n\n' % (agency, human_gmt_launch_time, human_local_launch_time)
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
    main()
