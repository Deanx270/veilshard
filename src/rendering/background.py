import math
import random
import pygame
from src.rendering.ember_forest import draw_ember_forest

class Background:
    """Full-canvas layers; images are loaded/scaled once, never each frame."""
    def __init__(self, assets, stage):
        self.accent = stage["accent"]
        self.layers = []
        for layer in stage["background"].get("layers", []):
            self.layers.append((layer, [assets.image(layer["path"], (1600, 900))]))
        for sequence in stage["background"].get("sequences", []):
            self.layers.append((sequence, [assets.image(path, (1600, 900)) for path in sequence["frames"]]))
        self.fallback = self._placeholder(stage["id"])

    def _placeholder(self, stage_id):
        surface = pygame.Surface((1600, 900))
        accent = self.accent
        for y in range(900):
            t = y / 900
            pygame.draw.line(surface, (int(12+accent[0]*0.10*t), int(17+accent[1]*0.07*t), int(32+accent[2]*0.10*t)), (0,y), (1600,y))
        glow = pygame.Surface((1600,900), pygame.SRCALPHA)
        for radius in range(280, 20, -8):
            pygame.draw.circle(glow, (*accent, 3), (800, 320), radius)
        surface.blit(glow,(0,0))
        rng = random.Random(stage_id)
        for _ in range(75):
            x,y=rng.randrange(1600),rng.randrange(580)
            pygame.draw.circle(surface, (79,86,113), (x,y), 1)
        pygame.draw.circle(surface, (87,91,122), (800,285), 130, 1)
        pygame.draw.circle(surface, (70,75,106), (800,285), 145, 1)
        for x in (100,260,1320,1480):
            height = rng.randrange(260,470)
            if stage_id in (1,4):
                pygame.draw.polygon(surface,(18,30,40),[(x-38,650),(x-18,200),(x+15,160),(x+32,650)])
                for offset in (-90,70):
                    pygame.draw.line(surface,(18,30,40),(x,400),(x+offset,210),18)
            else:
                pygame.draw.polygon(surface,(26,35,53),[(x-40,650),(x-40,650-height),(x,620-height),(x+40,650-height),(x+40,650)])
                pygame.draw.line(surface, (53,66,89),(x-40,650-height),(x-40,650),2)
        pygame.draw.polygon(surface,(20,26,42),[(0,650),(600,570),(1000,570),(1600,650),(1600,900),(0,900)])
        for y in (640,700,800):
            pygame.draw.line(surface,(38,45,64),(0,y),(1600,y),1)
        for x in range(-800,2600,300):
            pygame.draw.line(surface,(38,45,64),(800,560),(x,900),1)
        if stage_id == 1:
            draw_ember_forest(surface)
        return surface

    def draw(self, surface, time, foreground=False, shake=(0,0)):
        if not foreground:
            surface.blit(self.fallback, shake)
        for layer, frames in self.layers:
            if bool(layer.get("foreground",False)) != foreground or not frames:
                continue
            frame=frames[int(time*layer.get("fps",8))%len(frames)]
            if frame:
                # Move opposite edges slightly offscreen; exports should include overscan.
                depth=layer.get("depth",0)
                offset=math.sin(time*0.3)*depth*8
                surface.blit(frame,(round(offset+shake[0]),shake[1]))
        if not foreground:
            for i in range(24):
                x=(i*167+time*(9+i%4))%1600
                y=170+(i*79-time*12)%450
                pygame.draw.circle(surface,self.accent,(int(x),int(y)),1+i%2)
