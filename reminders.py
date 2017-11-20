import datetime

import dateparser


def parse_reminder(time_str, message, user_id, calendar, tg, current_chat, db):
    ev_time = dateparser.parse(date_string=time_str.strip(), settings={'PREFER_DATES_FROM': 'future'})
    if ev_time is None:
        invalid_time_message = {'chat_id': current_chat,
                                'text': "Sorry, I couldn't understand that time."}
        return invalid_time_message
    else:
        timestamp = ev_time.timestamp()
        set_reminder(timestamp, message, user_id, calendar, tg, db)
        time_str = format_time(ev_time)
        success_message = {'chat_id': current_chat,
                           'text': 'I will remind you about "{}" at {}.'.format(message, time_str)}
        return success_message


def set_reminder(timestamp, message, user_id, calendar, tg, db=None, save_to_db=True):
    reminder = Reminder(message, user_id, timestamp)
    calendar.add_event(timestamp, remind, args=[reminder, tg, db])
    if save_to_db:
        db['reminders'].insert(dict(time=timestamp, message=message, user_id=user_id))


def load_from_db(db, calendar, tg):
    table = db['reminders']
    if table.count() != 0:
        for row in table:
            set_reminder(row['time'], row['message'], row['user_id'], calendar, tg, save_to_db=False)


def remind(reminder, tg, db):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')
    data = {'chat_id': reminder.user_id,
            'text': 'Reminder: {}'.format(reminder.message)}
    tg.send_message(data)
    db['reminders'].delete(time=reminder.time, message=reminder.message, user_id=reminder.user_id)


def format_time(ev_time):
    if isinstance(ev_time, int):
        ev_time = datetime.datetime.fromtimestamp(ev_time)
    if not isinstance(ev_time, datetime.datetime):
        raise TypeError('ev_time should be int or datetime.')
    return '{}-{}-{} {:02}:{:02}'.format(ev_time.year, ev_time.month, ev_time.day, ev_time.hour, ev_time.minute)


class Reminder:
    def __init__(self, message, user_id, time=None):
        self.message = message
        self.user_id = user_id
        self.time = time

    def __repr__(self):
        return 'Reminder("{}", {})'.format(self.message, self.user_id)

    def to_dict(self):
        return {'message': self.message, 'user_id': self.user_id}
