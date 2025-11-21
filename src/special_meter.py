import pygame
from spritesheet import Spritesheet
import json
import os
import math

class SpecialMeter:
    def __init__(self, scale):
        self.scale = scale
        self.spritesheet = Spritesheet("../Assets/Sheets/specialMeter_Sheet.png", scale)         
        self.frames = []
        script_dir = os.path.dirname(__file__)
        json_path = os.path.abspath(os.path.join(script_dir, "../Assets/Sheets/specialMeter.json"))
        
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
        self.MAX_POWER = self.max_frame_index + 1
        self.current_power = 0.0
        self.display_frame_index = 0.0       
        self.fill_speed_frames_per_sec = 100 
        
    def add_power(self, amount):
        self.current_power = min(self.MAX_POWER, self.current_power + amount)

    def subtract_power(self, amount):
        self.current_power = max(0.0, self.current_power - amount)

    def is_full(self):
        return self.current_power >= self.MAX_POWER

    def reset_power(self):
        self.current_power = 0.0

    def update(self, dt):
        if not self.frames:
            return

        target_frame_index = self.current_power * (self.max_frame_index / self.MAX_POWER)
        
        if self.display_frame_index < target_frame_index:
            frames_to_increase = self.fill_speed_frames_per_sec * (dt / 1000)
            self.display_frame_index += frames_to_increase
            
            if self.display_frame_index > target_frame_index:
                self.display_frame_index = target_frame_index
        
        elif self.display_frame_index > target_frame_index:
            frames_to_decrease = self.fill_speed_frames_per_sec * (dt / 1000) * 2 
            self.display_frame_index -= frames_to_decrease
            
            if self.display_frame_index < target_frame_index:
                self.display_frame_index = target_frame_index
                
        self.display_frame_index = max(0.0, min(self.display_frame_index, float(self.max_frame_index)))

    def draw(self, surface, x, y):
        if not self.frames:
            return
            
        frame_to_draw = int(round(self.display_frame_index))
        
        frame_to_draw = max(0, min(frame_to_draw, self.max_frame_index))
        
        surface.blit(self.frames[frame_to_draw], (x, y))