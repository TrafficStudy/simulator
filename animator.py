import random, math, time, sys
import pygame
import pygame.font
from traffic_grid import *
from constants import *

# Animator basics: (everything is in meters)
# lane width: 3.7  (us road lane width)
# car dimensions:
#     small: 1.7 x 4.4
#     medium 1.9 x 4.7
#     large: 2.4 x 8.4  (Large truck)



def transform(xy, tr):
    x0, y0 = xy
    xs, ys, xt, yt, theta = tr
    st = math.sin(theta * 3.1416 / 180)
    ct = math.cos(theta * 3.1416 / 180)
    # First scale
    x0 *= xs
    y0 *= ys
    # Then rotate
    x1 = x0 * ct + y0 * st
    y1 = x0 * st - y0 * ct
    # Then translate
    x = x1 + xt
    y = y1 + yt
    # TODO: All these should be in a single transformation matrix
    return (x, y)


def distance(x, y):
    return math.sqrt(x*x+y*y)


class Car:
    def __init__(self, cid):
        self.cid = cid
        # Figure out what type of cars we have here
        r = random.random()
        acc = 0
        for prob, data in CAR_DIMENSIONS:
            acc += prob
            if r >= acc:
                continue
            self.width, self.length = data
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.polylines = CAR_POLYLINES


