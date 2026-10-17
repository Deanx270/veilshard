import pygame
from src.core.resources import resource

class Assets:
    def __init__(self):
        self.cache = {}

    def image(self, path, size):
        key = (path, tuple(size))
        if key not in self.cache:
            try:
                image = pygame.image.load(str(resource(path))).convert_alpha()
                self.cache[key] = pygame.transform.smoothscale(image, size)
            except (FileNotFoundError, pygame.error):
                self.cache[key] = None
        return self.cache[key]
