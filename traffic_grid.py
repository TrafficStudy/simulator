import json
import random
import copy
import heapq
import statistics
from choreographer import Choreographer
from light_state import LightState
# import numpy as np

# Terminology:
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

ptestdata = 0 #determines whether to show specific events in each sample run

counter = 0
list_number = 100  # will be used later at the end of the loop
# list_number is the number of times the program is going to run
total_wait_time = 0
wait_time_list = []

while counter < list_number:  # 2 -> program runs 2 consecutive times

    DIRECTION_NAMES = ['North', 'West', 'South', 'East']

    # Behavior names
    DEFAULT_RIGHT = 1  # Means: Green: go, Red/Yellow: Stop and then yield_go(1)
    DEFAULT = 2  # Green: go, Red/Yellow: Wait
    YIELD_LEFT = 4  # Green: yield_go(2), Red/Yellow: Wait

    # From#, To#, Probability to take, probablility to stop, time_to_travel,
    # behavior (based on green/red)
    STANDARD_4WAY_YIELD = [
        [0, 1, 0.15, 0, 100, DEFAULT_RIGHT],
        [0, 2, 0.70, 0, 100, DEFAULT],
        [0, 3, 0.15, 0, 100, YIELD_LEFT],
        [1, 0, 0.15, 0, 100, YIELD_LEFT],
        [1, 3, 0.70, 0, 100, DEFAULT],
        [1, 2, 0.15, 0, 100, DEFAULT_RIGHT],
        [2, 1, 0.15, 0, 100, YIELD_LEFT],
        [2, 0, 0.70, 0, 100, DEFAULT],
        [2, 3, 0.15, 0, 100, DEFAULT_RIGHT],
        [3, 0, 0.15, 0, 100, DEFAULT_RIGHT],
        [3, 1, 0.70, 0, 100, DEFAULT],
        [3, 2, 0.15, 0, 100, YIELD_LEFT],
    ]

    # Events
    EV_CAR_STOPPED = 1
    EV_CAR_ENTER_INTERSECTION = 2
    EV_LIGHT_CHANGE = 3
    EV_DEQUEUE_GREEN = 4  # This is the slow de-queuing of a light just turned green

    EVENT_FORMAT_STRINGS = [
        "",
        "Car {0} stopped after passing intersection #{1}",
        "Car {0} approaches intersection #{1} from direction{2}",
        "Light changes at intersection #{0}",
        "Car {0} leaves intersection #{1} slowly"
    ]

    # Some time constants (in seconds)
    TS_FIRST_DEQUEUE_DELAY = 2
    TS_NEXT_DEQUEUE_DELAY = 2


    class Intersection:
        def __init__(self, iid, grid, mesh=STANDARD_4WAY_YIELD):
            super()
            self.iid = iid
            self.grid = grid
            self.n_from = 4
            self.n_to = 4
            self.from_iids = [None] * self.n_from
            self.to_iids = [None] * self.n_to
            self.to_dir_lookup = [2, 3, 0, 1]  # Leaving 0, arriving 2 etc.
            self.mesh = copy.deepcopy(mesh)
            self.intersection_state = None
            self.outgoing_queue = [[] for i in range(self.n_from * self.n_to)]  # include uturn
            self.light_state = LightState()
            self.qid_to_route = self.build_qid_lookup()
            self.pos_x = 0
            self.pos_y = 0

        def set_position(self, x, y):
            self.pos_x = x
            self.pos_y = y

        def build_qid_lookup(self):
            h = {}
            for r in self.mesh:
                qid = r[0] + r[1] * self.n_from
                h[qid] = r

            return h

        def assign_from_iid(self, d, iid):
            self.from_iids[d] = iid

        def assign_to_iid(self, d, iid):
            self.to_iids[d] = iid

        def incoming_traffic(self, ts, d, cid):
            # First determine where this car will go:
            ran = random.random()
            ran_acc = 0
            found_route = None
            for route in self.mesh:
                if route[0] != d:
                    continue
                ran_acc += route[2]
                if ran >= ran_acc:  # Not taken
                    continue
                found_route = route
                break

            is_red = self.light_state.is_red_at_time(ts, d)
            state = 0  # pass
            if is_red:
                next_green = self.light_state.next_green(ts, d)
                self.grid.add_event(EV_LIGHT_CHANGE, next_green, (self.iid, (d & 1)))

            qid = found_route[0] + found_route[1] * self.n_from
            if is_red or self.outgoing_queue[qid]:
                if ptestdata: print("Car {} stops at {}".format(cid, ts))
                self.grid.car_last_stop[cid] = ts
                # Enter the queue and schedule a light_change event
                item = [ts, cid, found_route[0], found_route[1]]
                self.outgoing_queue[qid].append(item)  # Queue will take care of this care
                state = len(self.outgoing_queue[qid])
            else:
                self.grid.count_waited += 1
                # No queue, just go through full speed
                if ptestdata: print("Car {} passed intersection #{} fast, to {}".format(cid, self.iid,  DIRECTION_NAMES[found_route[1]]))
                self.go_to_next_intersection(ts, cid, found_route)
            return (found_route[1], state)

        def go_to_next_intersection(self, ts, cid, found_route):
            # Check if the car will "go home"
            ran2 = random.random()
            if ran2 < found_route[3]:  # Car got home
                stop_time = ts + round(found_route[4] * ran2 / found_route[3])
                self.grid.add_event(EV_CAR_STOPPED, stop_time,
                                    (cid, self.iid, found_route[1]))
                return

            # Car continues
            arrival = ts + found_route[4]
            to_d = self.to_dir_lookup[found_route[1]]
            to_iid = self.to_iids[found_route[1]]
            self.grid.add_event(EV_CAR_ENTER_INTERSECTION, arrival, (cid, to_iid, to_d))

        def light_change(self, ts, to_state):
            for route in self.mesh:
                if (route[0] & 1) != to_state:
                    continue  # Nothing to do with red ones

                qid = route[0] + route[1] * self.n_from
                if self.outgoing_queue[qid]:
                    cid = self.outgoing_queue[qid][0][1]  # Peek only
                    self.grid.add_event(EV_DEQUEUE_GREEN, ts + TS_FIRST_DEQUEUE_DELAY,
                                        (cid, self.iid, qid))

        def dequeue_green(self, ts, cid, qid):
            if len(self.outgoing_queue[qid]) == 0:
                return
            item = self.outgoing_queue[qid].pop(0)
            self.go_to_next_intersection(ts, cid, self.qid_to_route[qid])
            duration = ts - self.grid.car_last_stop[cid]
            self.grid.total_wait_time += duration
            self.grid.count_waited += 1
            if self.outgoing_queue[qid]:
                cid = self.outgoing_queue[qid][0][1]
                self.grid.add_event(EV_DEQUEUE_GREEN, ts + TS_NEXT_DEQUEUE_DELAY,
                                    (cid, self.iid, qid))
            return item

        def is_inlet(self):
            return False


    class Inlet:
        def __init__(self, iid, to_iid, to_dir):
            self.iid = iid
            self.to_iid = to_iid
            self.to_dir = to_dir
            self.pos_x = None
            self.pos_y = None

        def is_inlet(self):
            return True

        def set_position(self, x, y):
            self.pos_x = x
            self.pos_y = y


    class TrafficGrid:
        def __init__(self, choreographer=None):
            super()
            self.events = []
            self.inlets = []
            self.outlets = []
            self.intersections = []
            self.last_event_ts = 0
            self.event_handlers = {
                EV_CAR_STOPPED: None,
                EV_CAR_ENTER_INTERSECTION: self.efn_enter_intersection,
                EV_LIGHT_CHANGE: self.efn_light_change,
                EV_DEQUEUE_GREEN: self.efn_dequeue_green,
            }
            self.choreographer = choreographer
            self.car_last_stop = {}  # cid => ts of the last time car stops
            self.total_wait_time = 0
            self.count_waited = 0

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

        def generate_grid(self, m, n):
            self.intersections = [None] * ((m + 2) * (n + 2))
            for i in range(m + 2):
                for j in range(n + 2):
                    iid = i + j * (m + 2)
                    if 0 < i < m + 1 and 0 < j < n + 1:
                        io = Intersection(iid, self)
                        io.set_position(i * 400 - 800, j * 400 - 800)
                        io.assign_from_iid(0, iid - (m + 2))
                        io.assign_from_iid(1, iid - 1)
                        io.assign_from_iid(2, iid + (m + 2))
                        io.assign_from_iid(3, iid + 1)
                        io.assign_to_iid(0, iid - (m + 2))
                        io.assign_to_iid(1, iid - 1)
                        io.assign_to_iid(2, iid + (m + 2))
                        io.assign_to_iid(3, iid + 1)
                    else:
                        pos_x = (i - 2) * 400
                        pos_y = (j - 2) * 400
                        if (i == 0 or i == m + 1) and (j == 0 or j == n + 1):
                            continue  # Nothing at the corners
                        if i == 0:
                            pos_x = 0
                            to_iid = iid + 1
                            d = 1
                        elif i == m + 1:
                            pos_x = 1200
                            to_iid = iid - 1
                            d = 3
                        elif j == 0:
                            pos_y = 0
                            to_iid = iid + m + 2
                            d = 0
                        else:
                            pos_y = 1200
                            to_iid = iid - (m + 2)
                            d = 2
                        io = Inlet(iid, to_iid, d)
                        io.set_position(pos_x, pos_y)
                        self.inlets.append(io)
                    self.intersections[iid] = io

        def add_event(self, ev_type, ts, payload):
            heapq.heappush(self.events, [ts, ev_type, payload])

        def print_event(self, ev):
            fmt = EVENT_FORMAT_STRINGS[ev[1]]
            msg = "{:-3d}: ".format(ev[0]) + fmt.format(*ev[2])
            for d in range(4):
                msg = msg.replace('direction{}'.format(d), DIRECTION_NAMES[d])
            if ptestdata: print(msg)

        def event_loop(self):
            while len(self.events) > 0:
                ev = heapq.heappop(self.events)
                self.print_event(ev)
                self.last_event_ts = ev[0]
                fn = self.event_handlers[ev[1]]
                if fn:
                    fn(ev[0], ev[2])

        # Payload is [cid, toIID, direction]
        def efn_enter_intersection(self, ts, payload):
            cid = payload[0]
            to_iid = payload[1]
            d = payload[2]
            iso = self.intersections[to_iid]
            if type(iso) is Inlet:
                if self.choreographer:
                    self.choreographer.car_intersection_event(ts, cid, to_iid, d, -1)
                # Car exits from the grid
            else:
                od, state = iso.incoming_traffic(ts, d, cid)
                if self.choreographer:
                    self.choreographer.car_intersection_event(ts, cid, to_iid, d, od, state)

        # This event only for intersections with car waiting
        # Payload is [iid, to_light_state]
        def efn_light_change(self, ts, payload):
            iid = payload[0]
            state = payload[1]
            iso = self.intersections[iid]
            iso.light_change(ts, state)

        def efn_dequeue_green(self, ts, payload):
            cid = payload[0]
            iid = payload[1]
            qid = payload[2]
            iso = self.intersections[iid]
            iso.dequeue_green(ts, cid, qid)
            if self.choreographer:
                n_from = iso.n_from
                id = qid % n_from
                od = int(qid / n_from)  # od is out_going direction
                self.choreographer.car_dequeue_event(ts, cid, iid, id, od)
