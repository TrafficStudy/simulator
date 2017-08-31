import random

EV_CAR_STOPPED = 1
EV_CAR_ENTER_INTERSECTION = 2
EV_LIGHT_CHANGE = 3
EV_DEQUEUE_GREEN = 4  # This is the slow de-queuing of a light just turned green

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
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, (fin_state, self.itn.iid))
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