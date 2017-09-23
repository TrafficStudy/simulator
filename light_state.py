import random

EV_ALL_STOP = -1
EV_CAR_STOPPED = 1
EV_CAR_ENTER_INTERSECTION = 2
EV_LIGHT_CHANGE = 3
EV_DEQUEUE_GREEN = 4  # This is the slow de-queuing of a light just turned green

# This is the "basic light", which has a pair of connected red/green lights
class LightState:

    def __init__(self, Intersection):
        super()
        # period and start determines how lights change
        self.phases = [
            # Assuming that any light configuration will be rotationally symmetrical,
            # Can be altered to be asymmetrical
            #
            [1, 1, 1, 1, 0, 0, 0, 0, 50],
            [1, 1, 1, 1, 1, 1, 1, 1, 4],
            [0, 0, 0, 0, 1, 1, 1, 1, 50]
        ]
        self.period = 100  # Typical red light duration
        self.half_period = 50
        self.start = 0
        # 0 = E-W, 1 = N-S
        self.state = 0
        self.itn = Intersection
        self.itn.grid.add_event(EV_LIGHT_CHANGE, self.start + self.phases[self.state][8],
                                True, (1, self.itn.iid))

    def is_red_at_time(self, time, d, qid):
        return self.phases[self.state][qid % 8]

class LightState1(LightState):

    def __init__(self, Intersection):
        super()
        # period and start determines how lights change
        self.phases = [
            # Assuming that any light configuration will be rotationally symmetrical,
            # Can be altered to be asymmetrical
            # 1 is red, 0 is green
            [1, 1, 1, 1, 0, 0, 0, 0, 50],
            [1, 1, 1, 1, 1, 1, 1, 1, 4],
            [0, 0, 0, 0, 1, 1, 1, 1, 50]
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
        return self.phases[self.state][qid % 8]

# Smarter cycle light that resets the cycle whenever a queue reaches over x cars
class LightState2(LightState1):

    def is_red_at_time(self, time, d, qid):
        # 8 is the number of routes not with rotate. symm. ones (n_from * n_to / 2)
        test = (self.itn.iid == 16)
        end_state = self.state
        # sum is the number of cars in that direction
        sum = 1
        s_block = (int)(qid/4)*4
        for i in range(s_block, s_block+4):
            sum += len(self.itn.outgoing_queue[i % 16])
        for i in range(s_block+8, s_block+12):
            sum += len(self.itn.outgoing_queue[i % 16])
        if sum >= 2:
            # self.itn.grid.add_event(EV_ALL_STOP, time, True, None)
            for i in range(len(self.phases)):
                if self.phases[i][qid % 8] == 0:
                    end_state = i
                    break
        if end_state != self.state:
            self.itn.grid.add_event(EV_LIGHT_CHANGE, time, True, (end_state, self.itn.iid))
        is_red = self.phases[end_state][qid % 8]
        return is_red

# Dumb light cycle that only changes to let queues pass
class LightStateDiag(LightState):

    def is_red_at_time(self, time, d, qid):
        return True

