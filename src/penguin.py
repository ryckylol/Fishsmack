import pygame
from spritesheet import Spritesheet
from animation import Animation

class Penguin:
    def __init__(self, scale):
        self.scale = scale
        self.movement_sheet = Spritesheet("../Assets/Sheets/penguin_walkCycle_Sheet.png", scale)
        movement_frame_data = [
            (0, 0, 64, 64),
            (64, 0, 64, 64),
        ]
        self.movement_animation = Animation(self.movement_sheet, movement_frame_data, frame_duration=150)

        self.swing_sheet = Spritesheet("../Assets/Sheets/penguin_swingL_Sheet.png", scale)
        swing_frame_data = [
            (0, 0, 64, 64),
            (64, 0, 64, 64),
        ]
        self.swing_animation = Animation(self.swing_sheet, swing_frame_data, frame_duration=100)

        self.current_animation = self.movement_animation
        
        self.x = 0
        self.y = 0
        self.width = 64 * scale
        self.height = 64 * scale
        self.speed = 300
        self.facing_right = True 

        self.is_attacking = False
        self.attack_damage = 15
        
        self.max_combo_hits = 3 
        self.combo_hit_count = 0 
        self.combo_reset_time = 600
        self.combo_reset_timer = 0
        self.full_recovery_delay = 300 
        self.recovery_timer = 0

        self.attack_duration = len(swing_frame_data) * 100 
        self.attack_active_timer = 0

        self.hitbox_size = (int(50 * scale), int(40 * scale)) 
        
        self.attack_hitbox_rect = pygame.Rect(0, 0, *self.hitbox_size)
        self.attack_hitbox_rect.topleft = (-1000, -1000)

    def start_attack(self):
        """Initiates the light attack (swingL)."""
        if self.is_attacking or self.recovery_timer > 0:
            return

        if self.combo_reset_timer <= 0:
            self.combo_hit_count = 0

        if self.combo_hit_count >= self.max_combo_hits:
            return

        self.combo_hit_count += 1
        
        self.is_attacking = True
        self.attack_active_timer = 0
        self.swing_animation.reset() 
        self.current_animation = self.swing_animation

        self.combo_reset_timer = 0

    def update(self, dt, boundary_rect):
        keys = pygame.key.get_pressed()
        
        if self.recovery_timer > 0:
            self.recovery_timer -= dt
            if self.recovery_timer < 0:
                self.recovery_timer = 0

        if self.combo_reset_timer > 0:
            self.combo_reset_timer -= dt
            if self.combo_reset_timer <= 0:
                self.combo_hit_count = 0

        if self.is_attacking:
            self.attack_active_timer += dt
            self.current_animation.update(dt) 

            if self.attack_active_timer >= self.attack_duration:
                
                self.is_attacking = False
                self.attack_active_timer = 0
                self.current_animation = self.movement_animation

                if self.combo_hit_count == self.max_combo_hits:
                    self.recovery_timer = self.full_recovery_delay
                    self.combo_reset_timer = self.full_recovery_delay 
                    self.combo_hit_count = 0 
                else:
                    self.combo_reset_timer = self.combo_reset_time

        is_moving = False
        if not self.is_attacking:
            move_amount = self.speed * (dt / 1000)

            if keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]:
                is_moving = True

            if keys[pygame.K_w]:
                self.y -= move_amount
            if keys[pygame.K_s]:
                self.y += move_amount
            if keys[pygame.K_a]:
                self.x -= move_amount
                self.facing_right = False
            if keys[pygame.K_d]:
                self.x += move_amount
                self.facing_right = True

            if is_moving:
                self.current_animation.update(dt) 
            else:
                if self.current_animation == self.movement_animation:
                    self.movement_animation.index = 0
                    self.movement_animation.timer = 0
                    
        self.x = max(boundary_rect.left, min(self.x, boundary_rect.right - self.width))
        self.y = max(boundary_rect.top, min(self.y, boundary_rect.bottom - self.height))

        if self.is_attacking:
            hitbox_y = self.y + (self.height / 2) - (self.hitbox_size[1] / 2) 

            if self.facing_right:
                hitbox_x = self.x + self.width - (5 * self.scale) 
            else:
                hitbox_x = self.x - self.hitbox_size[0] + (5 * self.scale)

            self.attack_hitbox_rect.topleft = (hitbox_x, hitbox_y)
        else:
            self.attack_hitbox_rect.topleft = (-1000, -1000)


    def draw(self, surface, debug_show_hitboxes=False):
        """Draws the penguin and the attack hitbox (if debugging and active)."""
        image = self.current_animation.get_frame()
        
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
            
        surface.blit(image, (self.x, self.y))
        
        if debug_show_hitboxes and self.is_attacking:
            pygame.draw.rect(surface, (0, 255, 255), self.attack_hitbox_rect, 2)