#cat

    if __name__ == "__main__":
        """the variable, __name__, is converted to the string "__main__" when the program
    is run in the original file - meaning it doens't get run when imported into a different file"""
        # random.seed(100)  # Deterministic random numbers
        tr = TrafficGrid()
        tr.choreographer = Choreographer(tr)
        tr.generate_grid(3, 3)
        # In this 3x3 grid example:
        #     1   2   3
        #     |   |   |
        #  5--6---7---8---9
        #     |   |   |
        # 10--11--12--13--14
        #     |   |   |
        # 15--16--17--18--19
        #     |   |   |
        #     21  22  23

        last_ts = 0
        inlet_array = [1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23]
        for i in range(100):
            last_ts += random.randint(0, 100)
            inlet = tr.intersections[random.choice(inlet_array)]
            tr.add_event(EV_CAR_ENTER_INTERSECTION, last_ts, (i, inlet.to_iid, inlet.to_dir))
        # tr.add_event(EV_CAR_ENTER_INTERSECTION, 0, (1, 7, 0))
        # tr.add_event(EV_CAR_ENTER_INTERSECTION, 1, (2, 11, 1))
        # tr.add_event(EV_CAR_ENTER_INTERSECTION, 3, (3, 17, 2))
        tr.event_loop()
        average_wait_time = tr.total_wait_time / tr.count_waited
        if ptestdata: print("All finished, average wait time per intersection = {}".format(average_wait_time))

    total_wait_time += average_wait_time
    wait_time_list.append(average_wait_time)
    counter += 1


class Statistics:
    print("Total wait time in %d runs:" % list_number, total_wait_time)
    if ptestdata: print(wait_time_list)

    wait_time_list.sort()

    print("The minimum is:", wait_time_list[0])
    print("The maximum is:", wait_time_list[list_number - 1])
    arithmetic_mean = total_wait_time / list_number
    print("The mean is:", arithmetic_mean)

    print("The median is:", statistics.median(wait_time_list))

    try:
        print("The standard deviation is:", statistics.stdev(wait_time_list, arithmetic_mean))
    except statistics.StatisticsError:
        print("The standard deviation is: N/A")