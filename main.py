import traceback

from pawt.bots import MappedCommandBot

import config
import memetext


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

        super().__init__(token, text_command_map, caption_command_map, url=url, session=session)

    @staticmethod
    def _plaintext_helper(message, text, *args, **kwargs):
        message.chat.send_message(text, *args, **kwargs)

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

    def secretcommand(self, message, unused):
        message.reply.send_message("Doesn't work any more, you cheeky devil :)")

    # noinspection PyPep8Naming
    def lelxD(self, message, unused):
        """lel xD."""
        self._plaintext_helper(message, memetext.xD)


def main():
    bot = ABot(config.token)
    while True:
        try:
            bot.run()
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
