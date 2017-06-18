import random, math, time, sys
import pygame
from traffic_grid import *

# Animator basics: (everything is in meters)
# lane width: 3.7  (us road lane width)
# car dimensions:
#     small: 1.7 x 4.4
#     medium 1.9 x 4.7
#     large: 2.4 x 8.4  (Large truck)


CAR_DIMENSIONS = [
    [0.5, (1.7, 4.4)],
    [0.4, (1.9, 4.7)],
    [0.1, (2.4, 8.4)]
]


def ROT90(l):
    return list(map(lambda xy : (-xy[1], xy[0]), l))


def MIRROR_Y(l):
    return list(map(lambda xy: (xy[0], -xy[1]), l))


def MIRROR_XY(l):
    return list(map(lambda xy: (-xy[0], -xy[1]), l))


def APPLY_4x(l):
    r9 = ROT90(l)
    r18 = ROT90(r9)
    r27 = ROT90(r18)
    return [l, r9, r18, r27]


def APPLY_8x(l):
    r9 = ROT90(l)
    mi = MIRROR_Y(l)
    r9m = ROT90(mi)
    mxy = MIRROR_XY(l)
    return [l, mi, r9, r9m, mxy, MIRROR_Y(mxy), MIRROR_XY(r9), MIRROR_XY(r9m)]

# This is from [-1, 1] on both dimensions
CAR_POLYLINES = [(-0.25, -1), (-1, 0), (-1, 1), (1, 1), (1, 0), (0.25, -1)]
LANE_WIDTH = 3.7
ZEBRA_WIDTH = 2.0
QZONE_LEN = 4 * 2.4
SZONE_LEN = 3 * 3.7
ISEC_SIZE = 3.5 * LANE_WIDTH
CS_W_SHAPE1 = [
    (-ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN - SZONE_LEN, -LANE_WIDTH * 1.5),
    (-ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN, -ISEC_SIZE),
    (-ISEC_SIZE - ZEBRA_WIDTH, -ISEC_SIZE),
    (-ISEC_SIZE - ZEBRA_WIDTH, ISEC_SIZE),
    (-ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN, ISEC_SIZE),
    (-ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN - SZONE_LEN, LANE_WIDTH * 1.5)
]
CS_WHITES = [
    [(-ISEC_SIZE, -ISEC_SIZE), (-ISEC_SIZE, ISEC_SIZE), (ISEC_SIZE, ISEC_SIZE),
     (ISEC_SIZE, -ISEC_SIZE), (-ISEC_SIZE, -ISEC_SIZE)]
] + APPLY_4x(CS_W_SHAPE1)

CS_YELLOW = APPLY_8x(
    [(-ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN - SZONE_LEN, LANE_WIDTH * 0.25),
     (-ISEC_SIZE - ZEBRA_WIDTH, LANE_WIDTH * 0.25)])

CS_DOTTED = APPLY_8x([(ISEC_SIZE + ZEBRA_WIDTH, LANE_WIDTH * 1.25),
                      (ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN, LANE_WIDTH * 1.25)]) + \
            APPLY_8x([(ISEC_SIZE + ZEBRA_WIDTH, LANE_WIDTH * 2.25),
                      (ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN, LANE_WIDTH * 2.25)])

COLOR_HALF_WHITE = (128,128,128)
COLOR_WHITE = (255,255,255)
COLOR_YELLOW = (255,255,0)

def transform(xy, tr):
    x0, y0 = xy
    xs, ys, xt, yt, theta = tr
    st = math.sin(theta * 3.1416 / 180)
    ct = math.cos(theta * 3.1416 / 180)
    # First scale
    x0 *= xs
    y0 *= ys
    # Then rotate
    x1 = x0 * ct - y0 * st
    y1 = x0 * st + y0 * ct
    # Then translate
    x = x1 + xt
    y = y1 + yt
    # TODO: All these should be in a single transformation matrix
    return (x, y)


class Car:
    def __init__(self):
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

    def draw(self, disp, t):
        tr = (self.width, self.length, 0, 0, 0)
        # First determine location and orientation
        points = map(lambda xy: transform(xy, tr), self.polylines)
        pygame.draw.lines(disp, self.color, True, points, 1)



