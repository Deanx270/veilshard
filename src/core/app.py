import copy
import json
import os
import pygame
from src.core.resources import resource
from src.core.input import SIZE, logical_mouse, viewport
from src.scenes.campaign import Campaign
from src.rendering.assets import Assets
from src.rendering.battlefield import Battlefield
from src.rendering.effects import Effects
from src.ui.widgets import UI, INK, MUTED
from src.ui.card_hand import CardHand
from src.rendering.action_timeline import ActionTimeline
from src.ui.battle_hud import BattleHUD
from src.rendering.animation_preview import AnimationPreview

class App:
    def __init__(self, start_stage: int = 1):
        pygame.init()
        self.window=pygame.display.set_mode((1280,720),pygame.RESIZABLE)
        self.canvas=pygame.Surface(SIZE)
        self.campaign=Campaign()
        if start_stage > 1:
            self.campaign.start()
            self.campaign.cleared_stages = set(range(start_stage - 1))
            self.campaign.index = min(len(self.campaign.stages) - 1, max(0, start_stage - 1))
            self.campaign.enter_battle()
        pygame.display.set_caption(self.campaign.story["title"])
        self.assets=Assets()
        self.ui=UI()
        self.hand=CardHand(self.ui)
        self.hud=BattleHUD(self.ui)
        self.end_pressed=0.0
        self.enemy_turn_in_progress=False
        self.timeline=ActionTimeline()
        self.pending_card=None
        self.preview=None
        self.preview_cache={}
        self.preview_target="player"
        self.preview_error=""
        self.effects=Effects()
        self.clock=pygame.time.Clock()
        self.running=True
        self.paused=False
        self.time=0.0
        self.lock=0.0
        self.fade=0.0
        self.last_scene=self.campaign.scene
        self.loaded_stage=None
        self.buttons={}
        self.draw_loading(0.01, "Initializing...")
        self.load_stage(progress_cb=self.draw_loading)

    def draw_loading(self, progress: float, status_text: str = ""):
        if os.environ.get("SDL_VIDEODRIVER") == "dummy":
            return
        s = self.canvas
        ui = self.ui
        c = self.campaign
        accent = c.stage.get("accent", (238, 132, 90))

        for event in pygame.event.get(pygame.QUIT):
            self.running = False
            return

        s.fill((10, 14, 26))
        ui.panel(s, pygame.Rect(390, 240, 820, 420), (17, 24, 43), (65, 76, 108), 24)

        subtitle = c.story.get("subtitle", "RESONANCE OF THE WEAVER").upper()
        ui.text(s, subtitle, (800, 290), 18, accent, True)
        ui.text(s, c.story.get("title", "VEILSHARD"), (800, 350), 54, INK, True)

        stage_name = c.stage.get("name", "Ember Forest")
        info = f"Chapter {c.index+1:02} : {stage_name}"
        ui.text(s, info, (800, 420), 22, MUTED, True)

        bar_x, bar_y, bar_w, bar_h = 500, 475, 600, 18
        pygame.draw.rect(s, (13, 17, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        pygame.draw.rect(s, (45, 55, 80), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=9)

        pct = max(0.0, min(1.0, progress))
        fill_w = max(0, min(bar_w, round(bar_w * pct)))
        if fill_w > 0:
            pygame.draw.rect(s, accent, (bar_x, bar_y, fill_w, bar_h), border_radius=9)
            if fill_w > 8:
                hl = pygame.Rect(bar_x + 4, bar_y + 3, fill_w - 8, max(2, bar_h // 4))
                pygame.draw.rect(s, (255, 255, 255, 110), hl, border_radius=4)

        pct_text = f"{int(pct * 100)}%"
        detail = f"{status_text}  ({pct_text})" if status_text else f"Loading assets...  ({pct_text})"
        ui.text(s, detail, (800, 525), 18, (160, 175, 205), True)
        ui.text(s, "VEILSHARD  /  PROTOTYPE 01", (40, 850), 17, MUTED)

        self.window.fill((5, 7, 13))
        area = viewport(self.window.get_size())
        self.window.blit(pygame.transform.smoothscale(s, area.size), area)
        pygame.display.flip()

    def load_stage(self, progress_cb=None):
        stage=self.campaign.stage
        if self.loaded_stage==stage["id"]: return
        self.close_preview()
        self.loaded_stage=stage["id"]
        cb = progress_cb if progress_cb is not None else getattr(self, "draw_loading", None)
        self.battlefield=Battlefield(self.assets,stage,progress_cb=cb)
        self.background=self.battlefield.background

    def change_feedback(self):
        if self.campaign.scene!=self.last_scene:
            self.last_scene=self.campaign.scene
            self.fade=0.28
        self.load_stage()

    def save_preview_properties(self):
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        stage_id = self.campaign.stage["id"]
        stages_path = resource("data/stages.json")
        try:
            with open(stages_path, "r", encoding="utf-8") as f:
                stages = json.load(f)

            target_stage = None
            for s in stages:
                if s.get("id") == stage_id:
                    target_stage = s
                    break
            if not target_stage:
                return

            saved_targets = []
            for key, prev in list(self.preview_cache.items()):
                if isinstance(key, tuple) and len(key) == 2:
                    s_id, target = key
                else:
                    s_id = key
                    target = "player"
                if s_id == stage_id and target in target_stage:
                    target_stage[target]["position"] = list(prev.spec["position"])
                    target_stage[target]["size"] = list(prev.spec["size"])
                    target_stage[target]["anchor"] = list(prev.spec.get("anchor", target_stage[target].get("anchor", [0.5, 1.0])))
                    target_stage[target]["scale"] = prev.spec.get("scale", 1.0)
                    target_stage[target]["shadow"] = copy.deepcopy(prev.spec["shadow"])
                    self.campaign.stage[target]["position"] = list(prev.spec["position"])
                    self.campaign.stage[target]["anchor"] = list(prev.spec.get("anchor", self.campaign.stage[target].get("anchor", [0.5, 1.0])))
                    self.campaign.stage[target]["size"] = list(prev.spec["size"])
                    self.campaign.stage[target]["scale"] = prev.spec.get("scale", 1.0)
                    self.campaign.stage[target]["shadow"] = copy.deepcopy(prev.spec["shadow"])
                    if hasattr(self, "battlefield") and target in self.battlefield.actors:
                        actor = self.battlefield.actors[target]
                        actual_actor = getattr(actor, "original", actor)
                        if hasattr(actual_actor, "apply_preview"):
                            actual_actor.apply_preview(prev)
                        else:
                            actual_actor.spec["position"] = list(prev.spec["position"])
                            actual_actor.spec["anchor"] = list(prev.spec.get("anchor", actual_actor.spec.get("anchor", [0.5, 1.0])))
                            actual_actor.spec["size"] = list(prev.spec["size"])
                            actual_actor.spec["scale"] = prev.spec.get("scale", 1.0)
                            actual_actor.spec["shadow"] = copy.deepcopy(prev.spec["shadow"])
                            if hasattr(actual_actor, "clips") and prev.spec["shadow"].get("enabled", True) and prev.spec["shadow"].get("mode") in ("frame", "contact"):
                                from src.rendering.frame_shadow import FrameShadows
                                actual_actor.frame_shadows = FrameShadows([frame for frames, _, _ in actual_actor.clips.values() for frame in frames], actual_actor.spec["shadow"])
                            elif not prev.spec["shadow"].get("enabled", True):
                                actual_actor.frame_shadows = None
                    saved_targets.append(target)

            with open(stages_path, "w", encoding="utf-8") as f:
                json.dump(stages, f, indent=2)
                f.write("\n")
            if saved_targets:
                print(f"[AUTO-SAVE] Successfully saved {saved_targets} for Stage {stage_id} to data/stages.json")
        except Exception as e:
            print(f"[AUTO-SAVE ERROR] Could not save stage properties: {e}")

    def close_preview(self):
        if self.preview is not None:
            self.save_preview_properties()
            self.battlefield.actors[self.preview_target] = self.preview.original
            self.preview = None

    def open_preview(self, target="player"):
        stage_id = self.campaign.stage["id"]
        self.preview_target = target
        try:
            cache_key = (stage_id, target)
            if cache_key in self.preview_cache:
                self.preview = self.preview_cache[cache_key]
            elif target == "player" and stage_id in self.preview_cache:
                self.preview = self.preview_cache[stage_id]
            else:
                self.preview = AnimationPreview(self.battlefield.actors[target], stage_id, target=target)
                self.preview_cache[cache_key] = self.preview
            self.preview.original = self.battlefield.actors[target]
            self.battlefield.actors[target] = self.preview
            self.preview_error = ""
        except (ValueError, pygame.error, OSError) as error:
            self.preview_error = str(error)

    def switch_preview_target(self, new_target):
        if not self.preview or new_target == self.preview_target:
            return
        self.close_preview()
        self.open_preview(new_target)

    def preview_action(self, name):
        if self.paused or self.lock or self.campaign.scene != "battle": return
        if name == "preview_toggle":
            if self.preview:
                self.close_preview()
            elif self.campaign.stage.get("debug", False):
                self.open_preview(self.preview_target)
        elif name == "preview_switch_target":
            if self.preview:
                new_target = "opponent" if self.preview_target == "player" else "player"
                self.switch_preview_target(new_target)
        elif self.preview:
            if name.startswith("preview_shadow_"): self.preview.shadow_adjust(name.removeprefix("preview_shadow_"))
            elif name == "preview_play": self.preview.play()
            elif name == "preview_step_back": self.preview.step(-1)
            elif name == "preview_step_forward": self.preview.step(1)
            elif name == "preview_switch_target":
                new_target = "opponent" if self.preview_target == "player" else "player"
                self.switch_preview_target(new_target)
            elif name == "preview_smaller": self.preview.resize(1/1.05)
            elif name == "preview_larger": self.preview.resize(1.05)
            elif name == "preview_log":
                self.preview.log()
                self.save_preview_properties()
            elif name == "preview_slower": self.preview.fps = max(1, self.preview.fps-1)
            elif name == "preview_faster": self.preview.fps = min(60, self.preview.fps+1)

    def actors_busy_time(self):
        return max((getattr(a, "busy_remaining", 0.0) for a in self.battlefield.actors.values()), default=0.0)

    def action(self,name):
        if name.startswith("preview_"):
            self.preview_action(name)
            return
        if name.startswith("buy_"):
            self.campaign.buy(name.removeprefix("buy_"))
            return
        if name == "menu": self.close_preview()
        c=self.campaign
        if name=="start": c.start()
        elif name=="battle":
            c.enter_battle()
            self.effects=Effects()
            self.timeline.cancel()
            self.pending_card=None
            self.lock=0
            self.hud.reset(c.battle)
            self.hand=CardHand(self.ui)
            for actor in self.battlefield.actors.values():
                actor.state="idle"
                actor.elapsed=0.0
                actor.hit_time=0.0
            if hasattr(self.battlefield.camera, "reset"):
                self.battlefield.camera.reset()
            self.battlefield.reactions.clear()
            self.battlefield.motion=None
        elif name=="next":
            self.enemy_turn_in_progress=False
            c.advance()
        elif name=="retry":
            self.enemy_turn_in_progress=False
            c.retry()
        elif name=="retry_prev":
            self.enemy_turn_in_progress=False
            c.retry_previous()
        elif name=="menu":
            c.scene="menu"; self.paused=False
            self.timeline.cancel(); self.pending_card=None; self.lock=0
            self.enemy_turn_in_progress=False
            for actor in self.battlefield.actors.values():
                actor.state="idle"; actor.elapsed=0.0
        elif name=="quit": self.running=False
        elif name=="resume": self.paused=False
        elif name=="pause": self.paused=True
        elif name=="end" and c.scene=="battle" and c.battle.status=="active" and not self.lock and not self.paused and not self.preview:
            self.end_pressed=0.16
            self.enemy_turn_in_progress=True
            kind=c.battle.intent.kind
            self.begin_action(kind,"opponent",c.battle.end_turn)
        self.change_feedback()

    def event(self,event):
        if event.type==pygame.QUIT: self.running=False
        if event.type==pygame.KEYDOWN and self.campaign.scene=="battle" and not self.paused:
            if event.key == pygame.K_F6:
                if self.campaign.stage.get("debug", False) or self.preview:
                    self.preview_action("preview_toggle")
                    return
            if self.preview:
                if event.key in (pygame.K_TAB, pygame.K_t):
                    self.preview_action("preview_switch_target")
                    return
                if self.preview.key(event.key, getattr(event, "mod", 0)):
                    return
        if event.type==pygame.KEYDOWN and self.campaign.scene=="battle" and not self.paused and self.battlefield.parallax:
            if self.battlefield.camera.debug_key(event.key): return
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            if self.campaign.scene=="battle": self.paused=not self.paused
            else: self.action("menu")
            return
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mouse=logical_mouse(event.pos,self.window.get_size())
            for name,rect in self.buttons.items():
                if rect.collidepoint(mouse):
                    if not self.lock or self.paused or name=="pause": self.action(name)
                    return
            if self.campaign.scene=="battle" and not self.paused and not self.lock and not self.preview:
                i=self.hand.hit(mouse)
                if i is not None:
                    card=self.campaign.battle.deck.hand[i]
                    if card.cost<=self.campaign.battle.energy and self.campaign.battle.status=="active":
                        self.pending_card=i
                        self.hand.remove(i)
                        self.begin_action(card.id if card.category=="attack" else card.category,"player",lambda: self.campaign.battle.play(i))

    def begin_action(self,kind,source,resolve):
        actor = self.battlefield.actors[source]
        def impact():
            effects=resolve()
            self.pending_card=None
            damage_and_other = [e for e in effects if not (e.kind == "block" and e.target == "enemy" and source == "opponent" and kind in ("attack", "heavy", "special"))]
            block_after = [e for e in effects if e.kind == "block" and e.target == "enemy" and source == "opponent" and kind in ("attack", "heavy", "special")]
            self.effects.add(damage_and_other,self.campaign.stage,kind,source)
            self.battlefield.feedback(effects,source,kind)
            if block_after and "defend" in actor.clips:
                actor.next_state = "defend"
                actor.on_state_change = lambda new_state: self.effects.add(block_after, self.campaign.stage, "defend", source)
            elif block_after:
                self.effects.add(block_after, self.campaign.stage, "defend", source)
        if kind == "special" and "special" in actor.clips:
            clip = "special"
        elif kind == "heavy" and "heavy" in actor.clips:
            clip = "heavy"
        elif kind in ("heavy", "special"):
            clip = "heavy" if "heavy" in actor.clips else "attack"
        elif kind == "block":
            clip = "defend"
        else:
            clip = kind
        if self.timeline.start(kind, source, impact, actor.action_timing(clip)):
            actor.trigger(clip)
            self.lock=max(self.timeline.remaining, self.actors_busy_time())

    def visible_hand(self):
        if getattr(self, "enemy_turn_in_progress", False):
            return []
        cards=list(self.campaign.battle.deck.hand)
        if self.pending_card is not None: cards.pop(self.pending_card)
        return cards

    def update(self,dt):
        if self.preview and not self.paused:
            self.preview.update(dt)
        if not self.paused and not self.preview:
            self.time+=dt
            self.effects.update(dt)
            self.battlefield.update(dt)
            self.timeline.update(dt)
            self.lock=max(self.timeline.remaining, self.actors_busy_time() if self.campaign.scene=="battle" else 0.0)
            if getattr(self, "enemy_turn_in_progress", False):
                opp = self.battlefield.actors.get("opponent")
                enemy_busy = getattr(opp, "busy_remaining", 0.0) if opp else 0.0
                if not self.timeline.active and enemy_busy == 0:
                    self.enemy_turn_in_progress = False
            self.battlefield.motion=self.timeline
            if self.campaign.scene=="battle": self.hud.update(dt,self.campaign.battle)
            self.end_pressed=max(0,self.end_pressed-dt)
            if self.campaign.scene=="battle":
                self.hand.sync(self.visible_hand())
                mouse=logical_mouse(pygame.mouse.get_pos(),self.window.get_size())
                self.hand.update(dt,mouse,not self.lock)
            if not self.lock: self.campaign.resolve()
        self.fade=max(0,self.fade-dt)
        self.change_feedback()

    def button(self,name,label,rect,mouse,enabled=True,accent=None):
        rect=pygame.Rect(rect)
        if enabled: self.buttons[name]=rect
        use_accent = accent if accent is not None else self.campaign.stage["accent"]
        self.ui.button(self.canvas,rect,label,mouse,use_accent,enabled)

    def draw(self):
        c=self.campaign; s=self.canvas; ui=self.ui
        mouse=logical_mouse(pygame.mouse.get_pos(),self.window.get_size())
        self.buttons={}
        if c.scene=="battle":
            self.draw_battle(mouse)
        elif c.scene=="shop":
            self.draw_shop(mouse)
        else:
            self.background.draw(s,self.time)
            self.background.draw(s,self.time,True)
            ui.panel(s,pygame.Rect(390,195,820,530),(17,24,43),(65,76,108),24)
            ui.text(s,c.story.get("subtitle", "").upper(),(800,245),18,c.stage["accent"],True)
            if c.scene=="menu":
                title=c.story["title"]; body=c.story["opening"]
                button=("start","Begin journey")
                ui.text(s,c.story.get("subtitle",""),(800,370),25,MUTED,True)
            elif c.scene=="intro":
                title=c.stage["name"]; body=c.story["introductions"][c.index]
                button=("battle","Enter battle")
                ui.text(s,f"CHAPTER {c.index+1:02} / {len(c.stages):02}",(800,370),22,MUTED,True)
            elif c.scene=="clear":
                title="Fragment recovered"; body=f"{c.stage['enemy']['name']} falls quiet. Another echo calls from beyond this place."
                button=("next","Follow the echo")
            elif c.scene=="over":
                title="The light fades"; body="Your journey is not over. Return to this stage with a fresh deck and full health."
                button=("retry","Retry stage")
            else:
                title="A fractured dawn"; body=c.story["ending"]
                button=("start","Play again")
            ui.text(s,title,(800,320),54,INK,True)
            ui.wrap(s,body,pygame.Rect(490,425,620,140),27)
            self.button(*button,(620,585,360,62),mouse)
            if c.scene=="menu": self.button("quit","Exit",(700,665,200,42),mouse)
            else: self.button("menu","Main menu",(700,665,200,42),mouse)
            ui.text(s,"VEILSHARD  /  PROTOTYPE 01",(40,850),17,MUTED)
        if self.paused:
            shade=pygame.Surface(SIZE,pygame.SRCALPHA); shade.fill((5,9,21,210)); s.blit(shade,(0,0))
            self.buttons={}
            ui.panel(s,pygame.Rect(550,275,500,350))
            ui.text(s,"Paused",(800,335),46,INK,True)
            self.button("resume","Resume",(650,410,300,60),mouse)
            self.button("menu","Main menu",(650,500,300,60),mouse)
        if self.fade:
            shade=pygame.Surface(SIZE); shade.fill((9,13,25)); shade.set_alpha(int(255*self.fade/0.28)); s.blit(shade,(0,0))
        self.window.fill((5,7,13))
        area=viewport(self.window.get_size())
        self.window.blit(pygame.transform.smoothscale(s,area.size),area)
        pygame.display.flip()

    def draw_shop(self, mouse):
        c = self.campaign; s = self.canvas; ui = self.ui
        self.background.draw(s, self.time)
        self.background.draw(s, self.time, True)

        dim = pygame.Surface((1600, 900), pygame.SRCALPHA)
        dim.fill((6, 9, 18, 195))
        s.blit(dim, (0, 0))

        panel_rect = pygame.Rect(150, 45, 1300, 810)
        ui.panel(s, panel_rect, (15, 20, 36), (60, 75, 110), 20)

        ui.text(s, "THE VEIL BAZAAR", (800, 88), 36, (244, 233, 212), True)

        res = c.last_battle_result
        if res:
            banner_rect = pygame.Rect(200, 130, 1200, 44)
            half_note = "   (Half Reward)" if res.get("half_reward") else ""
            if res.get("won"):
                bg_color = (22, 52, 36)
                border_color = (65, 150, 95)
                msg = f"STAGE CLEARED: {res['stage_name']}   |   Claimed +{res['earned']} Veil Shards{half_note}"
                text_color = (165, 245, 190)
            else:
                bg_color = (52, 25, 30)
                border_color = (150, 65, 75)
                msg = f"DEFEATED: Dealt {res['damage_dealt']}/{res['enemy_max_hp']} damage to {res['enemy_name']}   |   Gained +{res['earned']} Veil Shards{half_note}"
                text_color = (245, 175, 180)
            ui.panel(s, banner_rect, bg_color, border_color, 10)
            ui.text(s, msg, banner_rect.center, 18, text_color, True)

        balance_rect = pygame.Rect(1170, 70, 230, 46)
        ui.panel(s, balance_rect, (25, 32, 50), (225, 190, 110), 10)
        ui.text(s, f"Shards: {c.shards}", balance_rect.center, 22, (248, 220, 135), True)

        item_keys = ["hp", "attack", "shield", "heavy", "heal", "energy"]
        grid_x = 200
        grid_y = 195
        card_w = 380
        card_h = 250
        gap_x = 30
        gap_y = 20

        from src.scenes.campaign import SHOP_CATALOG
        for idx, key in enumerate(item_keys):
            col = idx % 3
            row = idx // 3
            bx = grid_x + col * (card_w + gap_x)
            by = grid_y + row * (card_h + gap_y)
            rect = pygame.Rect(bx, by, card_w, card_h)

            cat = SHOP_CATALOG[key]
            lvl = c.upgrades.get(key, 0)
            max_lvl = cat["max_level"]
            cost = c.item_cost(key)
            can_afford = c.can_buy(key)
            is_maxed = lvl >= max_lvl

            accent = {
                "hp": (230, 95, 95),
                "attack": (238, 132, 90),
                "shield": (112, 203, 236),
                "heavy": (198, 145, 232),
                "heal": (136, 246, 192),
                "energy": (245, 215, 120),
            }.get(key, (180, 190, 210))

            ui.panel(s, rect, (20, 27, 46), tuple(int(x * 0.7) for x in accent), 14)
            pygame.draw.rect(s, accent, (bx + 2, by + 2, card_w - 4, 4), border_top_left_radius=12, border_top_right_radius=12)

            ui.text(s, cat["name"], (bx + 16, by + 18), 20, (244, 233, 212))

            lvl_text = "MAX" if is_maxed else (f"Level {lvl}/{max_lvl}" if max_lvl > 1 else ("Active" if lvl > 0 else "Locked"))
            lw = ui.font(15).size(lvl_text)[0]
            ui.text(s, lvl_text, (bx + card_w - 18 - lw, by + 20), 15, accent)

            if key == "hp":
                cur_val = f"Current Max HP: {c.player_max_hp()}"
            elif key == "attack":
                cur_val = f"Current Damage: {6 + lvl * 2}"
            elif key == "shield":
                cur_val = f"Current Block: {6 + lvl * 2}"
            elif key == "heavy":
                cur_val = f"Current Damage: {10 + lvl * 3}"
            elif key == "heal":
                cur_val = f"Current Healing: {6 + lvl * 2}"
            elif key == "energy":
                cur_val = "Turn 1 starts with 3 Energy" if lvl > 0 else "Turn 1 starts with 2 Energy"

            ui.text(s, cat["desc"], (bx + 16, by + 60), 16, (200, 210, 225))
            ui.text(s, cur_val, (bx + 16, by + 90), 15, (148, 160, 188))

            btn_rect = pygame.Rect(bx + 20, by + card_h - 58, card_w - 40, 42)
            btn_id = f"buy_{key}"
            if is_maxed:
                ui.panel(s, btn_rect, (28, 34, 48), (48, 56, 74), 8)
                ui.text(s, "MAX LEVEL", btn_rect.center, 16, (120, 130, 150), True)
            else:
                self.button(btn_id, f"Enhance  ({cost})", btn_rect, mouse, enabled=can_afford, accent=accent)

        if res and res.get("won"):
            cont_label = "Continue Journey"
            cont_action = "next"
        else:
            cont_label = f"Retry Stage {c.index + 1}"
            cont_action = "retry"

        if c.index > 0:
            self.button("retry_prev", f"Retry Stage {c.index}", (380, 761, 210, 42), mouse)
        self.button(cont_action, cont_label, (630, 755, 340, 54), mouse, accent=c.stage["accent"])
        self.button("menu", "Main Menu", (1010, 761, 180, 42), mouse)

    def draw_battle(self,mouse):
        c=self.campaign; b=c.battle
        self.battlefield.draw(self.canvas,self.time,self.effects,self.ui.font(34))
        enabled=not self.lock and b.status=="active" and not self.paused and not self.preview
        self.hud.draw(self.canvas,c,mouse,enabled,self.end_pressed>0)
        self.buttons["pause"]=self.hud.pause
        if enabled: self.buttons["end"]=self.hud.end
        self.hand.sync(self.visible_hand())
        if not self.preview:
            self.hand.draw(self.canvas,b.energy)
        if self.battlefield.parallax and self.battlefield.camera.debug:
            from src.ui.battle_hud import glass
            camera=self.battlefield.camera
            glass(self.canvas,(425,17,870,86),210)
            self.ui.text(self.canvas,"PARALLAX DEBUG  |  F1 hide  F2 parallax  F3 master  F4 shake  F5 zoom",(440,24),18)
            mode="MASTER" if self.background.compare else "LAYERS"
            self.ui.text(self.canvas,f"{mode}  parallax={self.background.enabled}  pan=({camera.pan[0]:.1f}, {camera.pan[1]:.1f})  zoom={camera.zoom:.3f}",(440,49),17)
            self.ui.text(self.canvas,"Arrows: pan to limits   Home: reset view   (source-pixel units)",(440,73),16)
        if self.preview: self.preview.panel(self, mouse)
        if self.campaign.stage.get("debug", False) or self.preview:
            self.button("preview_toggle", "Close preview (F6)" if self.preview else "Test animation (F6)", (965, 16, 215, 30) if self.preview else (675, 22, 250, 40), mouse, not self.lock)
        if self.preview_error and (self.campaign.stage.get("debug", False) or self.preview): self.ui.text(self.canvas, self.preview_error[:110], (530, 70), 17)
        if not self.preview and not b.deck.hand and b.status == "active" and b.player.hp > 0 and not getattr(self, "enemy_turn_in_progress", False):
            self.ui.text(self.canvas,"End your turn to draw three cards.",(800,804),21,INK,True)

    def run(self,frames=None):
        if not self.running:
            pygame.quit()
            return
        count=0
        try:
            while self.running and (frames is None or count<frames):
                dt=min(self.clock.tick(60)/1000,0.05)
                for event in pygame.event.get(): self.event(event)
                self.update(dt)
                self.draw()
                count+=1
        finally:
            pygame.quit()
