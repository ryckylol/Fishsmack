import pygame
from spritesheet import Spritesheet
from animation import Animation
import math
import random
import os

class Seal(pygame.sprite.Sprite):
    def __init__(self, scale, x=0, y=0, base_speed=250):
        super().__init__()
        
        self.scale = scale
        self.x = x
        self.y = y
        self.base_speed = base_speed
        self.speed = base_speed * random.uniform(0.9, 1.1)
        self.facing_right = False 
        self.health = 50 
        self.max_health = 50
        self.total_attack_damage = 25
        self.damage_per_hit = self.total_attack_damage
        self.attack_range = 70 * scale
        self.slide_range = 500 * scale
        self.attack_cooldown = 4000
        self.cooldown_timer = 2000 + random.randint(0, 1000)
        self.has_entered_boundary = False
        self.is_alive = True
        self.is_staggered = False
        self.stagger_timer = 0
        self.stagger_duration = 300 
        self.is_sliding = False
        self.has_slid = False
        self.is_jumping_to_align = False
        self.is_attacking = False
        self.hits_landed = 0
        self.hit_frames = {2}
        self.current_damage = 0
        self.target_y_alignment = 0
        self.base_sheet = Spritesheet("../Assets/Sheets/seal_base_Sheet.png", scale) 
        self.slide_sheet = Spritesheet("../Assets/Sheets/seal_slide_Sheet.png", scale) 
        self.jump_sheet = Spritesheet("../Assets/Sheets/seal_jump_Sheet.png", scale)
        self.slap_sheet = Spritesheet("../Assets/Sheets/seal_slap_Sheet.png", scale)
        self.idle_animation = Animation(self.base_sheet, [(0, 0, 64, 64)], frame_duration=300)
        self.slide_animation = Animation(self.slide_sheet, [(0, 0, 64, 64)], frame_duration=100)

        jump_frame_data = [(0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64)]
        self.jump_animation = Animation(self.jump_sheet, jump_frame_data, frame_duration=100)
        self.jump_duration = len(jump_frame_data) * 100
        
        slap_frame_data = [(0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64), (192, 0, 64, 64)]
        self.slap_animation = Animation(self.slap_sheet, slap_frame_data, frame_duration=100)
        self.slap_duration = len(slap_frame_data) * 100 
        self.current_animation = self.idle_animation 
        self.width = 64 * scale
        self.height = 64 * scale 
        
        self.hitbox_rect = pygame.Rect(0, 0, int(50 * scale), int(40 * scale)) 
        self.slide_attack_size = (int(50 * scale), int(30 * scale))
        self.slide_attack_rect = pygame.Rect(0, 0, *self.slide_attack_size)
        
        self.slap_attack_size = (int(50 * scale), int(45 * scale))
        self.slap_attack_rect = pygame.Rect(0, 0, *self.slap_attack_size)
        self.attack_rect = self.slide_attack_rect
        self.slide_buildup_duration = 300
        self.slide_timer = 0
        self.slide_max_speed_multiplier = 3.0 
        self.jump_velocity = -400 * self.scale
        self.initial_y = 0
        self.jump_timer = 0 
        self.hop_start_x = 0
        self.hop_start_y = 0
        self.hop_end_x = 0
        self.hop_end_y = 0
        self.hop_distance_factor = 0.25 

    def start_slide(self, target_is_right_of_seal):
        if self.is_sliding or self.cooldown_timer > 0 or self.is_staggered or self.has_slid:
            return False

        self.facing_right = target_is_right_of_seal
        self.is_sliding = True
        self.current_animation = self.slide_animation
        self.slide_animation.reset()
        
        self.attack_rect = self.slide_attack_rect
        self.current_damage = self.total_attack_damage * 0.5
        self.slide_speed = self.base_speed * self.slide_max_speed_multiplier
        self.hits_landed = 0
        self.slide_timer = 0
        self.slide_attack_rect.topleft = (-1000, -1000)
        return True

    def start_jump_to_align(self, target_x, target_y):
        if self.is_attacking or self.is_sliding or self.is_jumping_to_align or self.is_staggered:
            return False
            
        self.is_jumping_to_align = True
        
        seal_center_x = self.x + self.width / 2
        seal_center_y = self.y + self.height / 2

        self.facing_right = (target_x > seal_center_x)

        dx_remaining = target_x - seal_center_x
        dy_remaining = target_y - seal_center_y
        
        self.hop_start_x = self.x
        self.hop_start_y = self.y
        self.hop_end_x = self.x + (dx_remaining * self.hop_distance_factor)
        self.hop_end_y = self.y + (dy_remaining * self.hop_distance_factor)

        self.current_animation = self.jump_animation
        self.jump_animation.reset()
        self.jump_timer = 0
        return True

    def start_slap(self, target_is_right_of_seal):
        if self.is_attacking or self.cooldown_timer > 0 or self.is_staggered:
            return False
            
        self.facing_right = target_is_right_of_seal 
        self.is_attacking = True
        self.hits_landed = 0
        self.cooldown_timer = self.attack_cooldown
        self.current_animation = self.slap_animation
        self.slap_animation.reset()
        self.attack_rect = self.slap_attack_rect
        self.current_damage = self.total_attack_damage * 0.1
        return True

    def take_damage(self, damage_amount, stagger_duration=300):
        if not self.is_alive:
            return

        self.health -= damage_amount
        
        if self.health > 0:
            self.is_staggered = True
            self.stagger_timer = stagger_duration
            self.is_attacking = False 
            self.is_sliding = False
            self.is_jumping_to_align = False
            self.current_animation = self.idle_animation
            self.attack_rect.topleft = (-1000, -1000)
            self.hits_landed = 0
            
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            
    def separate(self, all_enemies, dt):
        separation_strength = 2.0
        push_vector_x = 0
        push_vector_y = 0
        
        for other_enemy in all_enemies:
            if other_enemy != self and other_enemy.is_alive:
                self_center_x = self.x + self.width / 2
                self_center_y = self.y + self.height / 2
                other_center_x = other_enemy.x + other_enemy.width / 2
                other_center_y = other_enemy.y + other_enemy.height / 2
                
                dx = self_center_x - other_center_x
                dy = self_center_y - other_center_y
                distance = math.sqrt(dx**2 + dy**2)
                
                min_separation = (self.hitbox_rect.width + other_enemy.hitbox_rect.width) / 2
                
                if distance < min_separation * 1.5 and distance > 0:
                    dx_norm = dx / distance
                    dy_norm = dy / distance
                    
                    push_magnitude = (min_separation * 1.5 - distance) / (min_separation * 1.5)
                    
                    push_vector_x += dx_norm * push_magnitude * separation_strength
                    push_vector_y += dy_norm * push_magnitude * separation_strength

        self.x += push_vector_x * (self.speed * (dt / 1000))
        self.y += push_vector_y * (self.speed * (dt / 1000))
            
    def update(self, dt, target_x, target_y, boundary_rect, all_enemies):
        if not self.is_alive:
            self.attack_rect.topleft = (-1000, -1000)
            return

        if self.is_staggered:
            self.stagger_timer -= dt
            if self.stagger_timer <= 0:
                self.is_staggered = False
            self.current_animation = self.idle_animation
            return 

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0

        self.attack_rect.topleft = (-1000, -1000)
        
        seal_center_x = self.x + self.width / 2
        seal_center_y = self.y + self.height / 2
        
        dx = target_x - seal_center_x
        dy = target_y - seal_center_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if self.is_sliding:
            self.slide_timer += dt
            
            self.current_animation.update(dt) 

            slide_velocity = 0
            if self.slide_timer >= self.slide_buildup_duration:
                slide_velocity = self.slide_speed * (dt / 1000)
            else:
                pass

            if self.facing_right:
                self.x += slide_velocity
            else:
                self.x -= slide_velocity

            self.hitbox_rect.center = (self.x + self.width / 2, self.y + self.height / 2)
            
            if self.facing_right:
                slide_x = self.hitbox_rect.right - int(10 * self.scale)
            else:
                slide_x = self.hitbox_rect.left - self.slide_attack_rect.width + int(10 * self.scale)

            self.slide_attack_rect.topleft = (slide_x, 0)
            self.slide_attack_rect.centery = self.hitbox_rect.centery
            
            self.attack_rect = pygame.Rect(self.slide_attack_rect.x, self.slide_attack_rect.y, self.slide_attack_rect.width, self.slide_attack_rect.height)

            if (self.facing_right and self.x > boundary_rect.right - self.width) or \
               (not self.facing_right and self.x < boundary_rect.left) or \
               (self.slide_timer >= self.slide_buildup_duration and distance < self.attack_range):
                self.is_sliding = False
                self.has_slid = True
                self.current_animation = self.idle_animation
                self.cooldown_timer = 500
                self.hits_landed = 0
                
        elif self.is_jumping_to_align:
            self.jump_timer += dt
            self.current_animation.update(dt)

            t = min(1.0, self.jump_timer / self.jump_duration)

            x_delta = self.hop_end_x - self.hop_start_x
            self.x = self.hop_start_x + x_delta * t
            
            y_delta = self.hop_end_y - self.hop_start_y
            self.y = self.hop_start_y + y_delta * t

            self.separate(all_enemies, dt)

            self.hitbox_rect.center = (self.x + self.width / 2, self.y + self.height / 2)

            if self.jump_timer >= self.jump_duration:
                self.is_jumping_to_align = False
                self.current_animation = self.idle_animation
                self.cooldown_timer = 200
                
        elif self.is_attacking:
            self.current_animation.update(dt)
            current_frame = self.current_animation.index

            self.hitbox_rect.center = (self.x + self.width / 2, self.y + self.height / 2)

            if current_frame in self.hit_frames:
                hitbox_y = self.y + (self.height / 2) - (self.slap_attack_size[1] / 2)
                
                if self.facing_right: 
                    hitbox_x = self.x + self.width - (10 * self.scale) 
                else:
                    hitbox_x = self.x - self.slap_attack_size[0] + (10 * self.scale) 
                
                self.slap_attack_rect.topleft = (hitbox_x, hitbox_y)
                
            else:
                self.slap_attack_rect.topleft = (-1000, -1000)
                
            self.attack_rect = self.slap_attack_rect

            if self.current_animation.index == len(self.slap_animation.frames) - 1 and self.current_animation.time_since_last_frame >= 0:
                self.is_attacking = False
                self.current_animation = self.idle_animation
                self.hits_landed = 0
                
        else:
            other_attacker_is_present = any(
                other_enemy is not self and other_enemy.is_alive and (
                    (hasattr(other_enemy, 'is_attacking') and other_enemy.is_attacking) or 
                    (hasattr(other_enemy, 'is_sliding') and hasattr(other_enemy, 'is_sliding') and other_enemy.is_sliding)
                ) for other_enemy in all_enemies
            )

            is_moving = False
            self.separate(all_enemies, dt)
            move_amount = self.speed * (dt / 1000)

            if not self.has_entered_boundary:
                if distance > 0:
                    self.x += (dx / distance) * move_amount
                    self.y += (dy / distance) * move_amount
                is_moving = True
                
            elif other_attacker_is_present:
                retreat_speed = self.speed * 0.5 
                
                if dx > 0:
                    self.x -= retreat_speed * (dt / 1000)
                    self.facing_right = False 
                else:
                    self.x += retreat_speed * (dt / 1000)
                    self.facing_right = True 
                    
                is_moving = True

            elif not self.has_slid and distance > self.slide_range and self.cooldown_timer <= 0:
                self.start_jump_to_align(target_x, target_y)

            elif not self.has_slid and distance <= self.slide_range and self.cooldown_timer <= 0:
                self.start_slide(target_is_right_of_seal=(dx > 0))

            elif self.has_slid and distance > self.attack_range and self.cooldown_timer <= 0:
                if abs(dy) > 10 * self.scale or distance > self.attack_range * 0.8:
                    self.start_jump_to_align(target_x, target_y)

            elif self.has_slid and distance <= self.attack_range and self.cooldown_timer <= 0:
                self.start_slap(target_is_right_of_seal=(dx > 0))

            if not self.is_attacking and not self.is_sliding and not self.is_jumping_to_align:
                self.current_animation = self.idle_animation
                self.current_animation.update(dt)
                self.hitbox_rect.center = (self.x + self.width / 2, self.y + self.height / 2)

        if self.has_entered_boundary:
            self.x = max(boundary_rect.left, min(self.x, boundary_rect.right - self.width))
            self.y = max(boundary_rect.top, min(self.y, boundary_rect.bottom - self.height))
        else:
            seal_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if boundary_rect.contains(seal_rect):
                self.has_entered_boundary = True

        self.hitbox_rect.center = (self.x + self.width / 2, self.y + self.height / 2)

    def draw(self, surface, debug_show_hitboxes=False):
        if not self.is_alive:
            return
            
        image = self.current_animation.get_frame()

        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)

        surface.blit(image, (self.x, self.y))
        
        if debug_show_hitboxes:
            pygame.draw.rect(surface, (255, 0, 255), self.hitbox_rect, 2)
            if self.is_sliding or self.is_attacking:
                pygame.draw.rect(surface, (255, 0, 0), self.attack_rect, 2)