import pygame
import random
from spritesheet import Spritesheet
from animation import Animation

class PolarBear(pygame.sprite.Sprite):
    def __init__(self, scale, x, y):
        super().__init__()

        self.scale = scale * 1.8
        self.facing_right = False
        self.STATE_FALLING = 0
        self.STATE_LANDING_WAIT = 1
        self.STATE_ROARING = 2
        self.STATE_FIGHTING = 3        
        self.current_state = self.STATE_FALLING
        self.state_timer = 0
        self.is_roaring = False 

        fall_sheet = Spritesheet("../Assets/Sheets/polarBear_fall_Sheet.png", self.scale)
        fall_frames = [(0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64), (192, 0, 64, 64)]
        self.anim_fall = Animation(fall_sheet, fall_frames, frame_duration=100)

        angry_sheet = Spritesheet("../Assets/Sheets/polarBear_angry_Sheet.png", self.scale)
        angry_frames = [(0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64)]
        self.anim_angry = Animation(angry_sheet, angry_frames, frame_duration=9999)

        base_sheet = Spritesheet("../Assets/Sheets/polarBear_base_Sheet.png", self.scale)
        self.anim_idle = Animation(base_sheet, [(0, 0, 64, 64)])

        self.current_animation = self.anim_fall
        self.image = self.current_animation.get_frame()
        self.rect = self.image.get_rect()
        self.x = x
        self.y = -1000 
        self.rect.topleft = (self.x, self.y)
        self.width = self.rect.width
        self.height = self.rect.height
        self.hitbox_rect = pygame.Rect(0, 0, self.width * 0.6, self.height * 0.8)
        self.max_health = 500
        self.health = self.max_health
        self.is_alive = True
        self.velocity_y = 0
        self.gravity = 0.5 * self.scale

    def update(self, dt, target_x, target_y, boundary_rect, all_enemies, projectiles=None):
        self.state_timer += dt

        if self.current_state == self.STATE_FALLING:
            self.current_animation = self.anim_fall
            self.velocity_y += self.gravity
            self.y += self.velocity_y

            target_floor = boundary_rect.centery - (self.height / 2)
            
            if self.y >= target_floor:
                self.y = target_floor
                self.velocity_y = 0
                self.current_state = self.STATE_LANDING_WAIT
                self.state_timer = 0
                self.anim_angry.index = 0
                self.current_animation = self.anim_angry

        elif self.current_state == self.STATE_LANDING_WAIT:
            self.current_animation = self.anim_angry
            self.anim_angry.index = 0
            
            if self.state_timer >= 5000:
                self.current_state = self.STATE_ROARING
                self.state_timer = 0
                self.is_roaring = True

        elif self.current_state == self.STATE_ROARING:
            self.current_animation = self.anim_angry
            self.anim_angry.index = 1
            
            if self.state_timer >= 1500:
                self.current_state = self.STATE_FIGHTING
                self.is_roaring = False
                self.anim_angry.index = 2
                
        elif self.current_state == self.STATE_FIGHTING:
            if self.state_timer < 1000:
                self.current_animation = self.anim_angry
                self.anim_angry.index = 2
            else:
                # placeholder
                self.current_animation = self.anim_idle

        self.current_animation.update(dt)
        self.image = self.current_animation.get_frame()

        if self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
        self.rect.topleft = (self.x, self.y)

        self.hitbox_rect.centerx = self.rect.centerx
        self.hitbox_rect.bottom = self.rect.bottom

    def take_damage(self, amount):
        if self.current_state == self.STATE_FALLING:
            return
        self.health -= amount
        if self.health <= 0:
            self.is_alive = False

    def draw(self, surface, debug_show_hitboxes=False):
        surface.blit(self.image, self.rect)
        if debug_show_hitboxes:
            pygame.draw.rect(surface, (255, 0, 0), self.hitbox_rect, 2)