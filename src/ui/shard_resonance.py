"""Between-stage attunement presentation; Campaign remains authoritative."""
import math
import random
import pygame
from src.scenes.campaign import SHOP_CATALOG
from src.ui.widgets import UI, INK
from src.ui.resonance_icons import icon_surface, FROST, GLACIAL

MUTED=(180,185,205)

ACCENTS = {"hp":(241,133,161), "attack":FROST, "shield":(127,195,246),
           "heavy":GLACIAL, "heal":(129,221,173), "energy":(238,206,125)}
SUMMARY = {"hp":"+5 maximum health", "attack":"+2 Magic", "shield":"+2 Shield Block",
           "heavy":"Amplify Glacial Bolt", "heal":"+2 healing", "energy":"+1 energy on the first turn"}


def diamond(surface, color, center, radius, width=0):
    x,y=center
    pygame.draw.polygon(surface,color,[(x,y-radius),(x+radius,y),(x,y+radius),(x-radius,y)],width)


class ResonanceTypography(UI):
    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.SysFont("arial", size, bold=size>=29)
        return self.fonts[size]


class ShardResonance:
    def __init__(self):
        self.ui = ResonanceTypography()
        self.visit = None
        self.choices = []
        self.selected = None
        self.pressed = None
        self.balance = 0.0
        self.pulse = 0.0
        self.spent = 0
        self.hover = {}
        self.message = "Choose a resonance. Carry its strength into the next battle."
        self.sigil = pygame.Surface((1600,900),pygame.SRCALPHA)
        for radius in (245,325,410):
            pygame.draw.circle(self.sigil,(130,110,190,22),(800,460),radius,1)
        for i in range(12):
            angle=i*math.tau/12
            diamond(self.sigil,(167,146,220,32),(800+math.cos(angle)*325,460+math.sin(angle)*325),9,1)
        pygame.draw.polygon(self.sigil,(150,130,210,20),[(800,60),(1220,730),(380,730)],2)

    def enter(self, campaign):
        if self.visit is campaign.last_battle_result and self.choices: return
        self.visit = campaign.last_battle_result
        pool=[key for key,cat in SHOP_CATALOG.items() if campaign.upgrades[key]<cat["max_level"]]
        rest=[key for key in SHOP_CATALOG if key not in pool]
        self.choices=random.sample(pool,min(3,len(pool)))
        self.choices+=random.sample(rest,3-len(self.choices))
        self.selected=None; self.pressed=None; self.pulse=0; self.spent=0
        self.balance=float(campaign.shards); self.hover={key:0.0 for key in self.choices}
        self.message="Choose a resonance. Carry its strength into the next battle."

    def update(self, dt, campaign):
        self.enter(campaign)
        self.balance+=(campaign.shards-self.balance)*(1-math.exp(-dt*9))
        if abs(self.balance-campaign.shards)<.1: self.balance=float(campaign.shards)
        self.pulse=max(0,self.pulse-dt)

    def buy(self, campaign, key):
        self.enter(campaign)
        if key not in self.choices or self.pulse>.55: return False
        cost=campaign.item_cost(key)
        if not campaign.buy(key): return False
        self.selected=key; self.spent=cost; self.pulse=.85
        self.message=SHOP_CATALOG[key]["name"]+" enhanced. Your next battle begins stronger."
        return True

    def event(self, app, event, mouse):
        if event.type not in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP) or event.button!=1: return False
        hit=next((key for key,rect in app.buttons.items() if rect.collidepoint(mouse)),None)
        if event.type==pygame.MOUSEBUTTONDOWN:
            self.pressed=hit
            if hit and hit.startswith("select_"): self.selected=hit[7:]
        else:
            pressed=self.pressed; self.pressed=None
            if hit and pressed==hit:
                if hit.startswith("select_"): self.selected=hit[7:]
                else: app.action(hit)
        return True

    def values(self,c,key):
        if key=="hp": return c.player_max_hp(),5
        if key=="energy": return 2+c.upgrades[key],1
        if key=="heavy":
            current=c.glacial_damage()
            return current,c.glacial_damage(c.upgrades[key]+1)-current
        card=next(card for card in c.active_cards() if card.id==key)
        return card.amount,2

    def icon(self,s,key,center,color):
        diamond(s,tuple(int(v*.18) for v in color),center,49)
        diamond(s,color,center,49,1)
        s.blit(icon_surface(key,96),(center[0]-48,center[1]-48))

    def draw(self, app, mouse):
        c=app.campaign; ui=self.ui; s=app.canvas; self.enter(c)
        s.fill((11,13,25)); s.blit(self.sigil,(0,0))
        ui.text(s,"ATTUNE THE FRAGMENTS",(800,47),16,(170,154,209),True)
        ui.text(s,"Shard Resonance",(800,93),48,INK,True)
        ui.panel(s,pygame.Rect(1260,48,252,80),(30,27,48),(119,99,155),18)
        diamond(s,(226,201,255),(1295,88),13,2)
        ui.text(s,str(round(self.balance)),(1320,60),30,INK)
        ui.text(s,"VEIL SHARDS",(1320,98),14,(196,178,222))
        result=c.last_battle_result or {}
        won=result.get("won",False)
        status="Stage cleared" if won else "Journey interrupted"
        summary=f"{status}  /  {result.get('stage_name',c.stage['name'])}  /  +{result.get('earned',0)} shards"
        if result.get("half_reward"): summary+="  /  repeat reward"
        ui.panel(s,pygame.Rect(230,145,1140,43),(24,26,43),(56,53,79),10)
        ui.text(s,summary,(800,166),20,(200,196,218),True)
        ui.text(s,"THREE RESONANCES REVEAL THEMSELVES",(800,219),16,(191,182,213),True)
        for i,key in enumerate(self.choices):
            cat=SHOP_CATALOG[key]; level=c.upgrades[key]; maximum=cat["max_level"]
            base=pygame.Rect(165+i*430,253,410,435)
            hover=base.collidepoint(mouse)
            # Easing is updated with delta time in the app, not during drawing.
            amount=self.hover.get(key,0)
            rect=base.inflate(round(amount*8),round(amount*8));rect.y-=round(amount*6)
            color=ACCENTS[key]; maxed=level>=maximum; enabled=c.can_buy(key) and self.pulse<=.55
            if maxed: color=(140,139,160)
            pulse=self.pulse/.85 if key==self.selected else 0
            border=color if hover or key==self.selected else tuple(round(v*.45) for v in color)
            ui.panel(s,rect,(int(24+8*amount+12*pulse),int(26+6*amount),int(43+12*amount+16*pulse)),border,18)
            if key==self.selected:
                pygame.draw.rect(s,(*color,255),rect.inflate(-6,-6),2,border_radius=15)
            x=rect.centerx; y=rect.y
            pygame.draw.line(s,color,(rect.x+30,y+1),(rect.right-30,y+1),3)
            self.icon(s,key,(x,y+70),color)
            ui.text(s,cat["name"],(x,y+139),29,INK,True)
            ui.text(s,SUMMARY[key],(x,y+180),21,(215,212,226),True)
            current,step=self.values(c,key)
            preview=f"{current}  →  {current+step}" if not maxed else str(current)
            ui.text(s,preview,(x,y+226),36,color,True)
            detail="CURRENT  →  NEXT" if not maxed else "FULLY ATTUNED"
            if key=="heavy":
                multiplier=lambda n: f"{c.glacial_multiplier(n):.2f}".rstrip("0").rstrip(".")
                detail=f"{multiplier(level)}× Magic" if maxed else f"{multiplier(level)}× → {multiplier(level+1)}× Magic"
            elif key=="attack": detail="MAGIC · FROST BOLT DAMAGE"
            ui.text(s,detail,(x,y+259),15,MUTED,True)
            for j in range(maximum):
                diamond(s,color if j<level else (117,119,148),(x+(j-(maximum-1)/2)*23,y+292),6,0 if j<level else 1)
            ui.text(s,f"Level {level} / {maximum}",(x,y+318),16,(199,196,215),True)
            cost=c.item_cost(key)
            ui.text(s,"Resonance complete" if maxed else f"{cost} shards",(x,y+348),21,color if not maxed else MUTED,True)
            button=pygame.Rect(rect.x+28,y+373,rect.width-56,45)
            label="Fully attuned" if maxed else "Enhance" if c.can_buy(key) else f"Need {cost-c.shards} more shards"
            pressed=self.pressed=="buy_"+key
            fill=tuple(int(v*(.38 if pressed else .25 if button.collidepoint(mouse) else .18)) for v in color) if enabled else (28,29,42)
            ui.panel(s,button,fill,color if enabled else (65,65,84),10)
            ui.text(s,label,(button.centerx,button.centery+(2 if pressed else 0)),21,INK if enabled else MUTED,True)
            if enabled: app.buttons["buy_"+key]=button
            app.buttons["select_"+key]=rect
        ui.text(s,self.message,(800,726),20,(199,185,225),True)
        if self.pulse:
            ui.text(s,f"−{self.spent} shards",(1385,145),18,(220,174,235),True)
        app.button("next" if won else "retry","Proceed to next stage" if won else "Retry this stage",(600,779,400,62),mouse,accent=(186,159,240))
        app.button("menu","Main Menu",(350,788,200,44),mouse,accent=(105,101,129))
        if not won and c.index>0:
            app.button("retry_prev","Previous stage",(1050,788,220,44),mouse,accent=(105,101,129))
        ui.text(s,"Upgrades persist through this journey. Unspent shards are kept.",(800,871),16,MUTED,True)

    def update_hover(self, dt, mouse):
        for i,key in enumerate(self.choices):
            active=pygame.Rect(165+i*430,243,410,455).collidepoint(mouse) or key==self.selected
            self.hover[key]+=(float(active)-self.hover[key])*(1-math.exp(-dt*14))
