import pygame
import random
import math
from penguin import Penguin
from arctic_fox import ArcticFox
from seal import Seal
from giant_petrel import GiantPetrel
from polar_bear import PolarBear
from wave_manager import WaveManager
from healthbar import HealthBar
from special_meter import SpecialMeter
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

floor_top = int(display_H * 0.40)
floor_height = display_H - floor_top - 12
side_padding = -10

walkable_rect = pygame.Rect(side_padding, floor_top, display_W - (side_padding * 2), floor_height)

script_dir = os.path.dirname(__file__)
background_filename = "../Assets/background.png"
background_full_path = os.path.abspath(os.path.join(script_dir, background_filename))

try:
    background = pygame.image.load(background_full_path).convert()
    background = pygame.transform.scale(background, (display_W, display_H))
except FileNotFoundError:
    background = pygame.Surface((display_W, display_H))
    background.fill((50, 50, 50))

music_filename = "../Assets/audio/arcticMusic.mp3"
music_full_path = os.path.abspath(os.path.join(script_dir, music_filename))

MUSIC_MUTED = False
MUSIC_VOLUME = 0.2
MUSIC_START_DELAY_MS = 2000

try:
    pygame.mixer.init()
    pygame.mixer.music.load(music_full_path)
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1, 0.0, MUSIC_START_DELAY_MS)
except pygame.error as e:
    print(f"Warning: Could not load or play music file '{music_filename}'. Error: {e}")

class SmokeParticle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.size = random.randint(5, 12)
        self.max_lifetime = random.randint(30, 60)
        self.lifetime = self.max_lifetime
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.0, 3.0)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle) - random.uniform(0.5, 1.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.98
        self.vy *= 0.98
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime) ** 2)
        current_size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        grey_value = 40 + int(80 * (1 - self.lifetime / self.max_lifetime))
        color = (grey_value, grey_value, grey_value)
        particle_surface = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        particle_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(particle_surface, (*color, alpha), (current_size, current_size), current_size)
        surface.blit(particle_surface, (int(self.x) - current_size, int(self.y) - current_size))

