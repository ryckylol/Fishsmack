import pygame

class Animation:
    def __init__(self, spritesheet, frame_data, frame_duration=100):
        self.frames = []
        for x, y, w, h in frame_data:
            self.frames.append(spritesheet.get_sprite(x, y, w, h))
            
        self.frame_duration = frame_duration
        self.time_since_last_frame = 0
        self.index = 0
        self.loop = True
        
    def update(self, dt):
        self.time_since_last_frame += dt
        
        if self.time_since_last_frame >= self.frame_duration:
            self.time_since_last_frame = 0
            self.index += 1
            
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1

    def get_frame(self):
        if not self.frames:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        return self.frames[self.index]
        
    def reset(self):
        self.index = 0
        self.time_since_last_frame = 0