class Animator:
    def __init__(self, traffic_grid):
        self.canvas_size = 1200.0  # In meter
        self.traffic_grid = traffic_grid
        self.cars = []
        self.intersections = []
        self.disp = None
        self.t0 = 0
        self.screen_size = (900, 900)
        self.screen_offset = (0, 0)
        self.screen_scale = self.screen_size[0] / self.canvas_size * 2  # Each pixel == ? meters

        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.disp = pygame.display.set_mode(self.screen_size, 0, 32)
        self.t0 = time.time()

    def draw_dx_line(self, x, y0, y1):
        ss = self.screen_scale
        lw = round(ss * 0.2)
        if lw < 1:
            lw = 1
        for s in [1, -1]:
            dx = (x + s * LANE_WIDTH * 0.25) * ss - self.screen_offset[0]
            dy0 = y0 * ss - self.screen_offset[1]
            dy1 = y1 * ss - self.screen_offset[1]
            pygame.draw.line(self.disp, COLOR_YELLOW, (dx, dy0), (dx, dy1), lw)
            dx = (x + s * LANE_WIDTH * 1.5) * ss - self.screen_offset[0]
            pygame.draw.line(self.disp, COLOR_WHITE, (dx, dy0), (dx, dy1), lw)

    def draw_dy_line(self, x0, x1, y):
        ss = self.screen_scale
        lw = round(ss * 0.2)
        if lw < 1:
            lw = 1
        for s in [1, -1]:
            dy = (y + s * LANE_WIDTH * 0.25) * ss - self.screen_offset[1]
            dx0 = x0 * ss - self.screen_offset[0]
            dx1 = x1 * ss - self.screen_offset[0]
            pygame.draw.line(self.disp, COLOR_YELLOW, (dx0, dy), (dx1, dy), lw)
            dy = (y + s * LANE_WIDTH * 1.5) * ss - self.screen_offset[1]
            pygame.draw.line(self.disp, COLOR_WHITE, (dx0, dy), (dx1, dy), lw)

    def draw_d_lines(self, a, b1, b2):
        self.draw_dx_line(a, b1, b2)
        self.draw_dy_line(b1, b2, a)

    def draw_grid(self):
        # TODO: This is hard coded for now, should be following intersections
        for i in [1, 2, 3]:
            md = 400 * i - 200
            bc = 0
            for j in [1, 2, 3]:
                bd = j * 400 - 200
                self.draw_d_lines(md, bc, bd - ISEC_SIZE - ZEBRA_WIDTH - QZONE_LEN - SZONE_LEN)
                bc = bd + ISEC_SIZE + ZEBRA_WIDTH + QZONE_LEN + SZONE_LEN
            self.draw_d_lines(md, bc, 1200)

    def draw_intersection(self, io, t):
        ss = self.screen_scale
        tr = [ss, ss, io.pos_x * ss - self.screen_offset[0], io.pos_y * ss - self.screen_offset[1], 0]
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
            car.draw(self.disp, t)

    def draw(self, t):
        self.draw_grid()
        self.draw_intersections(t)
        self.draw_cars(t)
        pass

    def event_loop(self):
        while True:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif evt.type == pygame.MOUSEMOTION and evt.buttons[0] != 0:
                    self.drag(evt.rel)
                    print("Scree offste", self.screen_offset)
                elif evt.type == pygame.MOUSEBUTTONDOWN:
                    if evt.button == 4:  # Scroll up
                        self.zoom_in()
                    elif evt.button == 5:  # scroll down
                        self.zoom_out()

            # Draw the scene
            self.disp.fill((0, 0, 0))
            t = time.time() - self.t0
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

    def zoom_in(self):
        # TODO: Math is not 100% correct
        scale_progression = 0.25
        x = self.screen_offset[0] + self.screen_size[0] / 2 * scale_progression
        y = self.screen_offset[1] + self.screen_size[1] / 2 * scale_progression
        self.screen_offset = (x, y)
        self.screen_scale = (1 + scale_progression) * self.screen_scale

    def zoom_out(self):
        # TODO: Check for scale and offset limits
        scale_degression = 0.2  # 1/1.25 = 0.8
        x = self.screen_offset[0] - self.screen_size[0] / 2 * scale_degression
        y = self.screen_offset[1] - self.screen_size[1] / 2 * scale_degression
        self.screen_offset = (x, y)
        self.screen_scale = (1 - scale_degression) * self.screen_scale


if __name__ == "__main__":
    tr = TrafficGrid()
    tr.generate_grid(3, 3)
    an = Animator(tr)
    an.event_loop()