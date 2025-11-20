import os
import pygame
from spritesheet import Spritesheet

pygame.init()

display_W, display_H = 1280, 720
canvas = pygame.Surface((display_W, display_H))
window = pygame.display.set_mode((display_W, display_H))
FPS = 60

pygame.display.set_caption("Fishsmack")

# main loop
clock = pygame.time.Clock()
running = True

my_spritesheet = Spritesheet("../Assets/Sheets/penguin_baseSheet.png")
penguin = my_spritesheet.get_sprite(0, 0, 64, 64)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pass

    pygame.display.flip()
    clock.tick(FPS)

    canvas.fill((255, 255, 255))
    canvas.blit(penguin, (0, display_H - 128))
    window.blit(canvas, (0,0))
    pygame.display.update()
    
pygame.quit()