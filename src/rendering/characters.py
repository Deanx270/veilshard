import pygame
from src.rendering.frame_shadow import FrameShadows

def placeholder(size, accent, enemy=False, beast=False):
    """Original graphic silhouettes; replace via stage character PNG paths."""
    s=pygame.Surface((360,480),pygame.SRCALPHA)
    dark=(26,32,57)
    light=(212,221,240)
    if beast:
        pygame.draw.polygon(s,dark,[(40,390),(70,230),(160,170),(260,215),(320,390),(265,450),(230,330),(130,330),(100,455)])
        pygame.draw.polygon(s,accent,[(90,230),(60,110),(170,185),(270,95),(250,240),(180,290)])
        pygame.draw.polygon(s,dark,[(115,222),(175,196),(235,218),(213,280),(151,280)])
        pygame.draw.line(s,light,(135,235),(157,241),5)
        pygame.draw.line(s,light,(201,241),(222,235),5)
    else:
        pygame.draw.polygon(s,accent,[(155,170),(100,235),(52,425),(170,390),(280,440),(250,230),(205,170)])
        pygame.draw.polygon(s,dark,[(147,183),(115,310),(138,420),(128,456),(164,456),(180,330),(196,456),(231,456),(217,420),(245,310),(207,183)])
        pygame.draw.polygon(s,light,[(151,182),(180,205),(207,183),(196,284),(164,284)])
        pygame.draw.polygon(s,accent,[(169,200),(188,200),(200,300),(177,326),(158,300)])
        pygame.draw.polygon(s,(227,206,213),[(144,104),(181,88),(212,111),(207,161),(183,180),(149,157)])
        pygame.draw.polygon(s,(189,166,188),[(183,180),(207,161),(212,111),(188,126)])
        hair=(214,221,245) if not enemy else (56,61,92)
        pygame.draw.polygon(s,hair,[(131,155),(126,102),(150,65),(193,58),(225,92),(229,165),(204,138),(198,100),(176,128),(170,103),(147,142)])
        pygame.draw.line(s,accent,(151,139),(164,139),3)
        pygame.draw.line(s,accent,(191,139),(204,139),3)
        pygame.draw.polygon(s,dark,[(145,194),(112,214),(78,298),(93,310),(156,241)])
        pygame.draw.polygon(s,dark,[(209,194),(239,214),(278,295),(262,311),(199,240)])
        pygame.draw.polygon(s,light,[(74,289),(92,287),(103,314),(84,321)])
        pygame.draw.polygon(s,accent,[(60,260),(91,247),(108,282),(77,295)],3)
        pygame.draw.line(s,accent,(275,315),(307,140),6)
        pygame.draw.polygon(s,light,[(307,100),(322,137),(307,170),(292,137)])
    # Flat-lit facets evoke low-poly armor while final Blender exports are pending.
    if not beast:
        pygame.draw.polygon(s,tuple(int(c*0.65) for c in accent),[(205,178),(250,230),(280,440),(218,375)])
        pygame.draw.polygon(s,(66,76,108),[(147,183),(115,310),(164,284)])
    return pygame.transform.smoothscale(s,size)


