import sys
import pygame
import time
import math
import random

#testing testing 123 testing
def gen_random_item():
    t0 = random.randint(1, 100)
    s0 = random.randint(1, 20) / 10
    s1 = random.randint(1, 20) / 10
    edge = 5.0 + random.randint(0, 10)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return [t0, s0, s1, edge, color]


def run_animation():
    pygame.init()
    disp = pygame.display.set_mode((500, 500), 0, 32)
    t0 = time.time()

    n_items = 4
    items = list(map(lambda x: gen_random_item(), range(n_items)))

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Draw the scene
        disp.fill((0,0,0))  # Fill black
        t = time.time() - t0
        for item in items:
            t0, s0, s1, edge, color = item
            x = (500 - edge) * (math.sin(s0 * (t + t0)) + 1) / 2
            y = (500 - edge) * (math.sin(s1 * (t + t0)) + 1) / 2
            pygame.draw.rect(disp, color, (x, y, edge, edge), 0)
            pygame.draw.rect(disp, (255,255,255), (x, y, edge, edge), 1)

        pygame.display.update()
        # time.sleep(0.2)  # don't be always busy


if __name__ == "__main__":
    run_animation()
