import random

# This is the "basic light", which has a pair of connected red/green lights
class LightState:

    def __init__(self, Intersection):
        super()
        # period and start determines how lights change
        self.period = 120  # Typical red light duration
        self.half_period = 60
        self.start = random.randint(-100, 0)
        #false = red, true = green
        self.state = False
        self.itn = Intersection

    def is_red_at_time(self, time, d, qid):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        fin_state = not ((time - start) % self.period < self.half_period)
        if fin_state != self.state:
            self.state = fin_state
            self.itn.light_change(time, fin_state)
        return fin_state

# Smarter cycle light that resets the cycle whenever a queue reaches over 10 cars
class LightState1(LightState):

    def is_red_at_time(self, time, d, qid):
        if len(self.itn.outgoing_queue[qid]) >= 10:
            self.start = time
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        self.state = not ((time - start) % self.period < self.half_period)
        return self.state

    def next_green(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period

        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start