class CharacterSprite:
    """Cached RGBA clips sharing a fixed canvas and normalized ground anchor."""
    def __init__(self, assets, spec: dict, accent, enemy=False, beast=False):
        self.spec = spec
        scale = spec.get("scale", 1.0)
        self.size = tuple(max(1, round(v * scale)) for v in spec["size"])
        fallback = assets.image(spec.get("path", ""), self.size)
        if fallback is None:
            fallback = placeholder(self.size, accent, enemy, beast)
        self.clips = {"idle": ([fallback], 8, True)}
        for name, clip in spec.get("animations", {}).items():
            frames = [assets.image(path, self.size) for path in clip.get("frames", [])]
            frames = [frame for frame in frames if frame is not None]
            if frames:
                self.clips[name] = (frames, max(0.1, clip.get("fps", 8)), clip.get("loop", name == "idle"))
        # Static clip registration corrects differences in exported canvas origin.
        # It never follows the changing silhouette or adds animated displacement.
        self.clip_offsets = {}
        for name in self.clips:
            config = spec.get("animations", {}).get(name, {})
            source_size = config.get("source_size", self.size)
            offset = config.get("canvas_offset", [0, 0])
            self.clip_offsets[name] = tuple(round(offset[i] * self.size[i] / source_size[i]) for i in range(2))
        self.flashes = {}
        for name, (frames, fps, loop) in self.clips.items():
            frames = [pygame.transform.flip(f, True, False) if spec.get("flip_x", False) else f for f in frames]
            self.clips[name] = (frames, fps, loop)
            tinted = []
            for frame in frames:
                flash = frame.copy()
                # Add RGB only, retaining transparent pixels and edge alpha.
                flash.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)
                tinted.append(flash)
            self.flashes[name] = tinted
        shadow = spec.get("shadow", {})
        shadow_size = tuple(max(1, round(v * scale)) for v in shadow.get("size", [160, 42]))
        self.shadow = assets.image(shadow["path"], shadow_size) if shadow.get("path") else None
        if self.shadow is None:
            self.shadow = pygame.Surface(shadow_size, pygame.SRCALPHA)
            pygame.draw.ellipse(self.shadow, (5, 8, 18, shadow.get("opacity", 100)), self.shadow.get_rect())
        self.frame_shadows = FrameShadows([frame for frames, _, _ in self.clips.values() for frame in frames], shadow) if shadow.get("mode") in ("frame", "contact") else None
        self.state = "idle"
        self.elapsed = 0.0
        self.hit_time = 0.0

    @property
    def order(self):
        return self.spec.get("render_order", self.spec["position"][1])

    def action_timing(self, state: str):
        """Use exported clip timing only when every configured frame loaded."""
        config = self.spec.get("animations", {}).get(state, {})
        if "impact_frame" not in config or state not in self.clips:
            return None
        frames, fps, loop = self.clips[state]
        if len(frames) != len(config.get("frames", [])):
            return None
        index = max(1, min(len(frames)-1, config["impact_frame"]))
        return index / fps, len(frames) / fps

    def trigger(self, state: str):
        if state == "hit":
            self.hit_time = 0.20
        if state in self.clips:
            self.state = state
            self.elapsed = 0.0

    def update(self, dt: float):
        self.hit_time = max(0.0, self.hit_time - dt)
        self.elapsed += dt
        frames, fps, loop = self.clips[self.state]
        if not loop and self.elapsed >= len(frames) / fps:
            self.state = "idle"
            self.elapsed = 0.0

    def frame_index(self):
        frames, fps, loop = self.clips[self.state]
        index = int(self.elapsed * fps)
        index = index % len(frames) if loop else min(index, len(frames)-1)
        return index

    def frame(self):
        index = self.frame_index()
        return self.flashes[self.state][index] if self.hit_time > 0 else self.clips[self.state][0][index]

    def draw(self, surface, displacement=(0,0)):

        pos = [self.spec["position"][i]+displacement[i] for i in range(2)]
        anchor = self.spec.get("anchor", [0.5, 1.0])
        shadow = self.spec.get("shadow", {})
        offset = shadow.get("offset", [0, 0])
        if not self.frame_shadows and shadow.get("enabled", True):
            rect = self.shadow.get_rect(center=(round(pos[0]+offset[0]), round(pos[1]+offset[1])))
            surface.blit(self.shadow, rect)
        frame = self.frame()
        registration = self.clip_offsets.get(self.state, (0, 0))
        top_left = (round(pos[0]-frame.get_width()*anchor[0])+registration[0],
                    round(pos[1]-frame.get_height()*anchor[1])+registration[1])
        if self.frame_shadows:
            shadow_origin = tuple(top_left[i]-registration[i] for i in range(2)) if shadow.get("mode") == "contact" else top_left
            self.frame_shadows.draw(surface, self.clips[self.state][0][self.frame_index()], shadow_origin)
        surface.blit(frame, top_left)
