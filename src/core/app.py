import math
import pygame
from src.core.input import SIZE, logical_mouse, viewport
from src.scenes.campaign import Campaign
from src.rendering.assets import Assets
from src.rendering.background import Background
from src.rendering.characters import placeholder, draw_character
from src.rendering.effects import Effects
from src.ui.widgets import UI, INK, MUTED

class App:
    def __init__(self):
        pygame.init()
        self.window=pygame.display.set_mode((1280,720),pygame.RESIZABLE)
        self.canvas=pygame.Surface(SIZE)
        self.campaign=Campaign()
        pygame.display.set_caption(self.campaign.story["title"])
        self.assets=Assets()
        self.ui=UI()
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
        self.card_rects=[]
        self.played_card=None
        self.played_age=0.0
        self.load_stage()

    def load_stage(self):
        stage=self.campaign.stage
        if self.loaded_stage==stage["id"]: return
        self.loaded_stage=stage["id"]
        self.background=Background(self.assets,stage)
        self.characters=[]
        for key in ("player","opponent"):
            spec=stage[key]
            asset=self.assets.image(spec["path"],tuple(spec["size"]))
            self.characters.append(asset or placeholder(spec["size"],stage["accent"] if key=="opponent" else (146,175,244),key=="opponent",key=="opponent" and stage["id"] in (2,4)))

    def change_feedback(self):
        if self.campaign.scene!=self.last_scene:
            self.last_scene=self.campaign.scene
            self.fade=0.28
            self.card_rects=[]
        self.played_card=None
        self.played_age=0.0
        self.load_stage()

    def action(self,name):
        c=self.campaign
        if name=="start": c.start()
        elif name=="battle":
            c.enter_battle()
            self.effects=Effects()
        elif name=="next": c.advance()
        elif name=="retry": c.retry()
        elif name=="menu":
            c.scene="menu"; self.paused=False
        elif name=="quit": self.running=False
        elif name=="resume": self.paused=False
        elif name=="end" and c.battle and not self.lock:
            self.effects.add(c.battle.end_turn(),c.stage)
            self.lock=0.65
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
                    if not self.lock or self.paused: self.action(name)
                    return
            if self.campaign.scene=="battle" and not self.paused and not self.lock:
                for i,rect in enumerate(self.card_rects):
                    if rect.collidepoint(mouse):
                        card=self.campaign.battle.deck.hand[i]
                        effects=self.campaign.battle.play(i)
                        if effects:
                            self.played_card=(card,rect.copy())
                            self.played_age=0.0
                            self.effects.add(effects,self.campaign.stage)
                            self.lock=0.35
                        return

    def update(self,dt):
        if not self.paused:
            self.time+=dt
            self.effects.update(dt)
            self.played_age+=dt
            if self.played_age>=0.35: self.played_card=None
            self.lock=max(0,self.lock-dt)
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
        self.buttons={}; self.card_rects=[]
        self.background.draw(s,self.time,shake=self.effects.offset(self.time))
        if c.scene=="battle":
            self.draw_battle(mouse)
        else:
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
            self.buttons={}; self.card_rects=[]
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
        c=self.campaign; b=c.battle; s=self.canvas; ui=self.ui; accent=c.stage["accent"]
        for image,key in zip(self.characters,("player","opponent")):
            offset=self.effects.offset(self.time)
            draw_character(s,image,c.stage[key],(offset[0],offset[1]+math.sin(self.time*1.8)*3))
        self.background.draw(s,self.time,True,self.effects.offset(self.time))
        self.effects.draw(s,ui.font(34))
        ui.text(s,f"{c.index+1:02}  /  {c.stage['name'].upper()}",(42,28),23,accent)
        ui.text(s,f"TURN {b.turn:02}     •     ESC TO PAUSE",(1190,30),18,MUTED)
        ui.health(s,"The Duelist",b.player,pygame.Rect(60,85,420,82),(144,176,245))
        ui.health(s,c.stage["enemy"]["name"],b.enemy,pygame.Rect(1120,85,420,82),accent)
        ui.panel(s,pygame.Rect(545,105,510,72))
        ui.text(s,"ENEMY INTENT"+("  /  FRACTURED" if b.plan.enraged else ""),(565,115),14,accent)
        ui.text(s,b.intent.label,(565,137),23)
        # Opaque bottom UI guarantees readability above any foreground export.
        pygame.draw.rect(s,(12,18,33),(0,660,1600,240))
        pygame.draw.line(s,(57,68,97),(30,660),(1570,660),1)
        ui.text(s,"ENERGY",(65,714),18,MUTED)
        ui.text(s,f"{b.energy} / 2",(60,744),50,(160,187,255))
        ui.text(s,f"Draw {len(b.deck.draw_pile)}  /  Discard {len(b.deck.discard)}",(60,833),17,MUTED)
        width=250; gap=20; count=len(b.deck.hand)
        start=(1600-(count*width+max(0,count-1)*gap))/2
        for i,card in enumerate(b.deck.hand):
            rect=pygame.Rect(start+i*(width+gap),678,width,215)
            hover=rect.collidepoint(mouse) and not self.paused and not self.lock
            if hover: rect.y-=12
            self.card_rects.append(rect)
            ui.card(s,card,rect,hover,card.cost<=b.energy)
        if self.played_card:
            card,origin=self.played_card
            ghost=pygame.Surface((250,215),pygame.SRCALPHA)
            ui.card(ghost,card,pygame.Rect(0,0,250,215),True,True)
            ghost.set_alpha(int(255*(1-self.played_age/0.35)))
            s.blit(ghost,(origin.x,origin.y-self.played_age*240))
        if not b.deck.hand: ui.text(s,"No cards left. End your turn to draw three.",(800,780),25,MUTED,True)
        self.button("end","End turn",(1300,752,240,64),mouse,not self.lock and b.status=="active")
        ui.text(s,"Play cards • anticipate • endure",(1270,837),16,MUTED)

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
