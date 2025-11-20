import pygame

class Spritesheet:
    def __init__(self, filename, scale_factor=1):
        self.sprite_sheet = pygame.image.load(filename).convert_alpha()
        print(f"DEBUG: Loaded {filename}")
        print(f"DEBUG: Image Size is {self.sprite_sheet.get_size()}")
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