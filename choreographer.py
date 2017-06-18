

class Car:
    def __init__(self, cid):
        self.id = cid


class Choreographer:
    def __init__(self):
        self.cars = {}

    def car_intersection_event(self, ts, cid, to_iid, d, state=0):
        if not cid in self.cars:
            self.cars[cid] = Car(cid)
        car = self.cars[cid]

    def car_dequeue_event(self, ts, cid, iid):
        pass