import random

# This is the "basic light", which has a pair of connected red/green lights
class LightState:
    def __init__(self):
        super()
        # period and start determines how lights change
        self.period = 1000000  # Typical red light duration
        self.half_period = 500000
        self.start = random.randint(0, 100)
    # gets the start time, checks if
    def is_red_at_time(self, time, d):
        start = self.start
        if (d & 1):
            start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
        if (d & 1):
            start += self.half_period

        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start


