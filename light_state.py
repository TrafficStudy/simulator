import random

EV_ALL_STOP = -1
EV_CAR_STOPPED = 1
EV_CAR_ENTER_INTERSECTION = 2
EV_LIGHT_CHANGE = 3
EV_DEQUEUE_GREEN = 4  # This is the slow de-queuing of a light just turned green

# This is the "basic light", which has a pair of connected red/green lights
# now outdated
class LightState:

    def __init__(self, Intersection):
        super()
        # period and start determines how lights change
        self.phases = [
            # Assuming that any light configuration will be rotationally symmetrical,
            # Can be altered to be asymmetrical
            #
            [1, 0, 1, 0, 1, 0, 1, 0, 50],
            [0, 1, 0, 1, 0, 1, 0, 1, 50]
        ]
        self.period = 100  # Typical red light duration
        self.half_period = 50
        self.start = random.randint(-100, 0)
        # 0 = E-W, 1 = N-S
        self.state = 0
        self.itn = Intersection
        self.itn.grid.add_event(EV_LIGHT_CHANGE, self.start + self.phases[self.state][8],
                                True, (1, self.itn.iid))

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

# Smarter cycle light that resets the cycle whenever a queue reaches over x cars
class LightState1(LightState):

    def is_red_at_time(self, time, d, qid):
        # 8 is the number of routes not with rotate. symm. ones (n_from * n_to / 2)
        end_state = self.state
        # sum = len(self.itn.outgoing_queue[qid])
        sum = 0
        s_block = (int)(qid/4)*4
        for i in range(s_block, (s_block+4)%16):
            sum += len(self.itn.outgoing_queue[i])
        for i in range((s_block+8)%16, ((s_block+12)%16)):
            sum += len(self.itn.outgoing_queue[i])
        if (sum) >= 2:
            self.itn.grid.add_event(EV_ALL_STOP, time, True, None)
            # to change: instead of setting the end_state directly,
            # iterate through the cycle until a satisfactory phase is found
            end_state = (qid + 1) % 2
        if end_state != self.state:
            self.state = end_state
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, True, (end_state, self.itn.iid))
        is_red = self.phases[self.state][qid % 8]
        # if self.itn.iid == 16: print(qid)
        return is_red

# Dumb light cycle that only changes to let queues pass
class LightStateDiag(LightState):

    def is_red_at_time(self, time, d, qid):
        return True

