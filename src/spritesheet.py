import pygame
import os

class Spritesheet:
    def __init__(self, filename, scale_factor=1):
        self.filename = filename
        script_dir = os.path.dirname(__file__)
        full_path = os.path.abspath(os.path.join(script_dir, filename))
        
        try:
            if not os.path.exists(full_path):
                current_dir = os.getcwd()
                full_path = os.path.abspath(os.path.join(current_dir, filename))
                
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File not found in expected locations: {full_path}")
                
            self.sprite_sheet = pygame.image.load(full_path).convert_alpha()
        except pygame.error:
            self.sprite_sheet = pygame.Surface((128, 64), pygame.SRCALPHA)
            self.sprite_sheet.fill((255, 0, 255))
        except FileNotFoundError:
            self.sprite_sheet = pygame.Surface((128, 64), pygame.SRCALPHA)
            self.sprite_sheet.fill((255, 0, 255))
            
        self.scale_factor = scale_factor

    def get_sprite(self, x, y, w, h, sprite_scale=None):
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, w, h))

        scale = self.scale_factor
        if sprite_scale:
            scale *= sprite_scale

        if scale != 1:
            sprite = pygame.transform.scale(
                sprite,
                (int(w * scale), int(h * scale))
            )

        return sprite