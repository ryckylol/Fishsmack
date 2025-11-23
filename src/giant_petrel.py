import pygame
from spritesheet import Spritesheet
from animation import Animation
import math
import random

class WindGust(pygame.sprite.Sprite):
    def __init__(self, x, y, facing_right, scale):
        super().__init__()
        self.scale = scale
        self.facing_right = facing_right
        self.speed = 150 * scale
        self.damage = 20
        self.max_life = 2500
        self.timer = 0
        self.width = int(60 * scale)
        self.height = int(50 * scale)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox_rect = pygame.Rect(0, 0, int(30 * scale), int(30 * scale))
        self.hitbox_rect.center = self.rect.center
        self.wind_color = (173, 216, 230)

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.max_life:
            self.kill()
            GiantPetrel.decrement_wind_counter()
            return
        move_amount = self.speed * (dt / 1000)
        if self.facing_right:
            self.rect.x += move_amount
        else:
            self.rect.x -= move_amount
        self.hitbox_rect.center = self.rect.center
        self.image.fill((0,0,0,0))
        fade_factor = max(0, 1 - (self.timer / self.max_life))
        num_streaks = 5
        for i in range(num_streaks):
            current_alpha = int(255 * fade_factor * (1.0 - i * 0.15))
            if current_alpha <= 0:
                continue
            color_with_alpha = self.wind_color + (current_alpha,)
            streak_w = int(self.width * (0.8 - i * 0.1))
            streak_h = int(5 * self.scale)
            y_offset = (i - num_streaks / 2) * (5 * self.scale)
            wobble = math.sin(self.timer * 0.01 + i) * (2 * self.scale)
            streak_surf = pygame.Surface((streak_w, streak_h), pygame.SRCALPHA)
            streak_surf.fill(color_with_alpha)
            angle = math.sin(self.timer * 0.005 + i) * 5
            if not self.facing_right:
                angle *= -1
            rotated_surf = pygame.transform.rotate(streak_surf, angle)
            rotated_rect = rotated_surf.get_rect(center=(self.width / 2, self.height / 2 + y_offset + wobble))
            self.image.blit(rotated_surf, rotated_rect.topleft)
        core_alpha = int(255 * fade_factor)
        core_color = (self.wind_color[0], self.wind_color[1], self.wind_color[2], core_alpha)
        pygame.draw.circle(self.image, core_color, (self.width // 2, self.height // 2), int(5 * self.scale * fade_factor))

class GiantPetrel(pygame.sprite.Sprite):
    active_wind_attacks = 0

    @classmethod
    def decrement_wind_counter(cls):
        cls.active_wind_attacks = max(0, cls.active_wind_attacks - 1)

    def __init__(self, scale, x=0, y=0):
        super().__init__()
        self.scale = scale
        self.x = x
        self.y = y
        self.is_blood = random.random() < 0.10
        self.speed = 180 * random.uniform(0.9, 1.1)
        self.health = 80 if not self.is_blood else 100
        self.max_health = self.health
        self.peck_damage = 10
        self.wind_damage = 20
        self.peck_range = 120 * scale
        self.wind_range = 400 * scale
        self.min_wind_range = 120 * scale
        self.initial_delay = 1500
        self.action_cooldown = self.initial_delay
        self.wind_cooldown = 10000
        self.wind_timer = 0
        self.facing_right = False
        self.is_attacking = False
        self.current_attack = None
        self.has_fired_projectile = False
        self.hits_landed = 0
        self.is_alive = True
        self.is_staggered = False
        self.stagger_timer = 0
        self.hit_frames_peck = {1}
        self.projectile_frame_wind = 2
        self.width = 64 * scale
        self.height = 64 * scale
        self.hitbox_rect = pygame.Rect(0, 0, int(50 * scale), int(50 * scale))
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.peck_hitbox_size = (int(40 * scale), int(40 * scale))
        self.attack_end_pending = False
        prefix = "giantPetrel_"
        if self.is_blood:
            base_name = f"{prefix}blood_base_Sheet.png"
            walk_name = f"{prefix}bloodWalkCycle_Sheet.png"
            peck_name = f"{prefix}bloodPeck_Sheet.png"
            wing_name = f"{prefix}bloodWingAttack_Sheet.png"
        else:
            base_name = f"{prefix}base_Sheet.png"
            walk_name = f"{prefix}walkCycle_Sheet.png"
            peck_name = f"{prefix}peck_Sheet.png"
            wing_name = f"{prefix}wingAttack_Sheet.png"
        self.base_sheet = Spritesheet(f"../Assets/Sheets/{base_name}", scale)
        self.walk_sheet = Spritesheet(f"../Assets/Sheets/{walk_name}", scale)
        self.peck_sheet = Spritesheet(f"../Assets/Sheets/{peck_name}", scale)
        self.wing_sheet = Spritesheet(f"../Assets/Sheets/{wing_name}", scale)
        self.idle_animation = Animation(self.base_sheet, [(0,0,64,64)], 300)
        walk_data = [(0,0,64,64), (64,0,64,64), (128,0,64,64)]
        self.walk_animation = Animation(self.walk_sheet, walk_data, 150)
        peck_data = [(0,0,64,64), (64,0,64,64)]
        self.peck_animation = Animation(self.peck_sheet, peck_data, 200)
        self.peck_animation.loop = False
        wing_data = [(0,0,64,64), (64,0,64,64), (128,0,64,64), (192,0,64,64)]
        self.wing_animation = Animation(self.wing_sheet, wing_data, 250)
        self.wing_animation.loop = False
        self.current_animation = self.idle_animation

    def take_damage(self, amount):
        if not self.is_alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
        else:
            self.is_staggered = True
            self.stagger_timer = 300
            self.is_attacking = False
            self.current_attack = None

    def start_peck(self, target_right):
        self.facing_right = target_right
        self.is_attacking = True
        self.current_attack = 'peck'
        self.current_animation = self.peck_animation
        self.peck_animation.reset()
        self.hits_landed = 0
        self.attack_end_pending = False

    def start_wind(self, target_right):
        if GiantPetrel.active_wind_attacks >= 2:
            return False
        GiantPetrel.active_wind_attacks += 1
        self.facing_right = target_right
        self.is_attacking = True
        self.current_attack = 'wind'
        self.current_animation = self.wing_animation
        self.wing_animation.reset()
        self.has_fired_projectile = False
        self.wind_timer = self.wind_cooldown
        self.attack_end_pending = False
        return True

    def update(self, dt, target_x, target_y, boundary_rect, all_enemies, projectiles_group=None):
        if not self.is_alive:
            self.attack_rect.topleft = (-1000, -1000)
            return
        if self.action_cooldown > 0:
            self.action_cooldown -= dt
        if self.wind_timer > 0:
            self.wind_timer -= dt
        if self.is_staggered:
            self.stagger_timer -= dt
            if self.stagger_timer <= 0:
                self.is_staggered = False
            return
        center_x = self.x + self.width/2
        center_y = self.y + self.height/2
        dx = target_x - center_x
        dy = target_y - center_y
        dist = math.sqrt(dx*dx + dy*dy)
        self.attack_rect.topleft = (-1000, -1000)
        move_x = 0
        move_y = 0
        move_amount = 0.0
        if self.is_attacking:
            self.current_animation.update(dt)
            if self.current_attack == 'peck':
                if self.current_animation.index in self.hit_frames_peck and self.hits_landed == 0:
                    offset_x = self.width - 10 if self.facing_right else -self.peck_hitbox_size[0] + 10
                    self.attack_rect = pygame.Rect(self.x + offset_x, self.y + 15, *self.peck_hitbox_size)
                    self.current_damage = self.peck_damage
                last_index = len(self.peck_animation.frames) - 1
                if self.current_animation.index >= last_index:
                    if self.attack_end_pending:
                        self.is_attacking = False
                        self.hits_landed = 0
                        self.action_cooldown = 500
                        self.attack_end_pending = False
                    else:
                        self.attack_end_pending = True
            elif self.current_attack == 'wind':
                if self.current_animation.index == self.projectile_frame_wind and not self.has_fired_projectile:
                    if projectiles_group is not None:
                        spawn_x = self.x + self.width if self.facing_right else self.x
                        spawn_y = self.y + self.height/2
                        wind = WindGust(spawn_x, spawn_y, self.facing_right, self.scale)
                        projectiles_group.add(wind)
                        self.has_fired_projectile = True
                last_index = len(self.wing_animation.frames) - 1
                if self.current_animation.index >= last_index:
                    if self.attack_end_pending:
                        self.is_attacking = False
                        self.action_cooldown = 2000
                        self.attack_end_pending = False
                    else:
                        self.attack_end_pending = True
        else:
            self.current_animation = self.idle_animation
            if dist < self.peck_range and self.action_cooldown <= 0:
                self.start_peck(dx > 0)
            elif dist < self.wind_range and dist > self.min_wind_range and self.wind_timer <= 0 and self.action_cooldown <= 0:
                success = self.start_wind(dx > 0)
                if not success:
                    move_amount = self.speed * (dt/1000)
                    if dist > 0:
                        move_x = (dx/dist) * move_amount
                        move_y = (dy/dist) * move_amount
                    self.current_animation = self.walk_animation
                    self.walk_animation.update(dt)
                    self.facing_right = dx > 0
            else:
                if dist > self.peck_range * 0.8:
                    move_amount = self.speed * (dt/1000)
                    if dist > 0:
                        move_x = (dx/dist) * move_amount
                        move_y = (dy/dist) * move_amount
                    self.current_animation = self.walk_animation
                    self.walk_animation.update(dt)
                    self.facing_right = dx > 0
        potential_x = self.x + move_x
        potential_y = self.y + move_y
        for other_enemy in all_enemies:
            if other_enemy is self or not other_enemy.is_alive:
                continue
            temp_rect = pygame.Rect(potential_x, potential_y, self.width, self.height)
            if temp_rect.colliderect(other_enemy.hitbox_rect):
                other_center_x, other_center_y = other_enemy.hitbox_rect.center
                separation_dx = center_x - other_center_x
                separation_dy = center_y - other_enemy.hitbox_rect.center[1]
                sep_dist = math.sqrt(separation_dx**2 + separation_dy**2)
                if sep_dist > 0:
                    nudge_strength = move_amount * 0.5
                    move_x += (separation_dx / sep_dist) * nudge_strength
                    move_y += (separation_dy / sep_dist) * nudge_strength
        self.x += move_x
        self.y += move_y
        self.x = max(boundary_rect.left, min(self.x, boundary_rect.right - self.width))
        self.y = max(boundary_rect.top, min(self.y, boundary_rect.bottom - self.height))
        self.hitbox_rect.center = (self.x + self.width/2, self.y + self.height/2)

    def draw(self, surface, debug=False):
        if not self.is_alive:
            return
        img = self.current_animation.get_frame()
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (self.x, self.y))
        if debug:
            pygame.draw.rect(surface, (255,0,255), self.hitbox_rect, 1)
            if self.is_attacking and self.current_attack == 'peck':
                pygame.draw.rect(surface, (255,0,0), self.attack_rect, 1)
