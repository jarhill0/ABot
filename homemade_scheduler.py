import time


class Scheduler:
    """Schedules events to happen at a specific time. Events scheduled in the past will happen immediately by default"""

    def __init__(self):
        self.events = dict()

    def __repr__(self):
        text = ['Scheduler with {} events.'.format(len(self.events))]
        for key, event in self.events.keys(), self.events.values():
            text.append('{}: {}'.format(key, event))
        return '\n'.join(text)

    def add_event(self, event_time, func, args=None, kwargs=None, force=False, execute_past=True):
        event = Event(func, args if args else [], kwargs if kwargs else {})
        if event_time < time.time():
            # Event is scheduled in the class
            if execute_past:
                event.execute()
                return True
            else:
                return False
        if event_time not in self.events.keys() or force:
            self.events[event_time] = event
            return True
        return False  # failed because an event already exists at that time

    def check_events(self):
        current_time = time.time()
        executed = []
        for event_time in sorted(self.events.keys()):
            if event_time < current_time:
                self.events[event_time].execute()
                executed.append(event_time)
            else:
                break
        for time_ in executed:
            del self.events[time_]


class Event:
    """A representation of a function to execute and its argument."""

    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return '{}(args={}, kwargs={})'.format(self.func.__name__, self.args, self.kwargs)

    def execute(self):
        self.func(*self.args, **self.kwargs)
