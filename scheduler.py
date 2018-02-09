import sched

import time


class SpecialSched(sched.scheduler):
    def __init__(self, tg, timefunc=time.monotonic, delayfunc=time.sleep):
        super().__init__(timefunc=timefunc, delayfunc=delayfunc)
        self.tg = tg.copy()

    def enter(self, delay, priority, action, argument=(), kwargs=None):
        if kwargs is None:
            kwargs = dict()
        kwargs['tg'] = self.tg
        return super().enter(delay, priority, action, argument, kwargs)

    def enterabs(self, time, priority, action, argument=(), kwargs=None):
        if kwargs is None:
            kwargs = dict()
        kwargs['tg'] = self.tg
        return super().enterabs(time, priority, action, argument, kwargs)
