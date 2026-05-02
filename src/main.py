#!/usr/bin/env python3
import os
import sys

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from dashboard import Dashboard


def main():
    demo = "--demo" in sys.argv

    if not demo:
        os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")

    pygame.init()

    if "--fullscreen" in sys.argv or not demo:
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME
        )
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    pygame.display.set_caption("OpenDash")

    if demo:
        from speeduino import DemoReader
        reader = DemoReader()
    else:
        from speeduino import SpeeduinoReader
        reader = SpeeduinoReader()

    reader.start()

    dash = Dashboard(screen)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    dash.next_page()
            else:
                dash.handle_event(event)

        data = reader.get_data()
        dash.render(data)
        pygame.display.flip()
        clock.tick(FPS)

    reader.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
