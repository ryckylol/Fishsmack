import pygame
from arctic_fox import ArcticFox
from seal import Seal
from giant_petrel import GiantPetrel
from polar_bear import PolarBear 
import random

class WaveManager:
    def __init__(self, scale, boundary_rect, penguin, special_meter):
        self.scale = scale
        self.boundary_rect = boundary_rect
        self.penguin = penguin
        self.special_meter = special_meter
        self.current_wave = 1
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
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
        all_enemies_w2 = [Seal] * num_seals + [ArcticFox] * num_foxes
        random.shuffle(all_enemies_w2)
        
        for i in range(5):
            enemy_type = all_enemies_w2[i]
            side = side_3_count if i < 3 else side_2_count
            part_2_enemies.append({"type": enemy_type, "side": side})
        random.shuffle(part_2_enemies)
        wave_2 = wave_2_part_1 + part_2_enemies

        main_side = random.choice(["left", "right"])
        opp_side = "right" if main_side == "left" else "left"
        
        wave_3_part_1 = [
            {"type": GiantPetrel, "side": main_side},
            {"type": GiantPetrel, "side": opp_side},
            {"type": GiantPetrel, "side": opp_side},
            {"type": "wait_for_clear"}
        ]

        wave_3_part_2 = []
        side_major = random.choice(["left", "right"])
        side_minor = "right" if side_major == "left" else "left"
        pool_w3 = [GiantPetrel, Seal] 
        for _ in range(3): pool_w3.append(random.choice([GiantPetrel, Seal]))
        random.shuffle(pool_w3)
        
        for i in range(5):
            enemy_type = pool_w3[i]
            side = side_major if i < 3 else side_minor
            wave_3_part_2.append({"type": enemy_type, "side": side})
        wave_3 = wave_3_part_1 + wave_3_part_2

        wave_4 = [
            {"type": PolarBear, "side": "center"}
        ]

        self.wave_definitions = {
            1: wave_1,
            2: wave_2,
            3: wave_3,
            4: wave_4 
        }

    def start_next_wave(self):
        if self.current_wave in self.wave_definitions:
            self.spawn_queue = list(self.wave_definitions[self.current_wave])
            self.wave_complete = False
            print(f"Starting Wave {self.current_wave}")
            if self.current_wave == 4:
                self.penguin.health = self.penguin.max_health
                self.special_meter.reset_power()
        else:
            self.wave_complete = True
            print("All Waves Complete!")

    def spawn_enemy(self, enemy_type, side):
        if enemy_type == PolarBear:
            spawn_x = self.boundary_rect.centerx - (64 * self.scale)
            spawn_y = -500 
            enemy = enemy_type(scale=self.scale, x=spawn_x, y=spawn_y)
            self.enemies.add(enemy)
            return

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
            if isinstance(enemy, GiantPetrel) or isinstance(enemy, PolarBear):
                enemy.update(dt, target_x, target_y, self.boundary_rect, all_enemies_list, self.projectiles)
            else:
                enemy.update(dt, target_x, target_y, self.boundary_rect, all_enemies_list)
                
            if not enemy.is_alive:
                self.enemies.remove(enemy)

        self.projectiles.update(dt)

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
        for enemy in sorted(self.enemies, key=lambda e: e.y + e.height):
            enemy.draw(surface, debug_show_hitboxes)

        for proj in self.projectiles:
            surface.blit(proj.image, proj.rect)
            if debug_show_hitboxes:
                pygame.draw.rect(surface, (0, 255, 255), proj.hitbox_rect, 2)