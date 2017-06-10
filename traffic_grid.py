import json
import random
import copy
import numpy as np

# Terminalogy:
#   IID: Intersection ID, uniquely identify an intersection (if > 0)
#        or an external source
#   CID: Car ID, uniquely identify a car


#              |
#             (0)
#              |
#             ---
# ----(1) ---|   |----(3)----
#             ---
#              |
#             (2)
#              |

LIGHT_STATES = {
    '0S': "0|2_*",  # Green for 0-straight
    # '0L',  # Green for 0-left
    '1S': "1|3_*"
}


# Behavior names
DEFAULT_RIGHT = 1  # Means: Green: go, Red/Yellow: Stop and then yield_go(1)
DEFAULT = 2  # Green: go, Red/Yellow: Wait
# LIGHTED_LEFT = 3  # Green: go, Red/Yellow: Wait
# (Note lighted left is same as default)
YIELD_LEFT = 4  # Green: yield_go(2), Red/Yellow: Wait

# From#, To#, Probability to take, probablility to stop, time_to_travers,
# behavior (based on green/red)
STANDARD_4WAY_YIELD = [
    [0, 1, 0.05, 0, 100, DEFAULT_RIGHT],
    [0, 2, 0.90, 0, 100, DEFAULT],
    [0, 3, 0.05, 0, 100, YIELD_LEFT],
    [1, 0, 0.05, 0, 100, YIELD_LEFT],
    [1, 3, 0.90, 0, 100, DEFAULT],
    [1, 2, 0.05, 0, 100, DEFAULT_RIGHT],
    [2, 1, 0.05, 0, 100, YIELD_LEFT],
    [2, 0, 0.90, 0, 100, DEFAULT],
    [2, 3, 0.05, 0, 100, DEFAULT_RIGHT],
    [3, 0, 0.05, 0, 100, DEFAULT_RIGHT],
    [3, 1, 0.90, 0, 100, DEFAULT],
    [3, 2, 0.05, 0, 100, YIELD_LEFT],
]

# Events
EV_CAR_STOPPED = 1

# Light states
LS_STOP = 1   # Red or yellow light
LS_GO = 2  # Green light with no cars
LS_DEQUEUE = 3   # Green with a queue, so everyone goes out a bit slower


# This is the "basic light", which has a pair of connected red/gree lights
class LightState:
    def __init__(self):
        super()
        self.cur_time = 0
        self.cur_state = LS_GO
        # period and start determines how lights change
        self.period = 120  # Typical red light duration
        self.half_period = 60
        self.start = random.randint(0, 100)

    def is_red_at_time(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period
        return (time - start) % self.period < self.half_period

    def next_green(self, time, d):
        start = self.start
        if (d & 1) != 0:
            start += self.half_period

        nperiods = int((time - start) / self.period)
        return nperiods * self.period + self.half_period + start


class Intersection:
    def __init__(self, iid, grid, mesh=STANDARD_4WAY_YIELD):
        super()
        self.iid = iid
        self.grid = grid
        self.n_from = 4
        self.n_to = 4
        self.from_iids = [None] * self.n_from
        self.to_iids = [None] * self.n_to
        self.mesh = copy.deepcopy(mesh)
        self.light_state = None
        self.intersection_state = None
        self.outgoing_queue = [[]] * (self.n_from * self.n_to)  # include uturn
        self.light_state = LightState()

    def assign_from_iid(self, d, iid):
        self.from_iids[d] = iid

    def assign_to_iid(self, d, iid):
        self.to_iids[d] = iid

    # Ingest the car into the queue and will be spit out at schedule_traffic
    def incoming_traffic(self, from_iid, cars, valid_ts):
        for arrival, cid in cars:
            # First determin where this car will go:
            ran = random.random()
            ran_acc = 0
            for route in self.mesh:
                if self.from_iids[route[0]] != from_iid:
                    continue
                ran_acc += route[2]
                if ran < ran_acc:  # Taken
                    ran2 = random.random()
                    if ran2 < route[3]:  # Car got home
                        stop_time = arrival + round(route[4] * ran2 / route[3])
                        self.grid.add_event(EV_CAR_STOPPED, stop_time,
                                            (cid, self.iid, route[1]))
                    else:  # Car continues
                        item = [arrival, cid, route[0], route[1]]
                        qid = route[0] + route[1] * self.n_from
                        self.outgoing_queue[qid].append(item)

    def schedule_traffic(self):
        for qid in range(self.n_from * self.n_to):
            self.outgoing_queue[qid].sort()
            fi = qid % self.n_from
            ti = qid / self.n_from
            # Here we have a sorted queue of cars, just need to figure out the
            # lights to determine how much each has to wait

            self.grid.schedule_traffic(self.iid, self.to_iids[ti],
                                       self.outgoing_queue[qid])


class Inlet:
    def __init__(self, iid, to_iid, to_dir):
        self.iid = iid
        self.to_iid = to_iid
        self.to_dir = to_dir


class TrafficGrid:
    def __init__(self):
        super()
        random.seek(0)  # Deterministic random numbers
        self.events = []
        self.inlets = []
        self.outlets = []
        self.intersections = []
        self.last_valid_iid = 1

    def load(self, file):
        with open(file, 'r') as fp:
            data = json.load(fp)
            self.inlets = data['inlets']
            self.outlets = data['outlets']
            self.intersections = data['intersections']

    def save(self, file):
        with open(file, 'w') as fp:
            data = {
                'inlets': self.inlets,
                'outlets': self.outlets,
                'intersections': self.intersections
            }
            json.dump(data, fp)

    def schedule_traffic(self, from_iid, to_iid, queue):
        pass

    def generate_grid(self, m, n):
        # Allocate 1 - m*n for intersections
        # Allocate m*n +1 - m*n +2*m for top/bottom

        self.intersections = [None] * (m * n)
        for i in range(m + 2):
            for j in range(n + 2):
                iid = i + j * (m + 2)
                if i > 0 and i < m + 1 and j > 0 and j < n + 1:
                    io = Intersection(iid, self)
                    io.assign_from_iid(0, iid - (m + 2))
                    io.assign_from_iid(1, iid - 1)
                    io.assign_from_iid(2, iid + (m + 2))
                    io.assign_from_iid(3, iid + 1)
                    io.assign_from_iid(0, iid - (m + 2))
                    io.assign_from_iid(1, iid - 1)
                    io.assign_from_iid(2, iid + (m + 2))
                    io.assign_from_iid(3, iid + 1)
                else:
                    if (i == 0 or i == m + 1) and (j == 0 and j == n + 1):
                        continue  # Nothing at the corners
                    if i == 0:
                        to_iid = iid + 1
                        d = 1
                    elif i == m + 1:
                        to_iid = iid - 1
                        d = 3
                    elif j == 0:
                        to_iid = iid + m + 2
                        d = 0
                    else:
                        to_iid = iid - (m + 2)
                        d = 2
                    io = Inlet(iid, to_iid, d)
                    self.inlets.append(io)
                self.intersections[i + j * m] = io

    def add_event(self, ev_type, ts, payload):
        self.events.append([ev_type, ts, payload])
