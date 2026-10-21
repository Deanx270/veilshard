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
        self.duration = 0.28
        self.clock = 0.0
        self.buffer = None
        self.strength = 1.0
        self.direction = 1

    def impact(self, strength=1.0, direction=1):
        self.strength=strength
        self.direction=direction
        self.duration = 0.42 if strength > 1.5 else 0.28
        self.remaining = self.duration

    def update(self, dt: float):
        self.clock += dt
        self.remaining = max(0.0, self.remaining-dt)

    @property
    def zoom(self):
        decay = self.remaining / max(0.001, self.duration)
        zoom_mult = 1.6 if self.strength > 1.5 else 1.0
        return self.base_zoom + self.impact_zoom * self.strength * zoom_mult * math.sin(math.pi * decay)

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
    def __init__(self, assets, stage: dict, progress_cb=None):
        self.parallax = "manifest" in stage["background"]
        if progress_cb:
            progress_cb(0.04, "Loading environment background...")
        self.background = ParallaxBackground(assets,stage["background"]) if self.parallax else Background(assets, stage)
        if progress_cb:
            progress_cb(0.10, "Environment ready")
        self.camera = ParallaxCamera(self.background,stage.get("camera",{})) if self.parallax else Camera(stage.get("camera", {}))
        self.motion=None
        self.reactions={}
        self.world = pygame.Surface(self.background.size if self.parallax else (1600, 900))
        self.effect_layer=pygame.Surface((1600,900),pygame.SRCALPHA)
        self.actors = {
            "player": CharacterSprite(assets, stage["player"], (146,175,244),
                                     enemy=False, beast=False, progress_cb=progress_cb, progress_range=(0.10, 0.52)),
            "opponent": CharacterSprite(assets, stage["opponent"], stage["accent"] if "accent" in stage else (146,175,244),
                                       enemy=True, beast=stage["id"] in (2,4), progress_cb=progress_cb, progress_range=(0.52, 0.95))
        }
        if progress_cb:
            progress_cb(1.0, "Stage ready")

    def feedback(self, effects, source: str, action: str):
        for effect in effects:
            target = "player" if effect.target == "player" else "opponent"
            if effect.kind == "damage":
                heavy=action in ("heavy","special")
                hit_state = "hit_heavy" if heavy and ("hit_heavy" in self.actors[target].clips or "hurt_heavy" in self.actors[target].clips) else "hit"
                self.actors[target].trigger(hit_state)
                direction = 1
                if source == "opponent":
                    strength = max(1.8, round(1.7 + max(1, effect.amount) * 0.1, 2)) if heavy else max(0.9, min(1.45, round(0.6 + max(1, effect.amount) * 0.1, 2)))
                else:
                    strength = 2.4 if heavy else 1.1
                self.camera.impact(strength, direction=direction)
                self.reactions[target]=(0.30, 36 if heavy else 19)

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
            procedural_motion = self.actors[key].spec.get("procedural_motion", True)
            if procedural_motion and self.motion and self.motion.source==key: offset=self.motion.offset()
            if procedural_motion and key in self.reactions:
                t,power=self.reactions[key]
                offset=((1 if key=="opponent" else -1)*power*math.sin(math.pi*t/0.30),0)
            self.actors[key].draw(self.world,tuple(offset[i]+ground_offset[i] for i in range(2)))
        self.background.draw(self.world, time, foreground=True)
        if (self.motion and self.motion.active and self.motion.kind in ("attack","heavy","special")
                and self.actors[self.motion.source].spec.get("placeholder_projectile", True)):
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
                pygame.draw.line(self.world,(219,167,244) if heavy else (251,204,139),tail,head,11 if heavy else 5)
                x,y=head
                pygame.draw.polygon(self.world,(255,235,208),[(x-9,y),(x,y-5),(x+9,y),(x,y+5)])
        if self.parallax:
            self.effect_layer.fill((0,0,0,0))
            effects.draw(self.effect_layer,font)
            self.world.blit(self.effect_layer,tuple(round(v) for v in ground_offset))
        else: effects.draw(self.world, font)
        self.camera.present(self.world, destination)
