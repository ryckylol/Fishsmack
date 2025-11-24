import pygame
import random
import math
from spritesheet import Spritesheet
from animation import Animation
import os

class SmokeParticle:
    def __init__(self, x, y, color, size, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.initial_size = size
        self.size = size
        self.vx = velocity[0]
        self.vy = velocity[1]
        self.lifetime = lifetime
        self.age = 0
        self.gravity = 0.005

    def update(self, dt):
        dt_s = dt / 1000.0
        self.age += dt
        self.x += self.vx * dt_s * 100
        self.y += self.vy * dt_s * 100
        self.vy += self.gravity * dt_s * 10
        self.vx *= 0.99
        progress = self.age / self.lifetime
        self.size = max(0, self.initial_size * (1 - progress))

    def is_alive(self):
        return self.age < self.lifetime

    def draw(self, surface):
        if self.size > 1:
            draw_color = self.color[:3]
            try:
                pygame.draw.circle(surface, draw_color, (int(self.x), int(self.y)), int(self.size))
            except ValueError:
                pass


class PolarBear(pygame.sprite.Sprite):
    def __init__(self, scale, x, y):
        super().__init__()
        self.scale = scale * 1.8
        self.facing_right = False

        self.STATE_INITIAL_LANDING = 0
        self.STATE_LANDING_WAIT = 1
        self.STATE_ROARING = 2
        self.STATE_FIGHTING = 3
        self.STATE_COOLDOWN = 4
        self.STATE_TRANSITION_RUN = 5
        self.STATE_FINAL_PHASE = 6
        self.STATE_DEFEATED = 7
        self.STATE_FINAL_FALL = 8
        self.current_state = self.STATE_INITIAL_LANDING

        fall_sheet = Spritesheet("../Assets/Sheets/polarBear_fall_Sheet.png", self.scale)
        self.anim_fall = Animation(fall_sheet, [(0,0,64,64),(64,0,64,64),(128,0,64,64),(192,0,64,64)], 500)

        angry_sheet = Spritesheet("../Assets/Sheets/polarBear_angry_Sheet.png", self.scale)
        self.anim_angry = Animation(angry_sheet, [(0,0,64,64),(64,0,64,64),(128,0,64,64)], 9999)

        base_sheet = Spritesheet("../Assets/Sheets/polarBear_base_Sheet.png", self.scale)
        self.anim_idle = Animation(base_sheet, [(0,0,64,64)])

        swing_sheet = Spritesheet("../Assets/Sheets/polarBear_threePartSwing_Sheet.png", self.scale)
        self.anim_swing = Animation(swing_sheet, [(0,0,64,64),(64,0,64,64),(128,0,64,64),(192,0,64,64),(256,0,64,64),(320,0,64,64),(384,0,64,64)], 150)

        slam_sheet = Spritesheet("../Assets/Sheets/polarBear_slam_Sheet.png", self.scale)
        self.anim_slam = Animation(slam_sheet, [(0,0,64,64),(64,0,64,64),(128,0,64,64)], 300)

        run_sheet = Spritesheet("../Assets/Sheets/polarBear_run_Sheet.png", self.scale)
        self.anim_run = Animation(run_sheet, [(0,0,64,64),(64,0,64,64),(128,0,64,64),(192,0,64,64)], 100)

        script_dir = os.path.dirname(__file__)
        roar_filename = "../Assets/audio/bearRoar.mp3"
        roar_full_path = os.path.abspath(os.path.join(script_dir, roar_filename))
        self.roar_sound = None

        try:
            pygame.mixer.init()
            self.roar_sound = pygame.mixer.Sound(roar_full_path)
            self.roar_sound.set_volume(0.4)
        except pygame.error as e:
            print(f"Warning: Could not load sound file '{roar_filename}'. Error: {e}")

        self.particles = []

        self.current_animation = self.anim_fall
        self.image = self.current_animation.get_frame()
        self.rect = self.image.get_rect()

        self.x = x
        self.y = -1000
        self.rect.topleft = (self.x, self.y)

        self.width = self.rect.width
        self.height = self.rect.height

        self.velocity_y = 0
        self.gravity = 0.5 * self.scale
        self.speed = 250 * self.scale
        self.run_speed = 100 * self.scale

        self.max_health = 2500
        self.health = self.max_health
        self.is_alive = True

        self.hitbox_rect = pygame.Rect(0,0,int(self.width*0.6),int(self.height*0.8))

        self.attack_hitbox_rect = pygame.Rect(-1000,-1000,0,0)
        self.current_attack_damage = 0
        self.hits_landed = set()

        self.initial_health_for_transition = self.max_health * 0.4

        self.state_timer = 0
        self.is_roaring = False
        self.attacks_done = 0
        self.max_attacks_before_cooldown = 2
        self.cooldown_duration = 5000

        self.is_attacking = False
        self.attack_cooldown = 4500
        self.current_attack_type = None

        self.SWING_DAMAGE = 2
        self.SLAM_DAMAGE = 3

        self.ATTACK_SWING = "swing"
        self.ATTACK_SLAM = "slam"

        self.SWING_HIT_FRAMES = {2,3,4,5}
        self.SLAM_HIT_FRAMES = {1,2}

        self.center_x = 0

        self.run_cycle_count = 0
        self.target_run_cycles = 4
        self.running_direction = 1
        self.transition_fall_started = False

        self.final_phase_speed = 350 * self.scale

        self.vulnerable = False
        self.playing_fake_fall = False
        self.run_phase_count = 0
        self.max_run_phases = 2
        self.pending_final_fall = False
        self.fallen_permanent = False

        self.run_collision_damage = 25
        self.run_hits_landed = set()

        self.final_phase_run_count = 0
        self.final_phase_max_runs_before_fall = 3
        self.final_phase_falling = False
        self.final_phase_fall_duration = 1000
        self.final_phase_fall_timer = 0

        self.defeat_fall_started = False
        self.MIN_HEALTH_TO_FALL = 1
        self.waiting_for_final_blow = False
        self.fall_when_running_damage_threshold = 50

    def start_attack(self):
        if self.is_attacking or self.state_timer < self.attack_cooldown or self.fallen_permanent or self.defeat_fall_started or self.pending_final_fall:
            return False
        if self.current_state in [self.STATE_FINAL_PHASE, self.STATE_DEFEATED, self.STATE_FINAL_FALL]:
            return False

        self.is_attacking = True
        self.state_timer = 0
        self.hits_landed.clear()
        self.attacks_done += 1

        self.current_attack_type = random.choice([self.ATTACK_SWING, self.ATTACK_SLAM])

        if self.current_attack_type == self.ATTACK_SWING:
            self.current_animation = self.anim_swing
            self.anim_swing.reset()
            self.current_attack_damage = self.SWING_DAMAGE
        else:
            self.current_animation = self.anim_slam
            self.anim_slam.reset()
            self.current_attack_damage = self.SLAM_DAMAGE

        self.attack_hitbox_rect.topleft = (-1000,-1000)
        return True

    def update_attack_hitbox(self, boundary_rect):
        if not self.is_attacking:
            self.attack_hitbox_rect.topleft = (-1000,-1000)
            return

        f = self.current_animation.index
        t = self.current_attack_type

        scale_multiplier = 2.0

        if t == self.ATTACK_SWING:
            if f in self.SWING_HIT_FRAMES:
                w = int(self.hitbox_rect.width * scale_multiplier)
                h = int(self.hitbox_rect.height * scale_multiplier)
                center_x = self.hitbox_rect.centerx
                if self.facing_right:
                    left = center_x - w * 0.25
                else:
                    left = center_x - w + w * 0.25
                top = self.hitbox_rect.top
                self.attack_hitbox_rect.update(left, top, w, h)
            else:
                self.attack_hitbox_rect.topleft = (-1000,-1000)
        elif t == self.ATTACK_SLAM:
            if f in self.SLAM_HIT_FRAMES:
                w = int(self.hitbox_rect.width * scale_multiplier * 1.5)
                h = int(self.hitbox_rect.height * scale_multiplier * 0.5)
                left = self.hitbox_rect.centerx - w // 2
                top = self.hitbox_rect.bottom - h
                self.attack_hitbox_rect.update(left, top, w, h)
            else:
                self.attack_hitbox_rect.topleft = (-1000,-1000)

    def is_animation_finished(self):
        return self.current_animation.index >= len(self.current_animation.frames)-1

    def _spawn_smoke_effect(self):
        center_x = self.hitbox_rect.centerx
        bottom_y = self.hitbox_rect.bottom
        hitbox_width = self.hitbox_rect.width
        spread_half_width = hitbox_width * 1.6

        for _ in range(12):
            spawn_x = random.uniform(center_x - spread_half_width, center_x + spread_half_width)
            angle = random.uniform(160, 380)
            speed = random.uniform(0.25 * self.scale, 0.65 * self.scale)
            vx = speed * math.cos(math.radians(angle))
            vy = speed * math.sin(math.radians(angle))
            size = random.randint(int(5 * self.scale), int(14 * self.scale))
            lifetime = random.randint(300, 520)
            self.particles.append(SmokeParticle(spawn_x, bottom_y, (255, 255, 255, 255), size, (vx, vy), lifetime))

    def update(self, dt, target_x, target_y, boundary_rect, all_enemies, projectiles=None):
        self.state_timer += dt
        dt_s = dt/1000

        target_floor = boundary_rect.centery - self.height/2
        self.center_x = boundary_rect.centerx - self.width/2

        self.particles = [p for p in self.particles if p.is_alive()]
        for p in self.particles:
            p.update(dt)

        if self.current_state == self.STATE_DEFEATED:
            self.current_animation = self.anim_fall
            self.anim_fall.index = len(self.anim_fall.frames)-1
            self.image = self.current_animation.get_frame()
            self.rect.topleft = (self.x, self.y)
            self.hitbox_rect.centerx = self.rect.centerx
            self.hitbox_rect.bottom = self.rect.bottom
            self.attack_hitbox_rect.topleft = (-1000,-1000)
            self.vulnerable = True
            self.fallen_permanent = True
            self.is_alive = False
            return

        elif self.current_state == self.STATE_FINAL_FALL:
            self.current_animation = self.anim_fall
            self.x = self.center_x
            self.attack_hitbox_rect.topleft = (-1000,-1000)

            if self.waiting_for_final_blow:
                self.vulnerable = True
                self.anim_fall.index = len(self.anim_fall.frames) - 1
                self.is_alive = self.health > 0

                if self.health <= 0:
                    self.current_state = self.STATE_DEFEATED
                    self.health = 0

            else:
                self.vulnerable = False
                self.anim_fall.update(dt)

                if self.is_animation_finished():
                    self.waiting_for_final_blow = True
                    self.health = self.MIN_HEALTH_TO_FALL

            self.image = self.current_animation.get_frame()
            self.rect.topleft = (self.x, self.y)
            self.hitbox_rect.centerx = self.rect.centerx
            self.hitbox_rect.bottom = self.rect.bottom
            return

        if self.current_state == self.STATE_INITIAL_LANDING:
            self.current_animation = self.anim_fall
            self.velocity_y += self.gravity
            self.y += self.velocity_y

            if self.y >= target_floor:
                self.y = target_floor
                self.velocity_y = 0
                self.current_state = self.STATE_LANDING_WAIT
                self.state_timer = 0
                self.anim_angry.index = 0
                self.x = self.center_x

        elif self.current_state == self.STATE_LANDING_WAIT:
            self.current_animation = self.anim_angry
            self.anim_angry.index = 0
            self.vulnerable = False
            if self.state_timer >= 2000:
                self.current_state = self.STATE_ROARING
                self.state_timer = 0
                if self.roar_sound:
                    self.roar_sound.play()

        elif self.current_state == self.STATE_ROARING:
            self.current_animation = self.anim_angry
            self.anim_angry.index = 1
            self.is_roaring = True
            self.vulnerable = False

            if self.state_timer >= 800:
                self.current_state = self.STATE_FIGHTING
                self.is_roaring = False
                self.anim_angry.index = 2
                self.x = self.center_x
                self.state_timer = self.attack_cooldown

        elif self.current_state == self.STATE_FIGHTING:
            self.is_attacking = self.is_attacking and not self.is_animation_finished()
            self.facing_right = target_x > self.x + self.width/2
            self.vulnerable = True

            if self.is_attacking:
                self.current_animation.update(dt)

                f = self.current_animation.index
                t = self.current_attack_type

                is_hit_frame = (
                    (t == self.ATTACK_SWING and f in self.SWING_HIT_FRAMES) or
                    (t == self.ATTACK_SLAM and f in self.SLAM_HIT_FRAMES)
                )

                if is_hit_frame:
                    self._spawn_smoke_effect()

                if self.is_animation_finished():
                    self.is_attacking = False
                    self.current_attack_type = None
                    self.current_attack_damage = 0
                    self.state_timer = 0

                    if self.attacks_done >= self.max_attacks_before_cooldown:
                        self.current_state = self.STATE_COOLDOWN
                    else:
                        self.current_animation = self.anim_idle

            else:
                self.current_animation = self.anim_idle
                self.current_animation.update(dt)

                if self.state_timer >= self.attack_cooldown:
                    self.start_attack()

        elif self.current_state == self.STATE_COOLDOWN:
            self.current_animation = self.anim_angry
            self.anim_angry.index = 2
            self.is_attacking = False
            self.attack_hitbox_rect.topleft = (-1000,-1000)
            self.vulnerable = False

            if self.state_timer >= self.cooldown_duration:
                self.current_state = self.STATE_FIGHTING
                self.attacks_done = 0
                self.state_timer = self.attack_cooldown

        elif self.current_state == self.STATE_TRANSITION_RUN:
            self.current_animation = self.anim_run
            self.y = target_floor
            self.x += self.running_direction * self.speed * dt_s
            self.facing_right = self.running_direction == 1
            self.vulnerable = True

            if self.running_direction == 1 and self.x + self.width > boundary_rect.right:
                self.running_direction = -1
                self.run_cycle_count += 1
            elif self.running_direction == -1 and self.x < boundary_rect.left:
                self.running_direction = 1
                self.run_cycle_count += 1

            if self.run_cycle_count >= self.target_run_cycles:
                if abs(self.x - self.center_x) < 20 * self.scale:
                    self.x = self.center_x
                    self.current_state = self.STATE_FIGHTING
                    self.state_timer = self.attack_cooldown
                    self.anim_angry.index = 2
                    self.vulnerable = True
                    self.run_phase_count += 1
                    self.run_cycle_count = 0
                else:
                    if self.x < self.center_x:
                        self.running_direction = 1
                    else:
                        self.running_direction = -1

        elif self.current_state == self.STATE_FINAL_PHASE:
            self.current_animation = self.anim_run
            self.y = target_floor
            self.x += self.running_direction * self.final_phase_speed * dt_s
            self.facing_right = self.running_direction == 1
            self.vulnerable = True

            boundary_hit = False

            if self.running_direction == 1 and self.x + self.width > boundary_rect.right:
                self.running_direction = -1
                boundary_hit = True
            elif self.running_direction == -1 and self.x < boundary_rect.left:
                self.running_direction = 1
                boundary_hit = True

            if boundary_hit:
                self.final_phase_run_count += 1
                if self.final_phase_run_count >= self.final_phase_max_runs_before_fall:
                    self.x = self.center_x
                    self._trigger_final_defeat()

        if self.current_state not in [self.STATE_DEFEATED, self.STATE_FINAL_FALL]:
            self.current_animation.update(dt)

        self.image = self.current_animation.get_frame()

        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect.topleft = (self.x, self.y)
        self.hitbox_rect.centerx = self.rect.centerx
        self.hitbox_rect.bottom = self.rect.bottom

        if self.current_state == self.STATE_FIGHTING and self.is_attacking:
            self.update_attack_hitbox(boundary_rect)
        else:
            self.attack_hitbox_rect.topleft = (-1000,-1000)

    def take_damage(self, amount):
        if self.fallen_permanent:
            self.health -= amount
            if self.health <= 0:
                self.health = 0
                self.is_alive = False
            return

        if self.defeat_fall_started and not self.waiting_for_final_blow:
            return

        if not self.vulnerable:
            return

        new_health = self.health - amount

        if new_health <= self.MIN_HEALTH_TO_FALL and not self.defeat_fall_started:
            self.health = self.MIN_HEALTH_TO_FALL
            self._trigger_final_defeat()
            return

        if self.current_state == self.STATE_FINAL_FALL and self.waiting_for_final_blow and new_health <= 0:
            self.health = 0
            return

        is_running_state = self.current_state in [self.STATE_TRANSITION_RUN, self.STATE_FINAL_PHASE]

        if is_running_state and amount >= self.fall_when_running_damage_threshold:
            self.health = new_health
            if self.health < self.MIN_HEALTH_TO_FALL:
                self.health = self.MIN_HEALTH_TO_FALL
                self._trigger_final_defeat()
            return

        self.is_attacking = False
        self.attack_hitbox_rect.topleft = (-1000,-1000)
        self.vulnerable = False
        self.x = self.center_x
        self.current_state = self.STATE_FIGHTING
        self.state_timer = self.attack_cooldown
        self.anim_angry.index = 2

        self.run_cycle_count = 0
        self.final_phase_run_count = 0
        self.transition_fall_started = False
        self.final_phase_falling = False

        self.health = new_health

        if (self.current_state == self.STATE_FIGHTING and self.run_phase_count < self.max_run_phases and self.health <= self.initial_health_for_transition):
            self.current_state = self.STATE_TRANSITION_RUN
            self.state_timer = 0
            self.run_cycle_count = 0
            self.running_direction = 1 if self.x < self.center_x else -1
            self.is_attacking = False
            self.attack_hitbox_rect.topleft = (-1000,-1000)
            self.vulnerable = True
            self.anim_run.reset()
            health_chunk = (self.max_health / (self.max_run_phases + 1))
            self.initial_health_for_transition -= health_chunk

    def _trigger_final_defeat(self):
        self.is_attacking = False
        self.attack_hitbox_rect.topleft = (-1000,-1000)
        self.vulnerable = False
        self.defeat_fall_started = True
        self.x = self.center_x
        self.waiting_for_final_blow = False
        self.current_state = self.STATE_FINAL_FALL
        self.anim_fall.reset()
        self.pending_final_fall = True

    def run_collision_and_damage(self, penguin):
        if self.current_state not in [self.STATE_TRANSITION_RUN, self.STATE_FINAL_PHASE]:
            return

        peng_id = id(penguin)
        penguin_rect = pygame.Rect(penguin.x, penguin.y, penguin.width, penguin.height)

        if not self.fallen_permanent and self.hitbox_rect.colliderect(penguin_rect):
            if peng_id not in self.run_hits_landed:
                penguin.take_damage(self.run_collision_damage)

                if hasattr(penguin, "external_special_meter") and penguin.external_special_meter is not None:
                    penguin.external_special_meter.subtract_power(self.run_collision_damage * 0.2)

                self.run_hits_landed.add(peng_id)

    def draw(self, surface, debug_show_hitboxes=False):
        surface.blit(self.image, self.rect)
        for p in self.particles:
            p.draw(surface)

        if debug_show_hitboxes:
            pygame.draw.rect(surface,(255,0,0),self.hitbox_rect,2)
            pygame.draw.rect(surface,(0,255,0),self.attack_hitbox_rect,2)
