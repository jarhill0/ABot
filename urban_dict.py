import requests
from pawt.models.reply_markup import InlineKeyboardMarkupBuilder

API_PATH = 'http://api.urbandictionary.com/v0/define'


def send_message(chat, term, index=0):
    ud_response = requests.get(API_PATH, params={'term': term}).json()
    if ud_response['result_type'] != 'exact':  # unknown how many possible responses the API gives here
        return 'No definition found for {}.'.format(term)
    index = 0 if index >= len(ud_response['list']) else index
    entry = ud_response['list'][index]
    word = entry['word']
    definition = entry['definition']
    example = entry['example']

    builder = InlineKeyboardMarkupBuilder()
    if index != len(ud_response['list']) - 1:  # not the last one
        builder.add_button('Next definition', callback_data='ud:{}:{}:{}'.format(chat.id, index + 1, term))

    chat.send_message('*{}*:\n{}\n_{}_'.format(word, definition, example), parse_mode='Markdown',
                      reply_markup=builder.build())
