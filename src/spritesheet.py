import pygame

class Spritesheet:
    def __init__(self, filename, scale_factor=1):
        self.filename = filename
        self.scale_factor = scale_factor
        self.sprite_sheet = pygame.image.load(filename).convert_alpha()

    def get_sprite(self, x, y, w, h, sprite_scale=None, size=None):
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, w, h))

        if size is not None:
            sprite = pygame.transform.scale(sprite, size)
            return sprite

        final_scale = self.scale_factor

        if sprite_scale is not None:
            final_scale *= sprite_scale
        
        if final_scale != 1:
            new_w = int(w * final_scale)
            new_h = int(h * final_scale)
            sprite = pygame.transform.scale(sprite, (new_w, new_h))

        return sprite