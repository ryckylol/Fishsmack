import pygame
from arctic_fox import ArcticFox
from seal import Seal
import random

class WaveManager:
    def __init__(self, scale, boundary_rect):
        self.scale = scale
        self.boundary_rect = boundary_rect
        self.current_wave = 1
        self.enemies = pygame.sprite.Group()
        self.spawn_queue = []
        self.max_enemies_on_screen = 5
        self.wave_complete = True
        self.wave_start_delay = 2000
        self.wave_timer = 0        
        self.setup_waves()

    def setup_waves(self):
        wave_1 = [
            {"type": ArcticFox, "side": "right"},
            {"type": ArcticFox, "side": "right"},
            {"type": ArcticFox, "side": "right"},
            {"type": "wait_for_clear"}, 
            {"type": ArcticFox, "side": "left"},
            {"type": ArcticFox, "side": "left"},
            {"type": ArcticFox, "side": "right"},
        ]

        wave_2_part_1 = [
            {"type": Seal, "side": "left"},
            {"type": Seal, "side": "left"},
            {"type": Seal, "side": "right"},
            {"type": Seal, "side": "right"},
            {"type": "wait_for_clear"},
        ]

        part_2_enemies = []

        side_3_count = random.choice(["left", "right"])
        side_2_count = "right" if side_3_count == "left" else "left"

        num_seals = random.randint(1, 4) 
        num_foxes = 5 - num_seals
        
        all_enemies = [Seal] * num_seals + [ArcticFox] * num_foxes
        random.shuffle(all_enemies)

        side_3_enemies = []
        side_2_enemies = []
        
        for i in range(5):
            enemy_type = all_enemies[i]
            if len(side_3_enemies) < 3:
                side_3_enemies.append({"type": enemy_type, "side": side_3_count})
            else:
                side_2_enemies.append({"type": enemy_type, "side": side_2_count})
        
        part_2_enemies.extend(side_3_enemies)
        part_2_enemies.extend(side_2_enemies)
        random.shuffle(part_2_enemies)
        
        wave_2 = wave_2_part_1 + part_2_enemies


        self.wave_definitions = {
            1: wave_1,
            2: wave_2,
        }

    def start_next_wave(self):
        if self.current_wave in self.wave_definitions:
            self.spawn_queue = list(self.wave_definitions[self.current_wave])
            self.wave_complete = False
        else:
            self.wave_complete = True

    def spawn_enemy(self, enemy_type, side):
        enemy_width = 64 * self.scale
        enemy_height = 64 * self.scale
        spawn_y_min = self.boundary_rect.top
        spawn_y_max = self.boundary_rect.bottom - enemy_height
        spawn_y = random.uniform(spawn_y_min, spawn_y_max)
        
        if side == "right":
            spawn_x = self.boundary_rect.right 
        else:
            spawn_x = self.boundary_rect.left - enemy_width 

        enemy = enemy_type(scale=self.scale, x=spawn_x, y=spawn_y)
        enemy.facing_right = (side == "left") 
        self.enemies.add(enemy)


    def update(self, dt, target_x, target_y):
        
        all_enemies_list = self.enemies.sprites()

        for enemy in list(self.enemies):
            enemy.update(dt, target_x, target_y, self.boundary_rect, all_enemies_list) 
            if not enemy.is_alive:
                self.enemies.remove(enemy)
                
        if self.wave_complete and self.current_wave in self.wave_definitions:
            self.wave_timer += dt
            if self.wave_timer >= self.wave_start_delay:
                self.start_next_wave()
                self.wave_timer = 0
            return
            
        if not self.spawn_queue and not self.enemies:
            self.current_wave += 1
            self.wave_complete = True
            self.wave_timer = 0
            self.setup_waves() 
            return
            
        if self.spawn_queue:
            next_spawn = self.spawn_queue[0]
            
            if next_spawn["type"] == "wait_for_clear":
                if not self.enemies:
                    self.spawn_queue.pop(0)
                else:
                    return
                    
            elif len(self.enemies) < self.max_enemies_on_screen:
                enemy_type = next_spawn["type"]
                side = next_spawn["side"]
                self.spawn_enemy(enemy_type, side)
                self.spawn_queue.pop(0)

    def draw(self, surface, debug_show_hitboxes):
        for enemy in self.enemies:
            enemy.draw(surface, debug_show_hitboxes)