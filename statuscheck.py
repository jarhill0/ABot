import config

ONLINE_TEXT = 'A Bot is online.'
OFFLINE_TEXT = 'A Bot is offline.'


def already_running(tg):
    """Returns True is an instance of A Bot is running"""
    data = {'chat_id': config.status_channel_id}
    response = tg.get_chat(data)
    name = response['result']['title']
    return name == ONLINE_TEXT


def claim_status(tg):
    """Claims that the bot is running."""
    data = {'chat_id': config.status_channel_id, 'title': ONLINE_TEXT}
    tg.set_chat_title(data)


def reliquish_status(tg):
    """Removes claim that bot is running"""
    data = {'chat_id': config.status_channel_id, 'title': OFFLINE_TEXT}
    tg.set_chat_title(data)


if __name__ == '__main__':
    import telegram

    reliquish_status(telegram.Telegram(config.token))
