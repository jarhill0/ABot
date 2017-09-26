import dateparser


def parse_reminder(time_str, message, user_id, calendar, tg, current_chat):
    event_time = dateparser.parse(date_string=time_str, languages=['en'])
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


def set_reminder(timestamp, message, user_id, calendar, tg):
    reminder = Reminder(message, user_id)
    calendar.add_event(timestamp, remind, args=[reminder, tg])


def remind(reminder, tg):
    if not isinstance(reminder, Reminder):
        raise ValueError('reminder is not a Reminder.')
    data = {'chat_id': reminder.user_id,
            'text': 'Reminder: {}'.format(reminder.message)}
    tg.send_message(data)


class Reminder:
    def __init__(self, message, user_id):
        self.message = message
        self.user_id = user_id

    def __repr__(self):
        return 'Reminder("{}", {})'.format(self.message, self.user_id)
