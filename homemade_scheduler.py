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

    def add_event(self, event_time, func, args=None, kwargs=None, execute_past=True):
        event = Event(func, args if args else [], kwargs if kwargs else {})
        event_time = int(event_time)
        if event_time < time.time():
            # Event is scheduled in the class
            if execute_past:
                event.execute()
                return True
            else:
                return False
        while event_time in self.events.keys():
            event_time += 1
        self.events[event_time] = event

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

    def clear(self):
        """Remove all events."""
        self.__init__()


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
