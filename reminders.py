import json
import os
import time

import dateparser

import helpers


def parse_reminder(time_str, message, user_id, calendar, tg, current_chat):
    event_time = dateparser.parse(date_string=time_str.strip())
    if event_time is None:
        invalid_time_message = {'chat_id': current_chat,
                                'text': "Sorry, I couldn't understand that time."}
        return invalid_time_message
    else:
        timestamp = event_time.timestamp()
        set_reminder(timestamp, message, user_id, calendar, tg)
        success_message = {'chat_id': current_chat,
                           'text': 'I will remind you about "{}"'.format(message)}
        return success_message


def set_reminder(timestamp, message, user_id, calendar, tg, save_to_disk=True):
    reminder = Reminder(message, user_id)
    calendar.add_event(timestamp, remind, args=[reminder, tg])
    if save_to_disk:
        _save_event_to_disk(timestamp, reminder.to_dict())


def initialize_from_disk(calendar, tg):
    events = _history_trim_helper(_file_read_helper())
    _filesave_helper(events)

    for event_time in events.keys():
        message = events[event_time]['message']
        user_id = events[event_time]['user_id']
        set_reminder(int(float(event_time)), message, int(user_id), calendar, tg, save_to_disk=False)


def remind(reminder, tg):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')
    data = {'chat_id': reminder.user_id,
            'text': 'Reminder: {}'.format(reminder.message)}
    tg.send_message(data)


def _history_trim_helper(events):
    future_events = dict()
    now = time.time()
    for event_time in events.keys():
        if float(event_time) > now:
            future_events[event_time] = events[event_time]
    return future_events


def _save_event_to_disk(time, event):
    events = _history_trim_helper(_file_read_helper())
    events[time] = event  # will be buggy if multiple events happen at the same time
    _filesave_helper(events)


def _filesave_helper(json_object):
    with open(os.path.join(helpers.folder_path(), 'data', 'reminders.json'), 'w') as f:
        json.dump(json_object, f)


def _file_read_helper():
    try:
        with open(os.path.join(helpers.folder_path(), 'data', 'reminders.json')) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return dict()


class Reminder:
    def __init__(self, message, user_id):
        self.message = message
        self.user_id = user_id

    def __repr__(self):
        return 'Reminder("{}", {})'.format(self.message, self.user_id)

    def to_dict(self):
        return {'message': self.message, 'user_id': self.user_id}