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
        self.period = 100  # Typical red light duration
        self.half_period = 50
        self.start = random.randint(-100, 0)
        #false = red, true = green
        self.state = False
        self.itn = Intersection

    def is_red_at_time(self, time, d, qid):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        end_state = not ((time - start) % self.period < self.half_period)
        if end_state != self.state:
            self.state = end_state
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, (end_state, self.itn.iid))
        self.itn.grid.add_event(EV_LIGHT_CHANGE, self.next_green(time, d),
                                (end_state, self.itn.iid))
        return self.state

    def next_green(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period

        n_periods = int((time - start) / self.period)
        return n_periods * self.period + self.half_period + start

# Dumb light cycle that only changes to let queues pass
class LightState1(LightState):

    def is_red_at_time(self, time, d, qid):
        if len(self.itn.outgoing_queue[qid]) >= 10:
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, (qid % 2, self.itn.iid))
            self.state = qid % 2
        return self.state & d

# Smarter cycle light that resets the cycle whenever a queue reaches over x cars
class LightState2(LightState):

    def is_red_at_time(self, time, d, qid):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        end_state = not ((time - start) % self.period < self.half_period)
        if len(self.itn.outgoing_queue[qid]) >= 10:
            end_state = (qid + 1) % 2
            self.start = time
        if end_state != self.state:
            self.state = end_state
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, True, (end_state, self.itn.iid))
        self.itn.grid.add_event(EV_LIGHT_CHANGE, self.next_green(time, d), True,
                                (end_state, self.itn.iid))
        return self.state & d