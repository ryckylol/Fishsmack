import pygame
from penguin import Penguin
import os

pygame.init()

display_W, display_H = 1280, 720
window = pygame.display.set_mode((display_W, display_H))
canvas = pygame.Surface((display_W, display_H))
pygame.display.set_caption("Fishsmack")

FPS = 60
clock = pygame.time.Clock()

NATIVE_W, NATIVE_H = 480, 270
SCALE = display_W / NATIVE_W

floor_top = int(display_H * 0.30) 
floor_height = display_H - floor_top + 20 
side_padding = -10 

walkable_rect = pygame.Rect(
    side_padding,
    floor_top,
    display_W - (side_padding * 2),
    floor_height
)

script_dir = os.path.dirname(__file__)
background_filename = "../Assets/background.png"
background_full_path = os.path.abspath(os.path.join(script_dir, background_filename))

try:
    background = pygame.image.load(background_full_path).convert()
    background = pygame.transform.scale(background, (display_W, display_H))
except FileNotFoundError:
    print(f"ERROR: Could not load background image: {background_full_path}. Using solid color.")
    background = pygame.Surface((display_W, display_H))
    background.fill((50, 50, 50))

penguin = Penguin(scale=SCALE)
penguin.x = walkable_rect.centerx - (penguin.width / 2)
penguin.y = walkable_rect.bottom - penguin.height 


running = True
DEBUG_SHOW_BOUNDARIES = True
DEBUG_SHOW_HITBOXES = True

while running:
    dt = clock.tick(FPS) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_j:
                 penguin.start_attack()
            elif event.key == pygame.K_k:
                 penguin.start_heavy_attack()
            elif event.key == pygame.K_l:
                 penguin.start_special_attack()

    penguin.update(dt, walkable_rect)

    canvas.blit(background, (0, 0))
    
    penguin.draw(canvas, debug_show_hitboxes=DEBUG_SHOW_HITBOXES)

    if DEBUG_SHOW_BOUNDARIES:
        pygame.draw.rect(canvas, (255, 0, 0), walkable_rect, 2)
    window.blit(canvas, (0, 0))
    pygame.display.flip()

pygame.quit()