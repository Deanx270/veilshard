import pygame
from src.core.resources import resource

class Assets:
    def __init__(self):
        self.cache = {}

    def image(self, path, size, preserve_aspect=False):
        key = (path, tuple(size), preserve_aspect) if preserve_aspect else (path, tuple(size))
        if key not in self.cache:
            try:
                image = pygame.image.load(str(resource(path))).convert_alpha()
                target = (max(1, round(image.get_width() * size[1] / image.get_height())), size[1]) if preserve_aspect else size
                self.cache[key] = pygame.transform.smoothscale(image, target)
            except (FileNotFoundError, pygame.error):
                self.cache[key] = None
        return self.cache[key]
