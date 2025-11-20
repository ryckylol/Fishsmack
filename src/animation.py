class Animation:
    def __init__(self, spritesheet, frame_rects, frame_duration):
        self.frames = [spritesheet.get_sprite(*rect) for rect in frame_rects]
        self.frame_duration = frame_duration
        
        self.index = 0
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        while self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.index = (self.index + 1) % len(self.frames)

    def get_frame(self):
        return self.frames[self.index]