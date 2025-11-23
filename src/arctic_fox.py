import pygame
from spritesheet import Spritesheet
from animation import Animation
import math
import os
import random

class ArcticFox(pygame.sprite.Sprite):
    def __init__(self, scale, x=0, y=0, base_speed=200):
        super().__init__()
        self.scale = scale
        self.x = x
        self.y = y
        self.base_speed = base_speed
        self.speed = base_speed * random.uniform(0.9, 1.1)
        self.facing_right = False
        self.health = 30
        self.max_health = 30
        self.total_attack_damage = 5
        self.damage_per_hit = self.total_attack_damage / 3.0
        self.attack_range = 70 * scale
        self.attack_cooldown = 3000
        self.cooldown_timer = 2000
        self.is_attacking = False
        self.attack_timer = 0
        self.hits_landed = 0
        self.hit_frames = {2, 3, 4}
        self.has_hit_player = False
        self.is_alive = True
        self.is_staggered = False
        self.stagger_timer = 0
        self.stagger_duration = 300
        self.target_offset_y = random.uniform(-10 * scale, 10 * scale)
        self.cooldown_timer += random.randint(0, 1000)
        self.has_entered_boundary = False
        self.walk_sheet = Spritesheet("../Assets/Sheets/arcticFox_walkCycle_Sheet.png", scale)
        self.swing_sheet = Spritesheet("../Assets/Sheets/arcticFox_swing_Sheet.png", scale)
        idle_frame_data = [(0, 0, 64, 64)]
        self.idle_animation = Animation(self.walk_sheet, idle_frame_data, frame_duration=300)
        movement_frame_data = [
            (0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64), (192, 0, 64, 64)
        ]
        self.movement_animation = Animation(self.walk_sheet, movement_frame_data, frame_duration=100)
        swing_frame_data = [
            (0, 0, 64, 64), (64, 0, 64, 64), (128, 0, 64, 64),
            (192, 0, 64, 64), (256, 0, 64, 64), (320, 0, 64, 64)
        ]
        self.attack_animation = Animation(self.swing_sheet, swing_frame_data, frame_duration=150)
        self.attack_duration = len(swing_frame_data) * 150
        self.current_animation = self.idle_animation
        self.width = 64 * scale
        self.height = 64 * scale
        self.separation_radius = max(self.width, self.height) * 0.5
        self.hitbox_rect = pygame.Rect(0, 0, int(50 * scale), int(40 * scale))
        self.attack_hitbox_size = (int(50 * scale), int(45 * scale))
        self.attack_rect = pygame.Rect(0, 0, *self.attack_hitbox_size)
        self.attack_rect.topleft = (-1000, -1000)

    def start_attack(self, target_is_right_of_fox):
        if self.is_attacking or self.cooldown_timer > 0 or self.is_staggered:
            return False
        self.facing_right = not target_is_right_of_fox
        self.is_attacking = True
        self.hits_landed = 0
        self.has_hit_player = False
        self.attack_timer = 0
        self.cooldown_timer = self.attack_cooldown
        self.current_animation = self.attack_animation
        self.attack_animation.reset()
        return True

    def take_damage(self, damage_amount, stagger_duration=300):
        if not self.is_alive:
            return
        self.health -= damage_amount
        if self.health > 0:
            self.is_staggered = True
            self.stagger_timer = stagger_duration
            self.is_attacking = False
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
                check_radius = self.separation_radius * 1.5
                self_center_x = self.x + self.width / 2
                self_center_y = self.y + self.height / 2
                other_center_x = other_enemy.x + other_enemy.width / 2
                other_center_y = other_enemy.y + other_enemy.height / 2
                dx = self_center_x - other_center_x
                dy = self_center_y - other_center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < check_radius and distance > 0:
                    dx_norm = dx / distance
                    dy_norm = dy / distance
                    push_magnitude = (check_radius - distance) / check_radius
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
        fox_center_x = self.x + self.width / 2
        fox_center_y = self.y + self.height / 2
        target_y_offset = target_y + self.target_offset_y
        dx = target_x - fox_center_x
        dy = target_y_offset - fox_center_y
        distance = math.sqrt(dx*dx + dy*dy)
        self.attack_rect.topleft = (-1000, -1000)

        if (not self.is_attacking and not self.is_staggered and self.cooldown_timer == 0 and distance <= self.attack_range):
            target_is_right_of_fox = target_x > fox_center_x
            self.start_attack(target_is_right_of_fox)

        if self.is_attacking:
            self.attack_timer += dt
            self.current_animation.update(dt)
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.current_animation = self.idle_animation
                self.attack_timer = 0
                self.has_hit_player = False
            else:
                current_frame = self.current_animation.index
                if current_frame in self.hit_frames:
                    hit_number = list(self.hit_frames).index(current_frame) + 1
                    if hit_number > self.hits_landed:
                        hitbox_y = self.y + (self.height / 2) - (self.attack_hitbox_size[1] / 2)
                        if self.facing_right:
                            hitbox_x = self.x - self.attack_hitbox_size[0] + (10 * self.scale)
                        else:
                            hitbox_x = self.x + self.width - (10 * self.scale)
                        self.attack_rect.topleft = (hitbox_x, hitbox_y)
        else:
            other_attacker_is_present = any(
                other_enemy is not self and other_enemy.is_alive and hasattr(other_enemy, "is_attacking") and other_enemy.is_attacking and abs(other_enemy.x - self.x) < 120 * self.scale and abs(other_enemy.y - self.y) < 120 * self.scale
                for other_enemy in all_enemies
            )
            move_amount = self.speed * (dt / 1000)
            is_moving = False
            self.separate(all_enemies, dt)
            if other_attacker_is_present:
                retreat_speed = self.speed * 0.5
                if dx > 0:
                    self.x -= retreat_speed * (dt / 1000)
                    self.facing_right = False
                else:
                    self.x += retreat_speed * (dt / 1000)
                    self.facing_right = True
                is_moving = True
            elif distance > self.attack_range:
                is_moving = True
                if distance > 0:
                    dx_norm = dx / distance
                    dy_norm = dy / distance
                    self.x += dx_norm * move_amount
                    self.y += dy_norm * move_amount
                if dx > 0:
                    self.facing_right = True
                elif dx < 0:
                    self.facing_right = False
            if is_moving:
                if self.current_animation != self.movement_animation:
                    self.current_animation = self.movement_animation
                    self.movement_animation.reset()
            else:
                if self.current_animation != self.idle_animation:
                    self.current_animation = self.idle_animation
                    self.idle_animation.reset()
            self.current_animation.update(dt)

        fox_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not self.has_entered_boundary and boundary_rect.contains(fox_rect):
            self.has_entered_boundary = True
        if self.has_entered_boundary:
            self.x = max(boundary_rect.left, min(self.x, boundary_rect.right - self.width))
            self.y = max(boundary_rect.top, min(self.y, boundary_rect.bottom - self.height))
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
            if self.is_attacking:
                pygame.draw.rect(surface, (255, 0, 0), self.attack_rect, 2)
