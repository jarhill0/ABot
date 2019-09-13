import datetime
import logging

from pawt import MAX_LENGTH
from pawt.exceptions import APIException
from pawt.models.reply_markup import InlineKeyboardMarkupBuilder

from db_handler import db

logging.basicConfig(filename='bot.log', level=logging.WARNING)


def remind(reminder, tg):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')

    text = 'Reminder: {}'.format(reminder.message)[:MAX_LENGTH['text']]
    builder = InlineKeyboardMarkupBuilder()
    builder.add_button('Snooze (10 min)', callback_data='reminder:10:')
    builder.new_row()
    builder.add_button('Snooze (1 hour)', callback_data='reminder:60:')
    try:
        tg.user(reminder.user_id).chat.send_message(text, reply_markup=builder.build())
    except APIException:
        logging.exception('Reminder exception')
    db['reminders'].delete(time=reminder.time, message=reminder.message, user_id=reminder.user_id)


def format_time(ev_time, user_tz=None):
    if isinstance(ev_time, (int, float)):
        ev_time = datetime.datetime.fromtimestamp(ev_time, tz=user_tz)
    if not isinstance(ev_time, datetime.datetime):
        raise TypeError('ev_time should be int or datetime.')
    return '{}-{}-{} {:02}:{:02}'.format(ev_time.year, ev_time.month, ev_time.day, ev_time.hour, ev_time.minute)


class Reminder:
    def __init__(self, message, user_id, timestamp):
        self.message = str(message)
        self.user_id = str(user_id)
        self.time = timestamp

    def __repr__(self):
        return 'Reminder("{}", {})'.format(self.message, self.user_id)

    def to_dict(self):
        return {'message': self.message, 'user_id': self.user_id}


def set_timezone(user_id, offset):
    """Save a user's offset from UTC."""
    timezone = db['timezone']
    timezone.upsert({'user': str(user_id), 'offset': offset}, ['user'])


def get_timezone(user_id):
    timezone = db['timezone']
    user_row = timezone.find_one(user=str(user_id))
    if user_row is None:
        return None
    offset = user_row['offset']
    return datetime.timezone(datetime.timedelta(hours=offset))
