"""Composite the entire 2D world before camera transforms; UI stays fixed."""
import math
import pygame
from src.rendering.background import Background
from src.rendering.characters import CharacterSprite


class Camera:
    def __init__(self, config: dict):
        self.base_zoom = max(1.0, min(1.25, config.get("zoom", 1.0)))
        self.impact_zoom = max(0.0, min(0.12, config.get("impact_zoom", 0.035)))
        self.focus = config.get("focus", [800, 430])
        self.remaining = 0.0
        self.clock = 0.0
        self.buffer = None

    def impact(self):
        self.remaining = 0.28

    def update(self, dt: float):
        self.clock += dt
        self.remaining = max(0.0, self.remaining-dt)

    @property
    def zoom(self):
        return self.base_zoom + self.impact_zoom * math.sin(math.pi*self.remaining/0.28)

    def present(self, world, destination):
        zoom = self.zoom
        if self.remaining == 0 and zoom == 1:
            destination.blit(world, (0, 0))
            return
        # Quantization limits buffer reallocations; source assets remain cached.
        zoom = round(max(zoom, 1.012 if self.remaining else 1.0)*200)/200
        size = (round(world.get_width()*zoom), round(world.get_height()*zoom))
        if self.buffer is None or self.buffer.get_size() != size:
            self.buffer = pygame.Surface(size)
        pygame.transform.smoothscale(world, size, self.buffer)
        shake = self.remaining / 0.28 * 4
        x = (1-zoom)*self.focus[0] + math.sin(self.clock*95)*shake
        y = (1-zoom)*self.focus[1] + math.cos(self.clock*81)*shake
        # Keep the frame covered even with a focus near an edge.
        x = max(destination.get_width()-size[0], min(0, round(x)))
        y = max(destination.get_height()-size[1], min(0, round(y)))
        destination.blit(self.buffer, (x, y))


class Battlefield:
    def __init__(self, assets, stage: dict):
        self.background = Background(assets, stage)
        self.camera = Camera(stage.get("camera", {}))
        self.world = pygame.Surface((1600, 900))
        self.actors = {
            key: CharacterSprite(assets, stage[key], stage["accent"] if key == "opponent" else (146,175,244),
                                 enemy=key == "opponent", beast=key == "opponent" and stage["id"] in (2,4))
            for key in ("player", "opponent")
        }

    def feedback(self, effects, source: str, action: str):
        self.actors[source].trigger(action)
        for effect in effects:
            target = "player" if effect.target == "player" else "opponent"
            if effect.kind == "damage":
                self.actors[target].trigger("hit")
                self.camera.impact()

    def update(self, dt: float):
        self.camera.update(dt)
        for actor in self.actors.values():
            actor.update(dt)

    def draw(self, destination, time, effects, font):
        self.background.draw(self.world, time)
        for actor in sorted(self.actors.values(), key=lambda actor: actor.order):
            actor.draw(self.world)
        self.background.draw(self.world, time, foreground=True)
        effects.draw(self.world, font)
        self.camera.present(self.world, destination)
