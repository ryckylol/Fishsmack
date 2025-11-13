import os
import pygame
import pygame_aseprite_animation

pygame.init()

WINDOW_SIZE = (800, 600)
FPS = 60

screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
pygame.display.set_caption("Fishsmack")

# loads static background image
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
background_ase = os.path.join(base_dir, "asepriteFiles", "background.aseprite")

background = pygame_aseprite_animation.Animation(background_ase)
background_surface = background.animation_frames[0]

# main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    scaled_bg = pygame.transform.smoothscale(background_surface, screen.get_size())
    screen.blit(scaled_bg, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()