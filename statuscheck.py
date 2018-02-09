import time

from requests.exceptions import ConnectionError


class StatusChecker:
    ONLINE_TEXT = 'A Bot is online.'
    OFFLINE_TEXT = 'A Bot is offline.'

    def __init__(self, tg, channel_id):
        self.channel = tg.chat(channel_id)

    def already_running(self):
        """Returns True is an instance of A Bot is running"""
        self.channel.get_chat()
        name = self.channel.title
        return name == StatusChecker.ONLINE_TEXT

    def claim_status(self):
        """Claims that the bot is running."""
        self.channel.set_title(StatusChecker.ONLINE_TEXT)

    def reliquish_status(self):
        """Removes claim that bot is running"""
        try:
            self.channel.set_title(StatusChecker.OFFLINE_TEXT)
        except ConnectionError:
            delay = 5
            print('Error relinquishing status. Trying again  in {} seconds'.format(delay))
            time.sleep(delay)

            try:
                self.channel.set_title(StatusChecker.OFFLINE_TEXT)
            except ConnectionError:
                print('Error relinquishing status. Exiting.')


class StatusDummy(StatusChecker):
    """To be used when status checking should not be performed."""

    def __init__(self):
        self.channel = None

    def already_running(self):
        return False

    def claim_status(self):
        pass

    def reliquish_status(self):
        pass


if __name__ == '__main__':
    from pawt import Telegram
    import config

    StatusChecker(Telegram(config.token), config.status_channel_id).reliquish_status()
