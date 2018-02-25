import requests


def add(message, text):
    """Follow with a link to add to http://telegramusic.ml."""
    words = text.partition(' ')[2].split()
    if not words:
        message.reply('Please provide a link.')
        return

    user = message.user
    name = user.full_name if user else 'a friend'  # message might not have a user
    link = words[0]
    response = requests.post('http://telegramusic.ml/add/',
                             data={'url': link, 'name': name})
    if response.status_code == 200:
        id_ = response.json()['id']
        message.reply('Your song is live at http://telegramusic.ml/{}/'.format(id_))
    else:
        message.reply('Could not add that link. Try another?')
