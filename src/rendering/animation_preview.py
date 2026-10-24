"""Temporary actor placement/playback tool; never edits stage or combat data."""
import copy
import json
import re
import pygame
from src.rendering.frame_shadow import FrameShadows
from src.core.resources import resource


def filename_order(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name.lower())]


class AnimationPreview:
    def __init__(self, original, stage_id, folder=None, target="player"):
        self.original = original
        self.target = target
        self.spec = copy.deepcopy(original.spec)
        self.spec["anchor"] = list(original.spec.get("anchor", [0.5, 1.0]))
        self.state = "idle"
        self.stage_id = stage_id
        if folder:
            target_dir = folder
        elif target == "opponent":
            opp_path = original.spec.get("path", "")
            if opp_path:
                p = resource(opp_path).parent
                while p.name in ("idle", "attack", "hurt", "defend"):
                    p = p.parent
                target_dir = p
            else:
                target_dir = resource(f"assets/enemies/enemy_{stage_id:02d}")
        else:
            target_dir = resource("assets/characters/char_01")
        if not target_dir.exists():
            target_dir = resource("assets/test-animation")
        self.paths = sorted(target_dir.glob("**/*.png") if target_dir.is_dir() else [], key=filename_order)
        if not self.paths:
            raise ValueError(f"No PNG frames in {target_dir}")
        self.sources = [pygame.image.load(str(path)).convert_alpha() for path in self.paths]
        if self.spec.get("flip_x", False):
            self.sources = [pygame.transform.flip(s, True, False) for s in self.sources]
        self.base_source = list(self.spec.get("source_size", self.sources[0].get_size()))
        self.base_height = self.base_source[1]
        self.height = round(original.size[1])
        self.frames = []
        self.elapsed = 0.0
        self.playing = False
        self.fps = 12
        self.index = 0
        self.message = "Auto-saves character & enemy properties to stages.json on F6 close / Tab switch."
        self.resize(1)

    def frame_index(self):
        return self.index

    @property
    def order(self):
        base = self.spec.get("render_order", self.spec["position"][1])
        if self.target == "opponent" and self.paths[self.index].name.lower().startswith("attack"):
            return max(base, self.spec.get("attack_render_order", 30))
        return base

    def resize(self, factor):
        self.height = max(40, min(1600, round(self.height * factor)))
        scale = self.height / self.base_height
        self.frames = [pygame.transform.smoothscale(frame, (max(1, round(frame.get_width() * scale)), max(1, round(frame.get_height() * scale)))) for frame in self.sources]
        self.spec["size"] = [max(1, round(self.base_source[0] * scale)), max(1, round(self.base_source[1] * scale))]
        self.spec["scale"] = 1.0
        self.rebuild_shadows()

    def rebuild_shadows(self):
        self.frame_shadows = FrameShadows(self.frames, self.spec.setdefault("shadow", {}))

    def shadow_adjust(self, name):
        config = self.spec["shadow"]
        if name == "toggle": config["enabled"] = not config.get("enabled", True)
        elif name in ("clockwise", "counterclockwise"):
            config["angle"] = (config.get("angle", 0)+(5 if name == "counterclockwise" else -5)+180)%360-180
            self.rebuild_shadows()
        elif name in ("darker", "lighter"):
            config["opacity"] = max(0, min(150, config.get("opacity",55)+(5 if name == "darker" else -5)))
        elif name in ("deeper", "flatter"):
            config["depth"] = round(max(.04, min(.6, config.get("depth",.18)+(.02 if name == "deeper" else -.02))),2)
            self.rebuild_shadows()
        elif name in ("wider", "narrower"):
            config["width"] = round(max(.4, min(2, config.get("width",1)+(.05 if name == "wider" else -.05))),2)
            self.rebuild_shadows()
        else:
            dx, dy = {"left":(-3,0), "right":(3,0), "up":(0,-3), "down":(0,3)}[name]
            offset = config.setdefault("offset", [0,0])
            offset[0] += dx; offset[1] += dy

    def trigger(self, state):
        pass

    def play(self):
        self.elapsed = 0.0
        self.index = 0
        self.playing = True

    def step(self, delta):
        self.playing = False
        self.index = (self.index + delta) % len(self.frames)
        self.elapsed = self.index / self.fps

    def update(self, dt):
        if self.playing:
            self.elapsed += dt
            self.index = min(len(self.frames)-1, int(self.elapsed * self.fps))
            if self.elapsed >= len(self.frames) / self.fps:
                self.playing = False

    def move(self, x, y):
        self.spec["position"][0] += x
        self.spec["position"][1] += y

    def key(self, key, mods=0):
        step = 1 if mods & pygame.KMOD_SHIFT else 10
        directions = {pygame.K_LEFT: (-step, 0), pygame.K_RIGHT: (step, 0), pygame.K_UP: (0, -step), pygame.K_DOWN: (0, step)}
        if key in directions:
            self.move(*directions[key])
        elif key == pygame.K_SPACE:
            self.play()
        elif key in (pygame.K_LEFTBRACKET, pygame.K_COMMA):
            self.step(-1)
        elif key in (pygame.K_RIGHTBRACKET, pygame.K_PERIOD):
            self.step(1)
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.resize(1.05)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.resize(1/1.05)
        else:
            return False
        return True

    def draw(self, surface, displacement=(0, 0)):
        frame = self.frames[self.index]
        x, y = (self.spec["position"][i] + displacement[i] for i in range(2))
        fname = self.paths[self.index].name.lower()
        if "attack" in fname or "heavy" in fname or "light" in fname:
            clip = "heavy" if "heavy" in fname else ("special" if "light" in fname else "attack")
        elif "hurt" in fname or "hit" in fname:
            clip = "hit_heavy" if "heavy" in fname else ("hit" if "hit" in self.spec.get("animations", {}) else "hurt")
        elif "defend" in fname or "block" in fname or "charge" in fname:
            clip = "defend" if "defend" in self.spec.get("animations", {}) else "block"
        elif "heal" in fname:
            clip = "heal"
        else:
            clip = "idle"
        config = self.spec.get("animations", {}).get(clip, {})
        offset = config.get("canvas_offset", [0, 0])
        scale = self.height / self.base_height
        anchor = self.spec.get("anchor", [0.5, 1.0])
        top_left = (round(x - frame.get_width() * anchor[0] + offset[0] * scale),
                    round(y - frame.get_height() * anchor[1] + offset[1] * scale))
        shadow_origin = (round(x - frame.get_width() * anchor[0]), round(y - frame.get_height() * anchor[1])) if self.spec["shadow"].get("mode") == "contact" else top_left
        self.frame_shadows.draw(surface, frame, shadow_origin)
        surface.blit(frame, top_left)

    def report(self):
        return {
            "stage_id": self.stage_id,
            "target": self.target,
            "position": self.spec["position"],
            "size": list(self.frames[self.index].get_size()),
            "scale": 1.0,
            "anchor": self.spec["anchor"],
            "fps": self.fps,
            "shadow": self.spec["shadow"],
            "frame": self.paths[self.index].name,
            "coordinate_space": "1600x900 logical battlefield; bottom-center image anchor",
            "frames": [path.name for path in self.paths]
        }

    def log(self):
        text = json.dumps(self.report(), indent=2)
        resource("animation-preview.json").write_text(text + "\n", encoding="utf-8")
        print("ANIMATION PREVIEW\n" + text)
        self.message = "Saved animation-preview.json in project root; send that file."

    def panel(self, app, mouse):
        ui, surface = app.ui, app.canvas
        px, py, pw, ph = 405, 10, 790, 246
        ui.panel(surface, pygame.Rect(px, py, pw, ph))
        target_title = "PLAYER" if self.target == "player" else "ENEMY"
        ui.text(surface, f"ANIMATION PREVIEW | Target: {target_title} (Tab to switch)", (px + 18, py + 10), 20)
        x, y = self.spec["position"]
        w, h = self.frames[self.index].get_size()
        ui.text(surface, f"Stage {self.stage_id} | Pos ({x}, {y}) | Size {w}x{h} | {self.index+1}/{len(self.frames)}: {self.paths[self.index].name} ({self.fps} FPS)", (px + 18, py + 36), 16)
        ui.text(surface, "Arrows: move 10px (Shift: 1px) | +/-: resize 5% | Space: play | [, ]: step frame", (px + 18, py + 58), 15)
        target_btn = "Enemy (Tab)" if self.target == "player" else "Player (Tab)"
        for name, label, rect in [
            ("preview_play", "Play", (px + 18, py + 82, 75, 32)),
            ("preview_step_back", "<", (px + 98, py + 82, 36, 32)),
            ("preview_step_forward", ">", (px + 138, py + 82, 36, 32)),
            ("preview_switch_target", target_btn, (px + 180, py + 82, 130, 32)),
            ("preview_smaller", "Size -", (px + 316, py + 82, 80, 32)),
            ("preview_larger", "Size +", (px + 402, py + 82, 80, 32)),
            ("preview_log", "Log values", (px + 488, py + 82, 120, 32)),
            ("preview_slower", "FPS -", (px + 614, py + 82, 75, 32)),
            ("preview_faster", "FPS +", (px + 695, py + 82, 75, 32)),
        ]:
            app.button(name, label, rect, mouse)
        ui.text(surface, self.message, (px + 18, py + 120), 15)

        shadow = self.spec["shadow"]
        ui.text(
            surface,
            f"SHADOW {shadow.get('mode','frame')} | opacity {shadow.get('opacity',55)} | depth {shadow.get('depth',.18):.2f} | width {shadow.get('width',1):.2f} | offset {shadow.get('offset',[0,0])} | angle {shadow.get('angle',0)} deg",
            (px + 18, py + 144),
            16,
        )
        controls = [
            ("toggle", "On / off"), ("lighter", "Lighter"), ("darker", "Darker"),
            ("flatter", "Flatter"), ("deeper", "Deeper"), ("narrower", "Narrower"), ("wider", "Wider"),
            ("left", "Left"), ("right", "Right"), ("up", "Up"), ("down", "Down"),
            ("counterclockwise", "Rot CCW"), ("clockwise", "Rot CW"),
        ]
        for i, (name, label) in enumerate(controls):
            app.button("preview_shadow_" + name, label, (px + 18 + (i % 7) * 108, py + 168 + (i // 7) * 36, 102, 31), mouse)
