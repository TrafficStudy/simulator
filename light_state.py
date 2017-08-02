import random

# This is the "basic light", which has a pair of connected red/green lights
class LightState:
    def __init__(self):
        super()
        # period and start determines how lights change
        self.period = 120  # Typical red light duration
        self.half_period = 60
        self.start = 0 #changed from random.randomint(0,100)

    def is_red_at_time(self, time, d):
        start = self.start
     #   if (d & 1) != 0:
     #       start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
     #   if (d & 1) != 0:
     #       start += self.half_period
        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start


"""
Sonny's notes:
^^ Not sure if that's the correct way of making the intersections change 'simultaneously'
Just an observation from running the tests after the changes...
-Occasionally, a distinct intersection would change lights 2 times in one timestamp
-About up to 5 lights on average would change at a time (I think it should be all of them?)
-20 seems like a mode for the wait time (might be irrelevant)
"""