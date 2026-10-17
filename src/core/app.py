import pygame
from src.core.input import SIZE, logical_mouse, viewport
from src.scenes.campaign import Campaign
from src.rendering.assets import Assets
from src.rendering.battlefield import Battlefield
from src.rendering.effects import Effects
from src.ui.widgets import UI, INK, MUTED
from src.ui.card_hand import CardHand
from src.rendering.action_timeline import ActionTimeline
from src.ui.battle_hud import BattleHUD

class App:
    def __init__(self):
        pygame.init()
        self.window=pygame.display.set_mode((1280,720),pygame.RESIZABLE)
        self.canvas=pygame.Surface(SIZE)
        self.campaign=Campaign()
        pygame.display.set_caption(self.campaign.story["title"])
        self.assets=Assets()
        self.ui=UI()
        self.hand=CardHand(self.ui)
        self.hud=BattleHUD(self.ui)
        self.end_pressed=0.0
        self.timeline=ActionTimeline()
        self.pending_card=None
        self.effects=Effects()
        self.clock=pygame.time.Clock()
        self.running=True
        self.paused=False
        self.time=0.0
        self.lock=0.0
        self.fade=0.0
        self.last_scene="menu"
        self.loaded_stage=None
        self.buttons={}
        self.load_stage()

    def load_stage(self):
        stage=self.campaign.stage
        if self.loaded_stage==stage["id"]: return
        self.loaded_stage=stage["id"]
        self.battlefield=Battlefield(self.assets,stage)
        self.background=self.battlefield.background

    def change_feedback(self):
        if self.campaign.scene!=self.last_scene:
            self.last_scene=self.campaign.scene
            self.fade=0.28
        self.load_stage()

    def action(self,name):
        c=self.campaign
        if name=="start": c.start()
        elif name=="battle":
            c.enter_battle()
            self.effects=Effects()
            self.timeline.cancel()
            self.pending_card=None
            self.lock=0
            self.hud.reset(c.battle)
            self.loaded_stage=None
            self.hand=CardHand(self.ui)
        elif name=="next": c.advance()
        elif name=="retry": c.retry()
        elif name=="menu":
            c.scene="menu"; self.paused=False
            self.timeline.cancel(); self.pending_card=None; self.lock=0
        elif name=="quit": self.running=False
        elif name=="resume": self.paused=False
        elif name=="pause": self.paused=True
        elif name=="end" and c.scene=="battle" and c.battle.status=="active" and not self.lock and not self.paused:
            self.end_pressed=0.16
            kind=c.battle.intent.kind
            self.begin_action(kind,"opponent",c.battle.end_turn)
        self.change_feedback()

    def event(self,event):
        if event.type==pygame.QUIT: self.running=False
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
            if self.campaign.scene=="battle" and not self.paused and not self.lock:
                i=self.hand.hit(mouse)
                if i is not None:
                    card=self.campaign.battle.deck.hand[i]
                    if card.cost<=self.campaign.battle.energy and self.campaign.battle.status=="active":
                        self.pending_card=i
                        self.hand.remove(i)
                        self.begin_action(card.id if card.category=="attack" else card.category,"player",lambda: self.campaign.battle.play(i))

    def begin_action(self,kind,source,resolve):
        def impact():
            effects=resolve()
            self.pending_card=None
            self.effects.add(effects,self.campaign.stage,kind)
            self.battlefield.feedback(effects,source,kind)
        if self.timeline.start(kind,source,impact):
            self.lock=self.timeline.remaining
            clip="attack" if kind in ("heavy","special") else "defend" if kind=="block" else kind
            self.battlefield.actors[source].trigger(clip)

    def visible_hand(self):
        cards=list(self.campaign.battle.deck.hand)
        if self.pending_card is not None: cards.pop(self.pending_card)
        return cards

    def update(self,dt):
        if not self.paused:
            self.time+=dt
            self.effects.update(dt)
            self.battlefield.update(dt)
            self.timeline.update(dt)
            self.lock=self.timeline.remaining
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

    def button(self,name,label,rect,mouse,enabled=True):
        rect=pygame.Rect(rect)
        if enabled: self.buttons[name]=rect
        self.ui.button(self.canvas,rect,label,mouse,self.campaign.stage["accent"],enabled)

    def draw(self):
        c=self.campaign; s=self.canvas; ui=self.ui
        mouse=logical_mouse(pygame.mouse.get_pos(),self.window.get_size())
        self.buttons={}
        if c.scene=="battle":
            self.draw_battle(mouse)
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

    def draw_battle(self,mouse):
        c=self.campaign; b=c.battle
        self.battlefield.draw(self.canvas,self.time,self.effects,self.ui.font(34))
        enabled=not self.lock and b.status=="active" and not self.paused
        self.hud.draw(self.canvas,c,mouse,enabled,self.end_pressed>0)
        self.buttons["pause"]=self.hud.pause
        if enabled: self.buttons["end"]=self.hud.end
        self.hand.sync(self.visible_hand())
        self.hand.draw(self.canvas,b.energy)
        if not b.deck.hand:
            self.ui.text(self.canvas,"End your turn to draw three cards.",(800,804),21,INK,True)

    def run(self,frames=None):
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
