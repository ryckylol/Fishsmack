import pygame
from spritesheet import Spritesheet
import json
import os
import math

class HealthBar:
    def __init__(self, scale):
        self.scale = scale
        self.spritesheet = Spritesheet("../Assets/Sheets/healthbar_Sheet.png", scale)         
        self.frames = []
        script_dir = os.path.dirname(__file__)
        json_path = os.path.abspath(os.path.join(script_dir, "../Assets/Sheets/healthbar.json"))
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.max_frame_index = 0
            return

        frame_keys = sorted(data['frames'].keys(), 
                            key=lambda k: int(k.split(' ')[1].split('.')[0]))
        
        for key in frame_keys:
            frame_data = data['frames'][key]['frame']
            rect = (frame_data['x'], frame_data['y'], frame_data['w'], frame_data['h'])
            self.frames.append(self.spritesheet.get_sprite(*rect))
            
        self.max_frame_index = len(self.frames) - 1 
        self.display_health_frame_index = 0.0
        self.target_frame_index = 0         
        self.drop_speed_frames_per_sec = 165 * 3        
        self.display_health_frame_index = 0.0
        self.target_frame_index = 0 

    def update(self, dt):
        
        if self.display_health_frame_index < self.target_frame_index: 
            frames_to_increase = self.drop_speed_frames_per_sec * (dt / 1000)
            
            self.display_health_frame_index += frames_to_increase
            
            if self.display_health_frame_index > self.target_frame_index:
                self.display_health_frame_index = float(self.target_frame_index)

        elif self.display_health_frame_index > self.target_frame_index:
            frames_to_decrease = self.drop_speed_frames_per_sec * (dt / 1000) * 0.5 
            
            self.display_health_frame_index -= frames_to_decrease
            
            if self.display_health_frame_index < self.target_frame_index:
                self.display_health_frame_index = float(self.target_frame_index)
        
        self.display_health_frame_index = max(0.0, self.display_health_frame_index)

    def set_target_health(self, current_health, max_health):
        if max_health <= 0 or self.max_frame_index <= 0:
            self.target_frame_index = self.max_frame_index
            return

        health_ratio = current_health / max_health
        inverted_index_float = self.max_frame_index * (1 - health_ratio)
        
        self.target_frame_index = max(0, min(math.ceil(inverted_index_float), self.max_frame_index))

    def draw(self, surface, x, y):
        
        if not self.frames:
            return
            
        frame_to_draw = int(self.display_health_frame_index)
        
        frame_to_draw = max(0, min(frame_to_draw, self.max_frame_index))
        
        surface.blit(self.frames[frame_to_draw], (x, y))