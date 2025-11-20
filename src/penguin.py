import pygame
from spritesheet import Spritesheet
from animation import Animation

class Penguin:
    def __init__(self, scale):
        self.sheet = Spritesheet("../Assets/Sheets/penguin_walkCycle_Sheet.png", scale)
        
        walk_frame_data = [
            (0, 0, 64, 64),
            (64, 0, 64, 64),
        ]

        self.walk_animation = Animation(self.sheet, walk_frame_data, frame_duration=150)

        self.x = 0
        self.y = 0
        
        self.width = 64 * scale
        self.height = 64 * scale
        
        self.speed = 300 
        self.facing_right = True 

    def update(self, dt, boundary_rect):
        keys = pygame.key.get_pressed()
        
        move_amount = self.speed * (dt / 1000)
        is_moving = False

        if keys[pygame.K_w]:
            self.y -= move_amount
            is_moving = True
        if keys[pygame.K_s]:
            self.y += move_amount
            is_moving = True
        if keys[pygame.K_a]:
            self.x -= move_amount
            self.facing_right = False
            is_moving = True
        if keys[pygame.K_d]:
            self.x += move_amount
            self.facing_right = True
            is_moving = True

        if self.x < boundary_rect.left:
            self.x = boundary_rect.left
            
        if self.x > boundary_rect.right - self.width:
            self.x = boundary_rect.right - self.width
            
        if self.y < boundary_rect.top:
            self.y = boundary_rect.top
            
        if self.y > boundary_rect.bottom - self.height:
            self.y = boundary_rect.bottom - self.height

        if is_moving:
            self.walk_animation.update(dt)

    def draw(self, surface):
        image = self.walk_animation.get_frame()
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        surface.blit(image, (self.x, self.y))