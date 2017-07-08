from heapq import *
from constants import *


class Car:
    def __init__(self, cid):
        self.id = cid
        self.time_line = []
        self.io = None

    def set_current_intersection(self, io):
        self.io = io

    def add_time_line_item(self, ts, xy, d):
        if xy is not None:
            x = xy[0] + self.io.pos_x
            y = xy[1] + self.io.pos_y
            xy = (x, y)
        heappush(self.time_line, [ts, xy, d])

    def add_tl_enter(self, ts, d):
        x0 = ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN + SZONE_LEN
        t0 = ts - x0 / INTERSECTION_SPEED
        self.add_time_line_item(t0, DIR_POS(d, 0.75 * LANE_WIDTH, -x0), d)

    def add_tl_shift_to_queue(self, ts, id, lane):
        x1 = ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN
        t1 = ts - x1 / INTERSECTION_SPEED
        # lane = SELECT_LANE(id, od)
        self.add_time_line_item(t1, DIR_POS(id, (0.75 + lane) * LANE_WIDTH, -x1), id)

    def add_tl_to_end_queue(self, ts, od, olane):  # olane is same as lane
        x1 = ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN
        t1 = ts + x1 / INTERSECTION_SPEED
        self.add_time_line_item(t1, DIR_POS(od ^ 2, (0.75 + olane) * LANE_WIDTH, -x1), od ^ 2)

    def add_tl_shift_back(self, ts, od):
        x0 = ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN + SZONE_LEN
        t0 = ts + x0 / INTERSECTION_SPEED
        self.add_time_line_item(t0, DIR_POS(od ^ 2, 0.75 * LANE_WIDTH, -x0), od ^ 2)

    def add_tl_to_turn(self, ts, d, lane):
        dt = LANE_WIDTH / 2 / INTERSECTION_SPEED
        t0 = ts - dt
        self.add_time_line_item(t0, DIR_POS(d, (0.75 + lane) * LANE_WIDTH, (lane - 3) * LANE_WIDTH), d)

    def add_tl_to_finish_turn(self, ts, od, lane):
        dt = LANE_WIDTH / 2 / INTERSECTION_SPEED
        t0 = ts + dt
        self.add_time_line_item(t0, DIR_POS(od ^ 2, (0.75 + lane) * LANE_WIDTH,
                                            (3 - lane) * LANE_WIDTH), od ^ 2)

    def add_tl_to_qpos(self, ts, id, lane, pos):
        x = ISEC_SIZE + ZEBRA_WIDTH + QZONE_PER_CAR * pos
        t0 = ts - x / INTERSECTION_SPEED
        self.add_time_line_item(t0, DIR_POS(id, (0.75 + lane) * LANE_WIDTH, -x), id)

    def add_tl_finished(self, ts, id):
        self.add_time_line_item(ts, DIR_POS(id, 0.75 * LANE_WIDTH, 0), id)
        self.add_time_line_item(ts + 0.1, None, -1)

    def info(self, ts):  # returns (xy, angle) at given ts
        ntl = len(self.time_line)
        if ts < self.time_line[0][0]:
            it = self.time_line[0]
            if it[1] is None:
                return None
            return (it[1][0], it[1][1], it[2])
        elif ts >= self.time_line[ntl-1][0]:
            it = self.time_line[ntl-1]
            if it[1] is None:
                return None
            return (it[1][0], it[1][1], it[2])

        i = 0
        while i < ntl -1 and ts > self.time_line[i+1][0]:
            i += 1

        if self.time_line[i][1] is None:
            return None

        x0, y0 = self.time_line[i][1]
        d0 = self.time_line[i][2] * 90

        if self.time_line[i+1][1] is None:
            it = self.time_line[i]
            return (it[1][0], it[1][1], it[2])

        x1, y1 = self.time_line[i+1][1]
        d1 = self.time_line[i+1][2] * 90

        if d0 - d1 > 180:
            d1 += 360
        elif d0 - d1 < -190:
            d0 += 360

        dt = self.time_line[i+1][0] - self.time_line[i][0]
        a1 = (ts - self.time_line[i][0]) / dt
        a0 = 1 - a1  # (self.time_line[i+1][0] - ts) / dt

        return (a0 * x0 + a1 * x1, a0 * y0 + a1 * y1, a0 * d0 + a1 * d1)

class Choreographer:
    def __init__(self, traffic_grid):
        self.traffic_grid = traffic_grid
        self.cars = {}

    def car_info(self, cid, ts):
        car = self.cars[cid]
        return car.info(ts)

    def car_intersection_event(self, ts, cid, iid, incoming_d, outgoing_d, state=0):
        if not cid in self.cars:
            self.cars[cid] = Car(cid)
        car = self.cars[cid]
        io = self.traffic_grid.intersections[iid]

        car.set_current_intersection(io)

        if outgoing_d == -1:
            car.add_tl_finished(ts + 10, incoming_d)
            return

        car.add_tl_enter(ts, incoming_d)
        lane = SELECT_LANE(incoming_d, outgoing_d)
        car.add_tl_shift_to_queue(ts, incoming_d, lane)

        if state == 0 and lane == 1:  # straight
            car.add_tl_to_end_queue(ts, outgoing_d, lane)
            car.add_tl_shift_back(ts, outgoing_d)
        elif state == 0:
            car.add_tl_to_turn(ts, incoming_d, lane)
            car.add_tl_to_finish_turn(ts, outgoing_d, lane)
            car.add_tl_to_end_queue(ts, outgoing_d, lane)
            car.add_tl_shift_back(ts, outgoing_d)
        else:
            car.add_tl_to_qpos(ts, incoming_d, lane, state)

    def car_dequeue_event(self, ts, cid, iid, incoming_d, outgoing_d):
        if not cid in self.cars:
            self.cars[cid] = Car(cid)
        car = self.cars[cid]
        lane = SELECT_LANE(incoming_d, outgoing_d)
        if lane == 1:  # straight
            car.add_tl_to_end_queue(ts, outgoing_d, lane)
            car.add_tl_shift_back(ts, outgoing_d)
        else:
            car.add_tl_to_turn(ts, incoming_d, lane)
            car.add_tl_to_finish_turn(ts, outgoing_d, lane)
            car.add_tl_to_end_queue(ts, outgoing_d, lane)
            car.add_tl_shift_back(ts, outgoing_d)
