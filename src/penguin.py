import pygame
from spritesheet import Spritesheet
from animation import Animation
import math

class Penguin:
    MAX_HEALTH = 140
    MAX_SPECIAL_FUEL = 100
    SPECIAL_SOUND_INTERVAL = 85

    def __init__(self, scale):
        self.scale = scale
        self.idle_sheet = Spritesheet("../Assets/Sheets/penguin_base_Sheet.png", scale)
        idle_frame_data = [(0, 0, 64, 64)]
        self.idle_animation = Animation(self.idle_sheet, idle_frame_data, frame_duration=300)
        self.movement_sheet = Spritesheet("../Assets/Sheets/penguin_walkCycle_Sheet.png", scale)
        movement_frame_data = [(64, 0, 64, 64),(0, 0, 64, 64)]
        self.movement_animation = Animation(self.movement_sheet, movement_frame_data, frame_duration=150)
        self.swing_light_sheet = Spritesheet("../Assets/Sheets/penguin_swingL_Sheet.png", scale)
        light_frame_data = [(0, 0, 64, 64),(64, 0, 64, 64)]
        self.light_animation = Animation(self.swing_light_sheet, light_frame_data, frame_duration=100)
        self.light_attack_duration = len(light_frame_data) * 100
        self.swing_heavy_sheet = Spritesheet("../Assets/Sheets/penguin_swingH_Sheet.png", scale)
        heavy_frame_data = [(0, 0, 64, 64),(64, 0, 64, 64)]
        self.heavy_animation = Animation(self.swing_heavy_sheet, heavy_frame_data, frame_duration=100)
        self.heavy_attack_duration = len(heavy_frame_data) * 100
        self.swing_special_sheet = Spritesheet("../Assets/Sheets/penguin_swingS_Sheet.png", scale)
        special_frame_data = [(0, 0, 64, 64),(64, 0, 64, 64)]
        self.special_animation = Animation(self.swing_special_sheet, special_frame_data, frame_duration=300)
        self.attack_sound = None
        try:
            self.attack_sound = pygame.mixer.Sound("../Assets/audio/fishSlap.mp3")
            self.attack_sound.set_volume(0.25)
        except pygame.error as e:
            print(f"Warning: Could not load attack sound '../Assets/audio/fishSlap.mp3'. Error: {e}")
        self.special_meter = 0
        self.external_special_meter = None
        self.min_special_cost = 0
        self.special_drain_rate = 50
        self.is_special_attacking = False
        self.special_speed_multiplier = 1.5
        self.special_flip_timer = 0
        self.special_flip_interval = 100
        self.special_sound_timer = 0
        self.wobble_timer = 0
        self.wobble_speed = 10
        self.wobble_amplitude = 5 * scale
        self.special_hitbox_size = (int(50 * scale), int(40 * scale))
        self.left_attack_hitbox_rect = pygame.Rect(0, 0, *self.special_hitbox_size)
        self.right_attack_hitbox_rect = pygame.Rect(0, 0, *self.special_hitbox_size)
        self.current_animation = self.idle_animation
        self.x = 0
        self.y = 0
        self.sprite_width = 64 * scale
        self.sprite_height = 64 * scale
        self.width = 25 * scale
        self.height = 25 * scale
        self.hurtbox_offset_x = (self.sprite_width - 25 * scale) / 2
        self.hurtbox_offset_y = (self.sprite_height - 25 * scale) / 2
        self.hurtbox = pygame.Rect(self.x, self.y, 50 * scale, 40 * scale)
        self.is_alive = True
        self.speed = 300
        self.facing_right = True
        self.max_health = self.MAX_HEALTH
        self.health = self.max_health
        self.is_attacking = False
        self.attack_type = None
        self.light_damage = 15
        self.heavy_damage = 30
        self.special_damage = 10
        self.current_attack_damage = 0
        self.enemies_hit_in_attack = set()
        self.max_combo_hits = 3
        self.combo_hit_count = 0
        self.combo_reset_time = 600
        self.combo_reset_timer = 0
        self.light_cooldown = 300
        self.heavy_cooldown = 500
        self.special_cooldown = 300
        self.attack_cooldown_timer = 0
        self.hitbox_size = (int(50 * scale), int(40 * scale))
        self.attack_hitbox_rect = pygame.Rect(0, 0, *self.hitbox_size)
        self.attack_hitbox_rect.topleft = (-1000, -1000)
        self.damage_flash_timer = 0
        self.damage_flash_duration = 150
        self.flash_color = (255, 100, 100)

    def set_special_meter(self, meter_ref):
        self.external_special_meter = meter_ref

    def take_damage(self, damage_amount):
        if self.health <= 0 or not self.is_alive:
            return
        self.health -= damage_amount
        if self.health < 0:
            self.health = 0
        self.damage_flash_timer = self.damage_flash_duration
        if self.health == 0:
            self.is_alive = False

    def start_attack(self):
        if not self.is_alive or self.is_attacking or self.attack_cooldown_timer > 0 or self.is_special_attacking:
            return
        if self.combo_reset_timer <= 0:
            self.combo_hit_count = 0
        if self.combo_hit_count >= self.max_combo_hits:
            return
        if self.attack_sound:
            self.attack_sound.play()
        self.combo_hit_count += 1
        self.is_attacking = True
        self.attack_type = 'light'
        self.attack_active_timer = 0
        self.current_animation = self.light_animation
        self.light_animation.reset()
        self.current_attack_damage = self.light_damage
        self.enemies_hit_in_attack.clear()
        self.combo_reset_timer = 0

    def start_heavy_attack(self):
        if not self.is_alive or self.is_attacking or self.attack_cooldown_timer > 0 or self.is_special_attacking:
            return
        if self.attack_sound:
            self.attack_sound.play()
        self.combo_hit_count = 0
        self.is_attacking = True
        self.attack_type = 'heavy'
        self.attack_active_timer = 0
        self.current_animation = self.heavy_animation
        self.heavy_animation.reset()
        self.current_attack_damage = self.heavy_damage
        self.enemies_hit_in_attack.clear()
        self.combo_reset_timer = 0

    def start_special_attack(self):
        if not self.is_alive or self.attack_cooldown_timer > 0 or self.is_special_attacking:
            return
        if self.external_special_meter is None or not self.external_special_meter.is_full():
            return
        self.external_special_meter.reset_power()
        self.is_attacking = False
        self.attack_type = None
        self.combo_hit_count = 0
        self.combo_reset_timer = 0
        self.is_special_attacking = True
        self.current_animation = self.special_animation
        self.special_animation.reset()
        self.current_attack_damage = self.special_damage
        self.enemies_hit_in_attack.clear()
        self.special_flip_timer = 0
        self.special_sound_timer = 0
        self.wobble_timer = 0
        self.special_meter = self.MAX_SPECIAL_FUEL
        if self.attack_sound:
            self.attack_sound.play()

    def update(self, dt, boundary_rect, enemy_hitboxes):
        if not self.is_alive:
            return
        keys = pygame.key.get_pressed()
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= dt
            if self.damage_flash_timer < 0:
                self.damage_flash_timer = 0
        self.attack_hitbox_rect.topleft = (-1000, -1000)
        self.left_attack_hitbox_rect.topleft = (-1000, -1000)
        self.right_attack_hitbox_rect.topleft = (-1000, -1000)
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= dt
            if self.attack_cooldown_timer < 0:
                self.attack_cooldown_timer = 0
        if self.combo_reset_timer > 0:
            self.combo_reset_timer -= dt
            if self.combo_reset_timer <= 0:
                self.combo_hit_count = 0
        if self.is_special_attacking:
            animation_ended = self.current_animation.index == len(self.current_animation.frames) - 1
            if not animation_ended:
                self.current_animation.update(dt)
            if animation_ended:
                self.special_flip_timer += dt
                if self.special_flip_timer >= self.special_flip_interval:
                    self.facing_right = not self.facing_right
                    self.special_flip_timer = 0
                self.wobble_timer += self.wobble_speed * (dt / 1000)
                self.special_sound_timer += dt
                if self.special_sound_timer >= self.SPECIAL_SOUND_INTERVAL:
                    if self.attack_sound:
                        self.attack_sound.play()
                    self.special_sound_timer = 0
            drain_amount = self.special_drain_rate * (dt / 1000)
            self.special_meter -= drain_amount
            if self.special_meter <= 0:
                self.special_meter = 0
                self.is_special_attacking = False
                self.current_animation = self.idle_animation
                self.current_attack_damage = 0
                self.enemies_hit_in_attack.clear()
                self.attack_cooldown_timer = self.special_cooldown
        elif self.is_attacking:
            self.attack_active_timer += dt
            self.current_animation.update(dt)
            if self.attack_type == 'light':
                attack_duration = self.light_attack_duration
            elif self.attack_type == 'heavy':
                attack_duration = self.heavy_attack_duration
            else:
                attack_duration = 100
            if self.attack_active_timer >= attack_duration:
                self.is_attacking = False
                self.current_attack_damage = 0
                self.enemies_hit_in_attack.clear()
                self.attack_active_timer = 0
                self.current_animation = self.idle_animation
                if self.attack_type == 'heavy':
                    self.attack_cooldown_timer = self.heavy_cooldown
                    self.combo_hit_count = 0
                    self.combo_reset_timer = 0
                elif self.attack_type == 'light':
                    if self.combo_hit_count == self.max_combo_hits:
                        self.attack_cooldown_timer = self.light_cooldown
                        self.combo_hit_count = 0
                        self.combo_reset_timer = 0
                    else:
                        self.combo_reset_timer = self.combo_reset_time
        is_moving = False
        current_speed = self.speed
        can_move = not self.is_attacking
        if self.is_special_attacking:
            current_speed *= self.special_speed_multiplier
        if can_move:
            move_amount = current_speed * (dt / 1000)
            if keys[pygame.K_w]: self.y -= move_amount
            if keys[pygame.K_s]: self.y += move_amount
            if keys[pygame.K_a]:
                self.x -= move_amount
                if not self.is_special_attacking: self.facing_right = False
            if keys[pygame.K_d]:
                self.x += move_amount
                if not self.is_special_attacking: self.facing_right = True
            if not self.is_special_attacking:
                if keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]:
                    if self.current_animation != self.movement_animation:
                        self.current_animation = self.movement_animation
                        self.movement_animation.reset()
                    self.current_animation.update(dt)
                else:
                    if self.current_animation != self.idle_animation:
                        self.current_animation = self.idle_animation
                        self.idle_animation.reset()
        collision_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        collision_rect.x = max(boundary_rect.left, min(collision_rect.x, boundary_rect.right - self.width))
        collision_rect.y = max(boundary_rect.top, min(collision_rect.y, boundary_rect.bottom - self.height))
        for enemy_hitbox in enemy_hitboxes:
            if collision_rect.colliderect(enemy_hitbox):
                dx = collision_rect.centerx - enemy_hitbox.centerx
                dy = collision_rect.centery - enemy_hitbox.centery
                overlap_x = (collision_rect.width / 2) + (enemy_hitbox.width / 2) - abs(dx)
                overlap_y = (collision_rect.height / 2) + (enemy_hitbox.height / 2) - abs(dy)
                if overlap_x > 0 and (overlap_x < overlap_y or overlap_y < 0):
                    if dx > 0:
                        collision_rect.x += overlap_x
                    else:
                        collision_rect.x -= overlap_x
                elif overlap_y > 0 and (overlap_y < overlap_x or overlap_x < 0):
                    if dy > 0:
                        collision_rect.y += overlap_y
                    else:
                        collision_rect.y -= overlap_y
        self.x, self.y = collision_rect.x, collision_rect.y
        self.hurtbox.topleft = (self.x - self.hurtbox_offset_x + (self.width/2), self.y - self.hurtbox_offset_y + (self.height/2))
        hitbox_y = self.y + (self.height / 2) - (self.hitbox_size[1] / 2)
        if self.is_special_attacking:
            hitbox_left_x = self.x - self.special_hitbox_size[0] + (5 * self.scale)
            hitbox_right_x = self.x + self.width - (5 * self.scale)
            self.left_attack_hitbox_rect.topleft = (hitbox_left_x, hitbox_y)
            self.right_attack_hitbox_rect.topleft = (hitbox_right_x, hitbox_y)
        elif self.is_attacking:
            self.attack_hitbox_rect.size = (int(50 * self.scale), int(40 * self.scale))
            if self.facing_right:
                hitbox_x = self.x + self.width - (5 * self.scale)
            else:
                hitbox_x = self.x - self.hitbox_size[0] + (5 * self.scale)
            self.attack_hitbox_rect.topleft = (hitbox_x, hitbox_y)

    def draw(self, surface, debug_show_hitboxes=False):
        if not self.is_alive:
            return
        image = self.current_animation.get_frame().copy()
        if self.damage_flash_timer > 0:
            image.fill(self.flash_color, special_flags=pygame.BLEND_RGB_ADD)
        draw_x = self.x - self.hurtbox_offset_x
        draw_y = self.y - self.hurtbox_offset_y
        if self.is_special_attacking:
            offset = math.sin(self.wobble_timer * math.pi * 2) * self.wobble_amplitude
            draw_x += offset
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        surface.blit(image, (draw_x, draw_y))
        if debug_show_hitboxes:
            pygame.draw.rect(surface, (255, 0, 0), self.hurtbox, 2)
            if self.is_special_attacking:
                pygame.draw.rect(surface, (0, 255, 255), self.left_attack_hitbox_rect, 2)
                pygame.draw.rect(surface, (0, 255, 255), self.right_attack_hitbox_rect, 2)
            elif self.is_attacking:
                pygame.draw.rect(surface, (0, 255, 255), self.attack_hitbox_rect, 2)
