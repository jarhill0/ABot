import datetime

from pawt.exceptions import APIException

from db_handler import db


def remind(reminder, tg):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')

    text = 'Reminder: {}'.format(reminder.message)
    try:
        tg.user(reminder.user_id).chat.send_message(text)
    except APIException:
        pass
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
