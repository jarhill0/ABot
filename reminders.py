import datetime
import logging

from pawt.exceptions import APIException
from pawt.models.reply_markup import InlineKeyboardMarkupBuilder

from db_handler import db

logging.basicConfig(filename='bot.log', level=logging.WARNING)


def remind(reminder, tg):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')

    text = 'Reminder: {}'.format(reminder.message)
    builder = InlineKeyboardMarkupBuilder()
    builder.add_button('Snooze (10 min)', callback_data='reminder:{u}:{m}'.format(u=reminder.user_id,
                                                                                  m=reminder.message))
    try:
        tg.user(reminder.user_id).chat.send_message(text, reply_markup=builder.build())
    except APIException:
        try:
            tg.user(reminder.user_id).chat.send_message(text)  # markup callback data too long...
        except APIException:
            logging.exception('Reminder exception')
    db['reminders'].delete(time=reminder.time, message=reminder.message, user_id=reminder.user_id)


def format_time(ev_time):
    if isinstance(ev_time, (int, float)):
        ev_time = datetime.datetime.fromtimestamp(ev_time)
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
