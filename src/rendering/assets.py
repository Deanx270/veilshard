import pygame
from src.core.resources import resource

_SHARED_CACHE = {}

class Assets:
    def __init__(self, use_cache=True):
        self.cache = _SHARED_CACHE if use_cache else {}

    def image(self, path, size, preserve_aspect=False):
        key = (path, tuple(size), preserve_aspect) if preserve_aspect else (path, tuple(size))
        if key not in self.cache:
            try:
                raw = pygame.image.load(str(resource(path)))
                try:
                    image = raw.convert_alpha()
                except (pygame.error, AttributeError):
                    image = raw
                target = (max(1, round(image.get_width() * size[1] / image.get_height())), size[1]) if preserve_aspect else size
                self.cache[key] = pygame.transform.smoothscale(image, target)
            except (FileNotFoundError, pygame.error):
                self.cache[key] = None
        return self.cache[key]

    @classmethod
    def clear_cache(cls):
        _SHARED_CACHE.clear()
