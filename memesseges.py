import memetext

tg = None


def globalize_tg(tg_from_main):
    global tg
    tg = tg_from_main


def helloworld(message):
    """Say hello."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Hello World!'}
    tg.send_message(data)


def source(message):
    """View source."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': 'Inspect my insides! http://github.com/jarhill0/ABot'}
    tg.send_message(data)


def settings(message):
    """View available settings."""
    current_chat = message['from']['id']  # respond always in PM
    data = {'chat_id': current_chat,
            'text': memetext.settings,
            'parse_mode': 'Markdown'}
    tg.send_message(data)


def shrug(message):
    """¯\_(ツ)_/¯."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '¯\_(ツ)_/¯', }
    tg.send_message(data)


def lenny(message):
    """( ͡° ͜ʖ ͡°)."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': '( ͡° ͜ʖ ͡°)', }
    tg.send_message(data)


def utensil(message):
    """Holds up spork."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': memetext.spork}
    tg.send_message(data)


def wtf(message):
    """What the hell."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': memetext.marines}
    tg.send_message(data)


def yyy(message):
    """Whyt thy hyll."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': memetext.myrynys}
    tg.send_message(data)


def secretcommand(message):
    current_chat = message['chat']['id']
    orig_message_id = message['message_id']
    data = {'chat_id': current_chat,
            'text': "Doesn't work any more, you cheeky devil :)",
            'reply_to_message_id': orig_message_id}
    tg.send_message(data)


def lelxD(message):
    """lel xD."""
    current_chat = message['chat']['id']
    data = {'chat_id': current_chat,
            'text': memetext.xD}
    tg.send_message(data)