class Animator:
    def __init__(self, traffic_grid):
        self.canvas_size = 1200.0  # In meters
        self.traffic_grid = traffic_grid
        self.cars = []
        self.disp = None
        self.font = None
        self.t0 = 0
        self.screen_size = (900, 900)
        self.screen_offset = (0, 0)
        self.screen_scale = self.screen_size[0] / self.canvas_size  # Each pixel == ? meters

        self.setup_cars()
        self.init_pygame()

    def setup_cars(self):
        for cid in self.traffic_grid.choreographer.cars.keys():
            self.cars.append(Car(cid))

    def init_pygame(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont('Comic Sans MS', 30)
        self.disp = pygame.display.set_mode(self.screen_size, 0, 32)
        self.t0 = time.time()

    def draw_dx_line(self, x, y0, y1):
        ss = self.screen_scale
        lw = round(ss * 0.2)
        if lw < 1:
            lw = 1
        for s in [1, -1]:
            dx = (x + s * LANE_WIDTH * 0.25) * ss - self.screen_offset[0] + self.screen_size[0] / 2
            dy0 = y0 * ss - self.screen_offset[1] + self.screen_size[1] / 2
            dy1 = y1 * ss - self.screen_offset[1] + self.screen_size[1] / 2
            pygame.draw.line(self.disp, COLOR_YELLOW, (dx, dy0), (dx, dy1), lw)
            dx = (x + s * LANE_WIDTH * 1.5) * ss - self.screen_offset[0] + self.screen_size[0] / 2
            pygame.draw.line(self.disp, COLOR_WHITE, (dx, dy0), (dx, dy1), lw)

    def draw_dy_line(self, x0, x1, y):
        ss = self.screen_scale
        lw = round(ss * 0.2)
        if lw < 1:
            lw = 1
        for s in [1, -1]:
            dy = (y + s * LANE_WIDTH * 0.25) * ss - self.screen_offset[1] + self.screen_size[1] / 2
            dx0 = x0 * ss - self.screen_offset[0] + self.screen_size[0] / 2
            dx1 = x1 * ss - self.screen_offset[0] + self.screen_size[0] / 2
            pygame.draw.line(self.disp, COLOR_YELLOW, (dx0, dy), (dx1, dy), lw)
            dy = (y + s * LANE_WIDTH * 1.5) * ss - self.screen_offset[1] + self.screen_size[1] / 2
            pygame.draw.line(self.disp, COLOR_WHITE, (dx0, dy), (dx1, dy), lw)

    def draw_d_lines(self, a, b1, b2):
        self.draw_dx_line(a, b1, b2)
        self.draw_dy_line(b1, b2, a)

    def draw_grid(self):
        # TODO: This is hard coded for now, should be following intersections
        for i in [-1, 0, 1]:
            md = 400 * i
            bc = -600
            for j in [-1, 0, 1]:
                bd = j * 400
                self.draw_d_lines(md, bc, bd - ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN - SZONE_LEN)
                bc = bd + ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN + SZONE_LEN
            self.draw_d_lines(md, bc, 600)

    def draw_intersection(self, io, t):
        ss = self.screen_scale
        tr = [ss, ss, io.pos_x * ss - self.screen_offset[0] + self.screen_size[0] / 2,
              io.pos_y * ss - self.screen_offset[1] + self.screen_size[1] / 2, 0]
        # Closed solid whites
        lw = round(ss * 0.2)
        if lw < 1:
            lw = 1
        for shp in CS_WHITES:
            td_shp = list(map(lambda xy: transform(xy, tr), shp))
            pygame.draw.lines(self.disp, COLOR_WHITE, False, td_shp, lw)
        for shp in CS_YELLOW:
            td_shp = list(map(lambda xy: transform(xy, tr), shp))
            pygame.draw.lines(self.disp, COLOR_YELLOW, False, td_shp, lw)
        for shp in CS_DOTTED:
            td_shp = list(map(lambda xy: transform(xy, tr), shp))
            pygame.draw.lines(self.disp, COLOR_HALF_WHITE, False, td_shp, lw)

    def draw_intersections(self, t):
        for isec in self.traffic_grid.intersections:
            if not isec or isec.is_inlet():
                continue
            self.draw_intersection(isec, t)

    def draw_cars(self, t):
        for car in self.cars:
            self.draw_car(t, car)

    def draw_car(self, t, car):
        info = self.traffic_grid.choreographer.car_info(car.cid, t)
        if info is None:
            return  # No more drawing
        ss = self.screen_scale
        tr = (car.width / 2 * ss, car.length / 2 * ss, info[0] * ss - self.screen_offset[0] + self.screen_size[0] / 2,
              info[1] * ss - self.screen_offset[1] + self.screen_size[1] / 2, info[2])
        # First determine location and orientation
        points = list(map(lambda xy: transform(xy, tr), car.polylines))
        pygame.draw.lines(self.disp, car.color, True, points, 1)

    def draw(self, t):
        self.draw_grid()
        self.draw_intersections(t)
        self.draw_cars(t)
        self.draw_texts()

    def draw_texts(self):
        pass
        # text = self.font.render("{}, {}".format(*self.screen_offset), False, (255,255,255))
        # self.disp.blit(text, (0, 0))

    def event_loop(self):
        while True:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif evt.type == pygame.MOUSEMOTION and evt.buttons[0] != 0:
                    self.drag(evt.rel)
                elif evt.type == pygame.MOUSEMOTION and evt.buttons[2] != 0:
                    self.zoom(evt.pos, evt.rel)
                    # print("Scree offste", self.screen_offset)
                elif evt.type == pygame.MOUSEBUTTONDOWN:
                    if evt.button == 4:  # Scroll up
                        self.zoom_in()
                    elif evt.button == 5:  # scroll down
                        self.zoom_out()

            # Draw the scene
            self.disp.fill((0, 0, 0))
            t = (time.time() - self.t0) * 3
            self.draw(t)

            pygame.display.update()
            # time.sleep(0.2)  # don't be always busy

    def drag(self, rel):
        x = self.screen_offset[0] - rel[0]
        y = self.screen_offset[1] - rel[1]
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        max_x = self.screen_scale * self.canvas_size - self.screen_size[0]
        max_y = self.screen_scale * self.canvas_size - self.screen_size[1]
        if max_x < 0:
            max_x = 0
        if max_y < 0:
            max_y = 0
        if x > max_x:
            x = max_x
        if y > max_y:
            y = max_y
        self.screen_offset = (x, y)

    def zoom(self, pos, rel):
        sx = self.screen_size[0] / 2 - pos[0]
        sy = self.screen_size[1] / 2 - pos[1]
        r0 = distance(sx, sy)
        if r0 == 0:
            return
        r1 = distance(sx + rel[0], sy + rel[0])
        self.screen_scale *= r0 / r1
        x = self.screen_offset[0] + round(pos[0] * (r0 / r1 - 1))
        y = self.screen_offset[1] + round(pos[1] * (r0 / r1 - 1))
        self.screen_offset = (x, y)

    def zoom_in(self):
        # TODO: Math is not 100% correct
        scale_progression = 0.25
        self.screen_scale = 1.25 * self.screen_scale
        x = self.screen_offset

    def zoom_out(self):
        # TODO: Check for scale and offset limits
        # 1/1.25 = 0.8
        self.screen_scale = 0.8 * self.screen_scale


if __name__ == "__main__":
    tr = TrafficGrid()
    tr.choreographer = Choreographer(tr)
    tr.generate_grid(3, 3)
    tr.add_event(EV_CAR_ENTER_INTERSECTION, 0, (1, 7, 0))
    tr.add_event(EV_CAR_ENTER_INTERSECTION, 1, (2, 11, 1))
    tr.add_event(EV_CAR_ENTER_INTERSECTION, 3, (3, 17, 2))
    tr.event_loop()

    an = Animator(tr)
    an.event_loop()
    print("All done")