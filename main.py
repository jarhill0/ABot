import datetime
import sys
import time

import launchlibrary
import launchreminders
import rand_frog
import reddit
from config import token, owner_un
from telegram import Telegram
from wolfram_alpha import query_wa

tg = Telegram(token)
next_launch = None


def restart():
    global go
    go = False
    time.sleep(1)
    main()


def main():
    launchlibrary.update_json_on_disk()

    global go, tg, next_launch
    tg = Telegram(token)
    next_launch = launchreminders.get_next_launch()
    go = True

    launchreminders.set_launch_triggers(next_launch)

    while go:
        response = tg.get_updates()
        # noinspection PySimplifyBooleanCheck
        if response['result'] != []:
            handle(response)


def handle(response):
    for item in response['result']:
        if 'message' in item.keys():

            message = item['message']

            message_text = message.get('text', None)
            current_chat = message['chat']['id']
            orig_message_id = message['message_id']

            if 'entities' in message.keys():
                entities = message['entities']
                bot_commands = []
                for entity in entities:
                    if entity['type'] == 'bot_command':
                        command = message_text[entity['offset']:entity['offset'] + entity['length']].lower()
                        if '@' in command:
                            if command[-11:] == 'a_group_bot':
                                bot_commands.append(command[:-12])
                        else:
                            bot_commands.append(command)

                for command in bot_commands:
                    if command == '/helloworld':
                        data = {'chat_id': current_chat,
                                'text': 'Hello World!', }
                        tg.send_message(data)
                    elif command == '/start':
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
                    elif command == '/help':
                        data = {'chat_id': current_chat,
                                'text': "Commands:\n"
                                        "\n/redditposts [subreddit] - List 5 hot posts from /r/[subreddit]"
                                        "\n/reddit [shortlink] - Get info on the linked Reddit post."
                                        "\n/wa - Follow with a query to get information from WolframAlpha"
                                        "\n/nextlaunch - Get information on the next SpaceX launch", }
                        tg.send_message(data)
                    elif command == '/settings':
                        data = {'chat_id': current_chat,
                                'text': "At the moment, I have no settings. Sorry."}
                        tg.send_message(data)
                    elif command == '/redditposts':
                        command_block = message_text[message_text.index('/redditposts'):]
                        try:
                            subreddit = command_block.split(' ')[1]
                        except IndexError:
                            bot_message = 'Specify a subreddit after /redditposts (e.g. /redditposts funny)'
                            continue
                        else:
                            bot_message = reddit.hot_posts(subreddit, 5)
                        finally:
                            data = {'chat_id': current_chat,
                                    'text': bot_message,
                                    'disable_web_page_preview': True}
                            tg.send_message(data)
                    elif command == '/stop':
                        username = message['from'].get('username', None)
                        if username == owner_un and time.time() - message['date'] < 15:
                            sys.exit()
                    elif command == '/nextlaunch':
                        send_launch_message(next_launch, current_chat)
                    elif command == '/secretcommand':
                        data = {'chat_id': current_chat,
                                'text': "doesn’t work any more, you cheeky devil :)",
                                'reply_to_message_id': orig_message_id}
                        tg.send_message(data)
                    elif command == '/wa':
                        command_block = message_text[message_text.index('/wa') + 3:].strip()
                        if command_block == '':
                            bot_message = 'Specify a query after /wa (e.g. /wa calories in a bagel)'
                        else:
                            try:
                                bot_message = query_wa(command_block)
                            except (KeyError, AttributeError):
                                bot_message = 'Error processing query.'
                        data = {'chat_id': current_chat,
                                'text': bot_message,
                                'parse_mode': 'Markdown'}
                        tg.send_message(data)
                    elif command == '/reddit':
                        command_block = message_text[message_text.index('/reddit'):]

                        try:
                            url = command_block.split(' ')[1]
                        except IndexError:
                            bot_message = 'Specify a url after /reddit (e.g. /reddit https://redd.it/robin)'
                            data = {'chat_id': current_chat,
                                    'text': bot_message,
                                    'disable_web_page_preview': True,
                                    }
                            tg.send_message(data)
                            continue
                        else:
                            text, is_image, image_url = reddit.post_proxy(url)
                            if not is_image:
                                data = {'chat_id': current_chat,
                                        'text': text,
                                        'disable_web_page_preview': False,
                                        }
                                tg.send_message(data)
                            else:
                                data = {'chat_id': current_chat,
                                        'photo': image_url,
                                        }
                                if len(text) >= 200:
                                    text = text[:199] + '…'
                                data['caption'] = text
                                tg.send_photo(data)

                    elif command == '/frogs':
                        image_url = rand_frog.main()
                        data = {'chat_id': current_chat,
                                'photo': image_url, }
                        tg.send_photo(data)


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
