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


_SPRITE_CACHE = {}


class CharacterSprite:
    """Cached RGBA clips sharing a fixed canvas and normalized ground anchor."""
    def __init__(self, assets, spec: dict, accent, enemy=False, beast=False, progress_cb=None, progress_range=(0.0, 1.0)):
        import json
        self.spec = spec
        self.enemy = enemy
        scale = spec.get("scale", 1.0)
        self.size = tuple(max(1, round(v * scale)) for v in spec["size"])
        actor_name = "opponent" if enemy else "character"
        p_min, p_max = progress_range
        p_span = p_max - p_min

        cache_key = (
            spec.get("path", ""),
            self.size,
            tuple(accent) if isinstance(accent, (list, tuple)) else accent,
            enemy,
            beast,
            spec.get("flip_x", False),
            json.dumps(spec.get("animations", {}), sort_keys=True),
            json.dumps(spec.get("lighting", {}), sort_keys=True),
            json.dumps(spec.get("shadow", {}), sort_keys=True),
        )

        if cache_key in _SPRITE_CACHE:
            cached = _SPRITE_CACHE[cache_key]
            self.clips = cached["clips"]
            self.clip_offsets = cached["clip_offsets"]
            self.flashes = cached["flashes"]
            self.shadow = cached["shadow"]
            self.frame_shadows = cached["frame_shadows"]
            if progress_cb:
                progress_cb(p_max, f"{actor_name.capitalize()} ready")
        else:
            fallback = assets.image(spec.get("path", ""), self.size, preserve_aspect=True)
            if fallback is None:
                fallback = placeholder(self.size, accent, enemy, beast)
            else:
                self.size = fallback.get_size()
            self.clips = {"idle": ([fallback], 8, True)}
            anims = spec.get("animations", {})
            total_frames = max(1, sum(len(c.get("frames", [])) for c in anims.values()))
            loaded_count = 0
            base_source = spec.get("source_size", [1920, 1080])
            sx = self.size[0] / base_source[0]
            sy = self.size[1] / base_source[1]
            for name, clip in anims.items():
                frames = []
                clip_source = clip.get("source_size", base_source)
                target_size = (max(1, round(clip_source[0] * sx)), max(1, round(clip_source[1] * sy)))
                for path in clip.get("frames", []):
                    frame = assets.image(path, target_size, preserve_aspect=True)
                    if frame is not None:
                        frames.append(frame)
                    loaded_count += 1
                    if progress_cb and (loaded_count % 6 == 0 or loaded_count == total_frames):
                        frac = p_min + p_span * 0.70 * (loaded_count / total_frames)
                        progress_cb(frac, f"Loading {actor_name} frames ({loaded_count}/{total_frames})...")
                if frames:
                    self.clips[name] = (frames, max(0.1, clip.get("fps", 8)), clip.get("loop", name == "idle"))
            if "hit" in self.clips and "hurt" not in self.clips:
                self.clips["hurt"] = self.clips["hit"]
            if "hit_heavy" in self.clips and "hurt_heavy" not in self.clips:
                self.clips["hurt_heavy"] = self.clips["hit_heavy"]
            if "hurt" in self.clips and "hit" not in self.clips:
                self.clips["hit"] = self.clips["hurt"]
            if "hurt_heavy" in self.clips and "hit_heavy" not in self.clips:
                self.clips["hit_heavy"] = self.clips["hurt_heavy"]
            if "defend" in self.clips and "block" not in self.clips:
                self.clips["block"] = self.clips["defend"]
            if "block" in self.clips and "defend" not in self.clips:
                self.clips["defend"] = self.clips["block"]
            lighting = spec.get("lighting", {})
            if lighting.get("enabled", True) and (lighting.get("ambient") or lighting.get("highlight") or lighting.get("bounce")):
                if progress_cb:
                    progress_cb(p_min + p_span * 0.76, f"Applying lighting to {actor_name}...")
                self.clips = self._apply_lighting(self.clips, lighting)
            # Static clip registration corrects differences in exported canvas origin.
            # It never follows the changing silhouette or adds animated displacement.
            self.clip_offsets = {}
            for name in self.clips:
                config = spec.get("animations", {}).get(name, {})
                offset = config.get("canvas_offset", [0, 0])
                self.clip_offsets[name] = tuple(round(offset[i] * self.size[i] / base_source[i]) for i in range(2))
            self.flashes = {}
            if progress_cb:
                progress_cb(p_min + p_span * 0.86, f"Processing hit reactions for {actor_name}...")
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
            if progress_cb:
                progress_cb(p_min + p_span * 0.94, f"Generating shadows for {actor_name}...")
            self.frame_shadows = FrameShadows([frame for frames, _, _ in self.clips.values() for frame in frames], shadow) if shadow.get("mode") in ("frame", "contact") else None
            _SPRITE_CACHE[cache_key] = {
                "clips": self.clips,
                "clip_offsets": self.clip_offsets,
                "flashes": self.flashes,
                "shadow": self.shadow,
                "frame_shadows": self.frame_shadows,
            }
            if progress_cb:
                progress_cb(p_max, f"{actor_name.capitalize()} ready")
        self.state = "idle"
        self.elapsed = 0.0
        self.hit_time = 0.0
        self.next_state = None
        self.on_state_change = None

    def apply_preview(self, prev):
        import copy
        from src.core.resources import resource
        new_size = tuple(prev.spec["size"])
        size_changed = new_size != tuple(self.size) or prev.spec.get("scale", 1.0) != self.spec.get("scale", 1.0)
        self.spec["position"] = list(prev.spec["position"])
        self.spec["size"] = list(prev.spec["size"])
        if "anchor" in prev.spec:
            self.spec["anchor"] = list(prev.spec["anchor"])
        self.spec["scale"] = prev.spec.get("scale", 1.0)
        self.spec["shadow"] = copy.deepcopy(prev.spec["shadow"])
        if size_changed and getattr(prev, "frames", None):
            self.size = new_size
            by_path = {p.resolve(): frame for p, frame in zip(prev.paths, prev.frames)}
            by_name = {p.name: frame for p, frame in zip(prev.paths, prev.frames)}
            raw_clips = {"idle": ([prev.frames[0]], 8, True)}
            for name, clip in self.spec.get("animations", {}).items():
                frames = []
                for path in clip.get("frames", []):
                    resolved = resource(path).resolve()
                    frame = by_path.get(resolved) or by_name.get(resolved.name)
                    if frame is not None:
                        frames.append(frame)
                if frames:
                    raw_clips[name] = (frames, max(0.1, clip.get("fps", 8)), clip.get("loop", name == "idle"))
            if "hit" in raw_clips and "hurt" not in raw_clips:
                raw_clips["hurt"] = raw_clips["hit"]
            if "hit_heavy" in raw_clips and "hurt_heavy" not in raw_clips:
                raw_clips["hurt_heavy"] = raw_clips["hit_heavy"]
            if "hurt" in raw_clips and "hit" not in raw_clips:
                raw_clips["hit"] = raw_clips["hurt"]
            if "hurt_heavy" in raw_clips and "hit_heavy" not in raw_clips:
                raw_clips["hit_heavy"] = raw_clips["hurt_heavy"]
            if "defend" in raw_clips and "block" not in raw_clips:
                raw_clips["block"] = raw_clips["defend"]
            if "block" in raw_clips and "defend" not in raw_clips:
                raw_clips["defend"] = raw_clips["block"]
            lighting = self.spec.get("lighting", {})
            if lighting.get("enabled", True) and (lighting.get("ambient") or lighting.get("highlight") or lighting.get("bounce")):
                self.clips = self._apply_lighting(raw_clips, lighting)
            else:
                self.clips = raw_clips
            base_source = self.spec.get("source_size", [1920, 1080])
            self.clip_offsets = {}
            for name in self.clips:
                config = self.spec.get("animations", {}).get(name, {})
                offset = config.get("canvas_offset", [0, 0])
                self.clip_offsets[name] = tuple(round(offset[i] * self.size[i] / base_source[i]) for i in range(2))
            self.flashes = {}
            for name, (frames, fps, loop) in self.clips.items():
                tinted = []
                for frame in frames:
                    flash = frame.copy()
                    flash.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)
                    tinted.append(flash)
                self.flashes[name] = tinted
        if self.spec["shadow"].get("mode") in ("frame", "contact"):
            self.frame_shadows = FrameShadows([frame for frames, _, _ in self.clips.values() for frame in frames], self.spec["shadow"])

    def _apply_lighting(self, clips: dict, config: dict) -> dict:
        ambient = config.get("ambient", [255, 255, 255])
        highlight = config.get("highlight", [0, 0, 0])
        bounce = config.get("bounce", [0, 0, 0])
        amb_surfs = {}
        grad_surfs = {}
        new_clips = {}
        for name, (frames, fps, loop) in clips.items():
            lit_frames = []
            for frame in frames:
                fsize = frame.get_size()
                lit = frame.copy()
                if list(ambient) != [255, 255, 255]:
                    if fsize not in amb_surfs:
                        amb = pygame.Surface(fsize)
                        amb.fill(ambient)
                        amb_surfs[fsize] = amb
                    lit.blit(amb_surfs[fsize], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                if any(highlight) or any(bounce):
                    if fsize not in grad_surfs:
                        small = pygame.Surface((1, 64), pygame.SRCALPHA)
                        for y in range(64):
                            sun_f = max(0.0, 1.0 - y / 40.0) ** 1.2
                            bounce_f = max(0.0, (y - 30.0) / 34.0) ** 1.2
                            r = int(min(255, highlight[0] * sun_f + bounce[0] * bounce_f))
                            g = int(min(255, highlight[1] * sun_f + bounce[1] * bounce_f))
                            b = int(min(255, highlight[2] * sun_f + bounce[2] * bounce_f))
                            small.set_at((0, y), (r, g, b, 255))
                        grad_surfs[fsize] = pygame.transform.smoothscale(small, fsize)
                    lit.blit(grad_surfs[fsize], (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                lit_frames.append(lit)
            new_clips[name] = (lit_frames, fps, loop)
        return new_clips

    @property
    def order(self):
        base = self.spec.get("render_order", self.spec["position"][1])
        if self.enemy and self.state in ("attack", "heavy", "special"):
            return max(base, self.spec.get("attack_render_order", 30))
        return base

    @property
    def busy_remaining(self) -> float:
        if self.state == "idle" or self.state not in self.clips:
            return 0.0
        frames, fps, loop = self.clips[self.state]
        if loop:
            return 0.0
        rem = max(0.0, len(frames) / fps - self.elapsed)
        if self.next_state and self.next_state in self.clips:
            n_frames, n_fps, _ = self.clips[self.next_state]
            rem += len(n_frames) / n_fps
        return rem

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
        if state in ("hit", "hit_heavy", "hurt", "hurt_heavy") or state.startswith("hit") or state.startswith("hurt"):
            self.hit_time = 0.20
        clip = state
        if clip not in self.clips:
            if state in ("hit", "hurt"):
                clip = "hit" if "hit" in self.clips else ("hurt" if "hurt" in self.clips else state)
            elif state in ("hit_heavy", "heavy_hit", "hurt_heavy", "heavy_hurt"):
                for candidate in ("hit_heavy", "hurt_heavy", "hit", "hurt"):
                    if candidate in self.clips:
                        clip = candidate
                        break
        if clip in self.clips:
            self.state = clip
            self.elapsed = 0.0
            if self.on_state_change:
                cb = self.on_state_change
                self.on_state_change = None
                cb(clip)

    def update(self, dt: float):
        self.hit_time = max(0.0, self.hit_time - dt)
        self.elapsed += dt
        state = self.state if self.state in self.clips else "idle"
        frames, fps, loop = self.clips[state]
        if not loop and self.elapsed >= len(frames) / fps:
            if self.next_state:
                nxt = self.next_state
                self.next_state = None
                self.trigger(nxt)
            else:
                self.state = "idle"
                self.elapsed = 0.0

    def frame_index(self):
        state = self.state if self.state in self.clips else "idle"
        frames, fps, loop = self.clips[state]
        index = int(self.elapsed * fps)
        index = index % len(frames) if loop else min(index, len(frames)-1)
        return index

    def frame(self):
        state = self.state if self.state in self.clips else "idle"
        index = self.frame_index()
        return self.flashes[state][index] if self.hit_time > 0 and state in self.flashes else self.clips[state][0][index]

    def draw(self, surface, displacement=(0,0)):

        pos = [self.spec["position"][i]+displacement[i] for i in range(2)]
        anchor = self.spec.get("anchor", [0.5, 1.0])
        shadow = self.spec.get("shadow", {})
        offset = shadow.get("offset", [0, 0])
        if not self.frame_shadows and shadow.get("enabled", True):
            rect = self.shadow.get_rect(center=(round(pos[0]+offset[0]), round(pos[1]+offset[1])))
            surface.blit(self.shadow, rect)
        frame = self.frame()
        state = self.state if self.state in self.clips else "idle"
        registration = self.clip_offsets.get(state, (0, 0))
        top_left = (round(pos[0]-frame.get_width()*anchor[0])+registration[0],
                    round(pos[1]-frame.get_height()*anchor[1])+registration[1])
        if self.frame_shadows:
            shadow_origin = tuple(top_left[i]-registration[i] for i in range(2)) if shadow.get("mode") == "contact" else top_left
            self.frame_shadows.draw(surface, self.clips[state][0][self.frame_index()], shadow_origin)
        surface.blit(frame, top_left)
