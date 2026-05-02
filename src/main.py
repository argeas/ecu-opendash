#!/usr/bin/env python3
import os
import sys

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from dashboard import Dashboard


def main():
    demo = "--demo" in sys.argv
    use_fbdev = "--fbdev" in sys.argv

    fb_out = None

    if use_fbdev:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        try:
            from fbdev import FramebufferOutput
            fb_out = FramebufferOutput("/dev/fb0")
            print(f"Using direct framebuffer output: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        except Exception as e:
            print(f"Framebuffer failed: {e}, falling back to SDL")
            fb_out = None
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        pygame.init()
        if "--fullscreen" in sys.argv:
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
        from speeduino import AutoReader
        reader = AutoReader()

    reader.start()

    dash = Dashboard(screen)

    from datalog import DataLogger
    logger = DataLogger()
    logger.start(reader)

    from tuning import ECUTuner
    tuner = ECUTuner(reader)

    from webui import WebUI
    webui = WebUI(dash, reader, logger=logger, tuner=tuner)
    webui.start()
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
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                dash.next_page()

        data = reader.get_data()
        dash.render(data)

        if fb_out:
            fb_out.write_surface(screen)
        else:
            pygame.display.flip()

        clock.tick(FPS)

    reader.stop()
    logger.stop()
    webui.stop()
    if fb_out:
        fb_out.close()
    pygame.quit()


if __name__ == "__main__":
    main()
