import random
import copy

# This is the "basic light", which has a pair of connected red/green lights
class LightState:

    def __init__(self, n_from, n_to, out_going_queue):
        super()
        # period and start determines how lights change
        self.period = 120  # Typical red light duration
        self.half_period = 60
        self.start = random.randint(0, 100)
        self.out_going_queue = copy.copy(out_going_queue)

    def is_red_at_time(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period

        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start

class LightState1(LightState):

    def is_red_at_time(self, time, d, qid):
        if len(self.out_going_queue[qid]) >= 10:
            self.start = time
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period

        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start