class SmokePoofSystem:
    def __init__(self):
        self.particles = []

    def create_poof(self, x, y, num_particles=30):
        for _ in range(num_particles):
            self.particles.append(SmokeParticle(x, y))

    def update(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

penguin = Penguin(scale=SCALE)
penguin.x = walkable_rect.centerx - (penguin.width / 2)
penguin.y = walkable_rect.bottom - penguin.height

health_bar = HealthBar(scale=SCALE)
special_meter = SpecialMeter(scale=SCALE)
penguin.set_special_meter(special_meter)

wave_manager = WaveManager(scale=SCALE, boundary_rect=walkable_rect, penguin=penguin, special_meter=special_meter)
wave_manager.start_next_wave()

smoke_system = SmokePoofSystem()

running = True
DEBUG_SHOW_BOUNDARIES = True
DEBUG_SHOW_HITBOXES = True

prev_is_special_attacking = False
shake_offset = [0, 0]
shake_intensity = 0
was_penguin_alive = penguin.is_alive

while running:
    dt = clock.tick(FPS)
    shake_offset = [0, 0]
    shake_intensity = 0

    health_bar.set_target_health(penguin.health, penguin.max_health)
    health_bar.update(dt)
    special_meter.update(dt)

    cutscene_active = False
    polar_bear = next((e for e in wave_manager.enemies if isinstance(e, PolarBear)), None)
    if polar_bear and polar_bear.current_state == polar_bear.STATE_INITIAL_LANDING:
        cutscene_active = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                MUSIC_MUTED = not MUSIC_MUTED
                if MUSIC_MUTED:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            if penguin.is_alive and not cutscene_active:
                if event.key == pygame.K_j:
                    penguin.start_attack()
                elif event.key == pygame.K_k:
                    penguin.start_heavy_attack()
                elif event.key == pygame.K_l:
                    penguin.start_special_attack()

    target_x = penguin.x + penguin.width / 2
    target_y = penguin.y + penguin.height / 2

    prev_is_special_attacking = penguin.is_special_attacking

    if cutscene_active:
        dist_to_left = abs(penguin.x - walkable_rect.left)
        dist_to_right = abs(penguin.x + penguin.width - walkable_rect.right)
        target_edge_x = walkable_rect.left if dist_to_left < dist_to_right else walkable_rect.right - penguin.width
        speed = penguin.speed * (dt / 1000)
        if abs(penguin.x - target_edge_x) > 5:
            penguin.x += speed if penguin.x < target_edge_x else -speed
            penguin.facing_right = penguin.x < target_edge_x
            if penguin.current_animation != penguin.movement_animation:
                penguin.current_animation = penguin.movement_animation
                penguin.movement_animation.reset()
            penguin.current_animation.update(dt)
        else:
            if penguin.current_animation != penguin.idle_animation:
                penguin.current_animation = penguin.idle_animation
                penguin.idle_animation.reset()
            penguin.current_animation.update(dt)
        penguin.attack_hitbox_rect.topleft = (-1000, -1000)
        penguin.x = max(walkable_rect.left, min(penguin.x, walkable_rect.right - penguin.width))
    else:
        enemy_hitboxes = [e.hitbox_rect for e in wave_manager.enemies if e.is_alive]
        penguin.update(dt, walkable_rect, enemy_hitboxes)

    smoke_system.update()
    wave_manager.update(dt, target_x, target_y)

    for enemy in wave_manager.enemies:
        if isinstance(enemy, PolarBear) and enemy.is_roaring:
            shake_intensity = 10
            shake_offset[0] = random.randint(-shake_intensity, shake_intensity)
            shake_offset[1] = random.randint(-shake_intensity, shake_intensity)

    if prev_is_special_attacking and not penguin.is_special_attacking:
        penguin.external_special_meter.reset_power()

    penguin_hitbox = pygame.Rect(penguin.x, penguin.y, penguin.width, penguin.height)

    if penguin.current_attack_damage > 0:
        active_hitboxes = []
        if penguin.is_attacking:
            active_hitboxes.append(penguin.attack_hitbox_rect)
        elif penguin.is_special_attacking:
            active_hitboxes.append(penguin.left_attack_hitbox_rect)
            active_hitboxes.append(penguin.right_attack_hitbox_rect)
        for hitbox in active_hitboxes:
            for enemy in list(wave_manager.enemies):
                if enemy.is_alive and hitbox.colliderect(enemy.hitbox_rect) and enemy not in penguin.enemies_hit_in_attack:
                    damage_dealt = penguin.current_attack_damage
                    enemy.take_damage(damage_dealt)
                    if enemy.health <= 0:
                        smoke_system.create_poof(enemy.x + enemy.width / 2, enemy.y + enemy.height, 200 if isinstance(enemy, PolarBear) else 30)
                    if not penguin.is_special_attacking:
                        penguin.external_special_meter.add_power(damage_dealt * 0.5)
                        penguin.enemies_hit_in_attack.add(enemy)

    for proj in list(wave_manager.projectiles):
        if proj.hitbox_rect.colliderect(penguin_hitbox):
            penguin.take_damage(proj.damage)
            penguin.external_special_meter.subtract_power(proj.damage * 0.2)
            proj.kill()
            GiantPetrel.decrement_wind_counter()

    for enemy in list(wave_manager.enemies):
        should_hit = False
        damage_taken = 0
        if isinstance(enemy, ArcticFox):
            if enemy.is_attacking and enemy.attack_rect.colliderect(penguin_hitbox):
                current_frame_index = enemy.current_animation.index
                hit_number = 0
                if current_frame_index in enemy.hit_frames:
                    hit_number = list(enemy.hit_frames).index(current_frame_index) + 1
                if hit_number > enemy.hits_landed:
                    enemy.hits_landed = hit_number
                    should_hit = True
                    damage_taken = enemy.damage_per_hit
        elif isinstance(enemy, Seal):
            if enemy.is_sliding and enemy.slide_timer >= enemy.slide_buildup_duration and enemy.attack_rect.colliderect(penguin_hitbox):
                if enemy.hits_landed == 0:
                    should_hit = True
                    enemy.hits_landed = 1
                    damage_taken = enemy.current_damage
            elif enemy.is_attacking and enemy.attack_rect.colliderect(penguin_hitbox) and enemy.hits_landed == 0:
                should_hit = True
                enemy.hits_landed = 1
                damage_taken = enemy.current_damage
        elif isinstance(enemy, GiantPetrel):
            if enemy.is_attacking and enemy.current_attack == 'peck' and enemy.attack_rect.colliderect(penguin_hitbox) and enemy.hits_landed == 0:
                should_hit = True
                enemy.hits_landed = 1
                damage_taken = enemy.peck_damage
        elif isinstance(enemy, PolarBear) and enemy.current_state == enemy.STATE_FIGHTING:
            if enemy.hitbox_rect.colliderect(penguin_hitbox):
                damage_taken = 0
                should_hit = False
        if should_hit:
            penguin.take_damage(damage_taken)
            if damage_taken > 0:
                penguin.external_special_meter.subtract_power(damage_taken * 0.2)
        if isinstance(enemy, PolarBear):
            enemy.run_collision_and_damage(penguin)
            if enemy.current_attack_damage > 0 and enemy.attack_hitbox_rect.colliderect(penguin_hitbox) and id(penguin) not in enemy.hits_landed:
                penguin.take_damage(enemy.current_attack_damage)
                penguin.external_special_meter.subtract_power(enemy.current_attack_damage * 0.2)
                enemy.hits_landed.add(id(penguin))

    if penguin.health <= 0 and was_penguin_alive:
        smoke_system.create_poof(penguin.x + penguin.width / 2, penguin.y + penguin.height)

    was_penguin_alive = penguin.is_alive

    canvas.blit(background, (0, 0))
    wave_manager.draw(canvas, DEBUG_SHOW_HITBOXES)
    penguin.draw(canvas, DEBUG_SHOW_HITBOXES)
    smoke_system.draw(canvas)
    health_bar.draw(canvas, 20, 20)
    meter_y = 20 + (health_bar.frames[0].get_height() + 5 if health_bar.frames else 50)
    special_meter.draw(canvas, 20, meter_y)

    if DEBUG_SHOW_BOUNDARIES:
        pygame.draw.rect(canvas, (255, 0, 0), walkable_rect, 2)
    if DEBUG_SHOW_HITBOXES:
        pygame.draw.rect(canvas, (255, 255, 0), penguin_hitbox, 2)

    window.blit(canvas, shake_offset)
    pygame.display.flip()

pygame.quit()
