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
    def __init__(self, original, stage_id, folder=None):
        self.original = original
        self.spec = copy.deepcopy(original.spec)
        self.spec["anchor"] = [0.5, 1.0]
        self.stage_id = stage_id
        self.paths = sorted((folder or resource("assets/test-animation")).glob("*.png"), key=filename_order)
        if not self.paths:
            raise ValueError("No PNG frames in assets/test-animation")
        self.sources = [pygame.image.load(str(path)).convert_alpha() for path in self.paths]
        self.height = round(original.size[1])
        self.frames = []
        self.elapsed = 0.0
        self.playing = False
        self.fps = 12
        self.index = 0
        self.message = "Adjust, then Log values to save a shareable readout."
        self.resize(1)

    @property
    def order(self):
        return self.spec.get("render_order", self.spec["position"][1])

    def resize(self, factor):
        self.height = max(40, min(1600, round(self.height * factor)))
        self.frames = [pygame.transform.smoothscale(frame, (max(1, round(frame.get_width() * self.height / frame.get_height())), self.height)) for frame in self.sources]
        self.spec["size"] = list(self.frames[0].get_size())
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
        # Match the live actor's fixed clip registration, including its shadow.
        clip = "attack" if self.paths[self.index].name.startswith("attack") else "idle"
        config = self.spec.get("animations", {}).get(clip, {})
        offset = config.get("canvas_offset", [0,0]); source = config.get("source_size", frame.get_size())
        top_left = (round(x-frame.get_width()/2+offset[0]*frame.get_width()/source[0]),
                    round(y-frame.get_height()+offset[1]*frame.get_height()/source[1]))
        shadow_origin = (round(x-frame.get_width()/2), round(y-frame.get_height())) if self.spec["shadow"].get("mode") == "contact" else top_left
        self.frame_shadows.draw(surface, frame, shadow_origin)
        surface.blit(frame, top_left)

    def report(self):
        return {"stage_id": self.stage_id, "position": self.spec["position"],
                "size": list(self.frames[self.index].get_size()), "scale": 1.0,
                "anchor": self.spec["anchor"], "fps": self.fps, "shadow": self.spec["shadow"],
                "frame": self.paths[self.index].name,
                "coordinate_space": "1600x900 logical battlefield; bottom-center image anchor",
                "frames": [path.name for path in self.paths]}

    def log(self):
        text = json.dumps(self.report(), indent=2)
        resource("animation-preview.json").write_text(text + "\n", encoding="utf-8")
        print("ANIMATION PREVIEW\n" + text)
        self.message = "Saved animation-preview.json in project root; send that file."

    def panel(self, app, mouse):
        ui, surface = app.ui, app.canvas
        ui.panel(surface, pygame.Rect(530, 115, 790, 400))
        ui.text(surface, "ANIMATION PREVIEW | Combat input disabled", (548, 125), 22)
        x, y = self.spec["position"]
        w, h = self.frames[self.index].get_size()
        ui.text(surface, f"Stage {self.stage_id} | Position ({x}, {y}) | Size {w} x {h} | Anchor bottom-center", (548, 159), 18)
        ui.text(surface, f"{self.index+1}/{len(self.frames)}: {self.paths[self.index].name} | {self.fps} FPS | Space: restart", (548, 185), 18)
        ui.text(surface, "Arrows: move 10 px | Shift+arrow: 1 px | +/-: resize 5%", (548, 211), 18)
        for name, label, rect in [("preview_play", "Play", (548,240,100,38)), ("preview_smaller", "Size -", (658,240,110,38)), ("preview_larger", "Size +", (778,240,110,38)), ("preview_log", "Log values", (898,240,155,38)), ("preview_slower", "FPS -", (1063,240,110,38)), ("preview_faster", "FPS +", (1183,240,110,38))]:
            app.button(name,label,rect,mouse)
        ui.text(surface, self.message, (548,291), 17)

        shadow = self.spec["shadow"]
        ui.text(surface, f"SHADOW {shadow.get('mode','frame')} | opacity {shadow.get('opacity',55)} | depth {shadow.get('depth',.18):.2f} | width {shadow.get('width',1):.2f} | offset {shadow.get('offset',[0,0])}", (548,326),18)
        controls = [("toggle", "On / off"), ("lighter", "Lighter"), ("darker", "Darker"), ("flatter", "Flatter"), ("deeper", "Deeper"), ("narrower", "Narrower"), ("wider", "Wider"), ("left", "Left"), ("right", "Right"), ("up", "Up"), ("down", "Down"), ("counterclockwise", "Rotate CCW"), ("clockwise", "Rotate CW")]
        for i, (name,label) in enumerate(controls):
            app.button("preview_shadow_"+name,label,(548+(i%6)*125,355+(i//6)*48,117,38),mouse)

        ui.text(surface, f"Angle: {shadow.get('angle',0)} degrees | 5 degrees per click", (685,459),18)
