import pygame
from penguin import Penguin
from arctic_fox import ArcticFox
from seal import Seal
from wave_manager import WaveManager
from healthbar import HealthBar 
from special_meter import SpecialMeter
import os
import math

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
    background = pygame.Surface((display_W, display_H))
    background.fill((50, 50, 50))

penguin = Penguin(scale=SCALE)
penguin.x = walkable_rect.centerx - (penguin.width / 2)
penguin.y = walkable_rect.bottom - penguin.height

health_bar = HealthBar(scale=SCALE)
special_meter = SpecialMeter(scale=SCALE)
penguin.set_special_meter(special_meter)

wave_manager = WaveManager(scale=SCALE, boundary_rect=walkable_rect)
wave_manager.start_next_wave()

running = True
DEBUG_SHOW_BOUNDARIES = True
DEBUG_SHOW_HITBOXES = True

is_enemy_attacking_flag = False
prev_is_special_attacking = False

while running:
    dt = clock.tick(FPS)

    health_bar.set_target_health(penguin.health, penguin.max_health)
    health_bar.update(dt)
    special_meter.update(dt)

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

    target_x = penguin.x + penguin.width / 2
    target_y = penguin.y + penguin.height / 2
    
    prev_is_special_attacking = penguin.is_special_attacking
    
    penguin.update(dt, walkable_rect)
    wave_manager.update(dt, target_x, target_y)

    if prev_is_special_attacking and not penguin.is_special_attacking:
        penguin.external_special_meter.reset_power()

    penguin_hitbox = pygame.Rect(penguin.x, penguin.y, penguin.width, penguin.height)

    is_enemy_attacking_flag = any(
        (enemy.is_attacking or (hasattr(enemy, 'is_sliding') and enemy.is_sliding))
        for enemy in wave_manager.enemies if enemy.is_alive
    )

    for enemy in list(wave_manager.enemies):
        enemy_center_x = enemy.x + enemy.width / 2
        penguin_center_x = penguin.x + penguin.width / 2
        
        distance_to_player = math.sqrt((enemy_center_x - penguin_center_x)**2 + (enemy.y - penguin.y)**2)

        if isinstance(enemy, ArcticFox):
            if not is_enemy_attacking_flag and not enemy.is_attacking and enemy.cooldown_timer <= 0 and distance_to_player <= enemy.attack_range:
                target_is_right_of_fox = (penguin_center_x > enemy_center_x)
                if enemy.start_attack(target_is_right_of_fox):
                    is_enemy_attacking_flag = True
                    break

    if penguin.current_attack_damage > 0:
        active_hitboxes = []
        if penguin.is_attacking:
            active_hitboxes.append(penguin.attack_hitbox_rect)
        elif penguin.is_special_attacking:
            active_hitboxes.append(penguin.left_attack_hitbox_rect)
            active_hitboxes.append(penguin.right_attack_hitbox_rect)
            
        for hitbox in active_hitboxes:
            for enemy in list(wave_manager.enemies):
                if enemy.is_alive and hitbox.colliderect(enemy.hitbox_rect):
                    if enemy not in penguin.enemies_hit_in_attack:
                        damage_dealt = penguin.current_attack_damage
                        enemy.take_damage(damage_dealt)
                        if not penguin.is_special_attacking:
                            penguin.external_special_meter.add_power(damage_dealt * 0.5)
                        if not penguin.is_special_attacking:
                            penguin.enemies_hit_in_attack.add(enemy)

    for enemy in list(wave_manager.enemies):
        is_enemy_attacking = enemy.is_attacking or (hasattr(enemy, 'is_sliding') and enemy.is_sliding)
        
        if is_enemy_attacking and enemy.attack_rect.colliderect(penguin_hitbox):
            should_hit = False
            
            if isinstance(enemy, Seal):
                if enemy.is_sliding and enemy.slide_timer >= enemy.slide_buildup_duration:
                    if enemy.hits_landed == 0:
                        should_hit = True
                elif enemy.is_attacking and enemy.hits_landed == 1:
                    should_hit = True

            elif isinstance(enemy, ArcticFox):
                current_frame_index = enemy.current_animation.index
                hit_number = 0
                if current_frame_index in enemy.hit_frames:
                    hit_number = list(enemy.hit_frames).index(current_frame_index) + 1
                if hit_number > enemy.hits_landed:
                    enemy.hits_landed = hit_number
                    should_hit = True

            if should_hit:
                damage_taken = enemy.current_damage if hasattr(enemy, 'current_damage') and enemy.current_damage > 0 else enemy.damage_per_hit
                penguin.take_damage(damage_taken)
                penguin.external_special_meter.subtract_power(damage_taken * 0.2)
                if isinstance(enemy, Seal) and enemy.is_sliding:
                    enemy.hits_landed = 1
                if isinstance(enemy, Seal) and enemy.is_attacking and not enemy.is_sliding:
                    enemy.hits_landed = 0

    canvas.blit(background, (0, 0))
    
    wave_manager.draw(canvas, DEBUG_SHOW_HITBOXES)
    penguin.draw(canvas, DEBUG_SHOW_HITBOXES)

    health_bar.draw(canvas, 20, 20)
    
    if health_bar.frames:
        meter_y = 20 + health_bar.frames[0].get_height() + 5
    else:
        meter_y = 50
        
    special_meter.draw(canvas, 20, meter_y)

    if DEBUG_SHOW_BOUNDARIES:
        pygame.draw.rect(canvas, (255, 0, 0), walkable_rect, 2)
    
    if DEBUG_SHOW_HITBOXES:
        pygame.draw.rect(canvas, (255, 255, 0), penguin_hitbox, 2)

    window.blit(canvas, (0, 0))
    pygame.display.flip()

pygame.quit()
