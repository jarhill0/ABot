import requests


def add(message, text):
    """Follow with a link to add to https://telegramusic.appspot.com."""
    words = text.partition(' ')[2].split()
    if not words:
        message.reply('Please provide a link.')
        return

    user = message.user
    name = user.full_name if user else 'a friend'  # message might not have a user
    link = words[0]
    response = requests.post('https://telegramusic.appspot.com/add/',
                             data={'url': link, 'name': name})
    if response.status_code == 200:
        location = response.json()['link']
        message.reply('Your song is live at https://telegramusic.appspot.com{}'.format(location))
    else:
        message.reply('Could not add that link. Try another?')
