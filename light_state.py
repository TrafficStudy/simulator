import random

# This is the "basic light", which has a pair of connected red/green lights
class LightState:
    def __init__(self):
        super()
        # period and start determines how lights change
<<<<<<< HEAD
        self.period = 1000000  # Typical red light duration
        self.half_period = 500000
        self.start = random.randint(0, 100)
    # gets the start time, checks if
    def is_red_at_time(self, time, d):
        start = self.start
        if (d & 1):
=======
        self.period = 120  # Typical red light duration
        self.half_period = 60
        self.start = random.randomint(0,100)

    def is_red_at_time(self, time, d):
        start = self.start
        if (d & 1) != 0: #d - direction so north/south or west/east
>>>>>>> origin/master
            start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
<<<<<<< HEAD
        if (d & 1):
            start += self.half_period

=======
        if (d & 1) != 0:
            start += self.half_period
>>>>>>> origin/master
        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start


<<<<<<< HEAD
=======
"""
Sonny's notes:
Changed it back to the original
"""
>>>>>>> origin/master
