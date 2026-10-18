"""Composite the entire 2D world before camera transforms; UI stays fixed."""
import math
import pygame
from src.rendering.background import Background
from src.rendering.characters import CharacterSprite
from src.rendering.parallax import ParallaxBackground, ParallaxCamera


class Camera:
    def __init__(self, config: dict):
        self.base_zoom = max(1.0, min(1.25, config.get("zoom", 1.0)))
        self.impact_zoom = max(0.0, min(0.12, config.get("impact_zoom", 0.035)))
        self.focus = config.get("focus", [800, 430])
        self.remaining = 0.0
        self.clock = 0.0
        self.buffer = None
        self.strength = 1.0

    def impact(self, strength=1.0):
        self.strength=strength
        self.remaining = 0.28

    def update(self, dt: float):
        self.clock += dt
        self.remaining = max(0.0, self.remaining-dt)

    @property
    def zoom(self):
        return self.base_zoom + self.impact_zoom * self.strength * math.sin(math.pi*self.remaining/0.28)

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
        shake = self.remaining / 0.28 * 4 * self.strength
        x = (1-zoom)*self.focus[0] + math.sin(self.clock*95)*shake
        y = (1-zoom)*self.focus[1] + math.cos(self.clock*81)*shake
        # Keep the frame covered even with a focus near an edge.
        x = max(destination.get_width()-size[0], min(0, round(x)))
        y = max(destination.get_height()-size[1], min(0, round(y)))
        destination.blit(self.buffer, (x, y))


class Battlefield:
    def __init__(self, assets, stage: dict):
        self.parallax = "manifest" in stage["background"]
        self.background = ParallaxBackground(assets,stage["background"]) if self.parallax else Background(assets, stage)
        self.camera = ParallaxCamera(self.background,stage.get("camera",{})) if self.parallax else Camera(stage.get("camera", {}))
        self.motion=None
        self.reactions={}
        self.world = pygame.Surface(self.background.size if self.parallax else (1600, 900))
        self.effect_layer=pygame.Surface((1600,900),pygame.SRCALPHA)
        self.actors = {
            key: CharacterSprite(assets, stage[key], stage["accent"] if key == "opponent" else (146,175,244),
                                 enemy=key == "opponent", beast=key == "opponent" and stage["id"] in (2,4))
            for key in ("player", "opponent")
        }

    def feedback(self, effects, source: str, action: str):
        for effect in effects:
            target = "player" if effect.target == "player" else "opponent"
            if effect.kind == "damage":
                self.actors[target].trigger("hit")
                heavy=action in ("heavy","special")
                self.camera.impact(1.55 if heavy else 0.65)
                self.reactions[target]=(0.30, 22 if heavy else 11)

    def update(self, dt: float):
        self.camera.update(dt)
        self.reactions={k:(max(0,t-dt),power) for k,(t,power) in self.reactions.items() if t>dt}
        for actor in self.actors.values():
            actor.update(dt)

    def draw(self, destination, time, effects, font):
        self.background.draw(self.world, time)
        ground_offset=self.background.actor_offset if self.parallax else (0,0)
        for key in sorted(self.actors,key=lambda key:self.actors[key].order):
            offset=(0,0)
            if self.motion and self.motion.source==key: offset=self.motion.offset()
            if key in self.reactions:
                t,power=self.reactions[key]
                offset=((1 if key=="opponent" else -1)*power*math.sin(math.pi*t/0.30),0)
            self.actors[key].draw(self.world,tuple(offset[i]+ground_offset[i] for i in range(2)))
        self.background.draw(self.world, time, foreground=True)
        if self.motion and self.motion.active and self.motion.kind in ("attack","heavy","special"):
            t=(self.motion.elapsed-(self.motion.impact-0.08))/0.08
            if 0<=t<1:
                source=self.actors[self.motion.source].spec
                target=self.actors["opponent" if self.motion.source=="player" else "player"].spec
                start=(source["position"][0],source["position"][1]-source["size"][1]*source.get("scale",1)*0.5)
                end=(target["position"][0],target["position"][1]-target["size"][1]*target.get("scale",1)*0.5)
                start=tuple(start[i]+ground_offset[i] for i in range(2))
                end=tuple(end[i]+ground_offset[i] for i in range(2))
                head=tuple(start[i]+(end[i]-start[i])*t for i in range(2))
                tail=tuple(start[i]+(end[i]-start[i])*max(0,t-0.18) for i in range(2))
                heavy=self.motion.kind in ("heavy","special")
                pygame.draw.line(self.world,(219,167,244) if heavy else (251,204,139),tail,head,7 if heavy else 3)
                x,y=head
                pygame.draw.polygon(self.world,(255,235,208),[(x-9,y),(x,y-5),(x+9,y),(x,y+5)])
        if self.parallax:
            self.effect_layer.fill((0,0,0,0))
            effects.draw(self.effect_layer,font)
            self.world.blit(self.effect_layer,tuple(round(v) for v in ground_offset))
        else: effects.draw(self.world, font)
        self.camera.present(self.world, destination)
