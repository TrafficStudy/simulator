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
QZONE_PER_CAR = 2.4
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

INTERSECTION_SPEED = 10 * 1609 / 3600  # 10m/h = 4.47 m/s


def DIR_POS(d, x, y):
    if d == 0:
        return (-x, y)
    if d == 1:
        return (y, x)
    if d == 2:
        return (x, -y)
    if d == 3:
        return (-y, -x)
    print("Bad dir: ", d)


# Returns 0 for left, 1 for straight, 2 for right
def SELECT_LANE(id, od):
    diff = (id + 4 - od) % 4
    if diff == 3:
        return 0
    if diff == 2:
        return 1
    if diff == 1:
        return 2
    return 2  # u-turn!
