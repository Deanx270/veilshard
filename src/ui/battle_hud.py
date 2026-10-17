"""Compact floating overlays, with no reserved battlefield region."""
import pygame
import math
from src.ui.widgets import INK, MUTED

GOLD=(204,182,139)

class CircleTarget:
    def __init__(self, center, radius):
        self.center=center; self.radius=radius
    def collidepoint(self,point):
        return (point[0]-self.center[0])**2+(point[1]-self.center[1])**2<=self.radius**2


def glass(surface,rect,alpha=155):
    rect=pygame.Rect(rect)
    pane=pygame.Surface(rect.size,pygame.SRCALPHA)
    pygame.draw.rect(pane,(13,17,27,alpha),pane.get_rect(),border_radius=8)
    surface.blit(pane,rect)


def bar(surface,rect,value,maximum,color):
    x,y,w,h=rect
    pygame.draw.polygon(surface,(21,25,31),[(x,y),(x+w,y),(x+w-8,y+h),(x-8,y+h)])
    fill=max(0,min(1,value/maximum))
    if fill:
        pygame.draw.polygon(surface,color,[(x,y+2),(x+(w-3)*fill,y+2),(x+(w-3)*fill-6,y+h-2),(x-5,y+h-2)])
    pygame.draw.lines(surface,GOLD,False,[(x-8,y+h+3),(x+w-6,y+h+3),(x+w+3,y)],1)


class BattleHUD:
    def __init__(self,ui):
        self.ui=ui
        self.display_hp={}
        self.end=CircleTarget((1450,786),70)
        self.pause=CircleTarget((1510,52),28)
        # Small original portrait, independent of full-height battle sprites.
        self.portrait=pygame.Surface((112,130),pygame.SRCALPHA)
        p=self.portrait
        pygame.draw.polygon(p,(22,29,44,220),[(56,0),(112,65),(56,130),(0,65)])
        pygame.draw.polygon(p,GOLD,[(56,2),(110,65),(56,128),(2,65)],2)
        pygame.draw.polygon(p,(88,106,154),[(56,71),(22,99),(56,122),(90,99)])
        pygame.draw.polygon(p,(226,204,199),[(32,44),(58,30),(81,46),(73,77),(55,91),(36,73)])
        pygame.draw.polygon(p,(206,215,237),[(23,66),(26,31),(56,15),(86,37),(89,73),(72,50),(60,42),(45,63),(43,43)])

    def reset(self,battle):
        self.display_hp={"player":float(battle.player.hp),"enemy":float(battle.enemy.hp)}

    def update(self,dt,battle):
        for key in ("player","enemy"):
            target=getattr(battle,key).hp
            previous=self.display_hp.get(key,float(target))
            self.display_hp[key]=previous+(target-previous)*(1-math.exp(-12*dt))
            if abs(self.display_hp[key]-target)<0.02: self.display_hp[key]=float(target)

    def draw(self,s,c,mouse,enabled=True,pressed=False):
        ui=self.ui; b=c.battle
        glass(s,(28,22,430,86),135)
        ui.text(s,f"Stage {c.index+1}  ·  {c.stage['name']}",(42,28),27,(244,231,206))
        pygame.draw.line(s,GOLD,(42,66),(435,66),1)
        ui.text(s,f"Defeat {c.stage['enemy']['name']}.",(42,77),18,(217,213,203))
        glass(s,(1340,25,110,48),130)
        ui.text(s,f"TURN {b.turn:02}",(1395,49),20,INK,True)
        pause_color=GOLD if self.pause.collidepoint(mouse) else (141,144,158)
        pygame.draw.circle(s,(31,32,45),self.pause.center,28)
        pygame.draw.circle(s,pause_color,self.pause.center,28,1)
        for x in (1502,1514): pygame.draw.rect(s,pause_color,(x,42,4,20))
        # Compact bottom-left status. No full-width fill or reserved viewport.
        glass(s,(40,722,335,142),130)
        s.blit(self.portrait,(28,723))
        ui.text(s,"THE DUELIST",(155,728),17,GOLD)
        ui.text(s,f"{b.player.hp} / {b.player.max_hp} HP",(155,755),23)
        bar(s,(156,791,205,13),self.display_hp.get("player",b.player.hp),b.player.max_hp,(125,208,160))
        for i in range(2):
            x=165+i*26
            color=(173,204,255) if i<b.energy else (68,74,91)
            pygame.draw.polygon(s,color,[(x,818),(x+9,827),(x,836),(x-9,827)],0 if i<b.energy else 1)
        ui.text(s,f"{b.energy}/2 ENERGY",(220,814),16,(191,208,239))
        if b.player.block: ui.text(s,f"◇ BLOCK {b.player.block}",(155,695),19,(151,207,248))
        ui.text(s,f"Draw {len(b.deck.draw_pile)}   ·   Discard {len(b.deck.discard)}",(153,847),15,MUTED)
        # Float above the configured sprite's head, clamped to the viewport.
        spec=c.stage['opponent']; height=spec['size'][1]*spec.get('scale',1)
        x=max(570,min(1250,spec['position'][0]-145))
        y=max(122,min(490,spec['position'][1]-height*spec.get('anchor',[0.5,1])[1]-100))
        glass(s,(x-14,y-8,320,101),145)
        ui.text(s,c.stage['enemy']['name'],(x,y),22,(244,230,210))
        bar(s,(x+4,y+33,285,10),self.display_hp.get("enemy",b.enemy.hp),b.enemy.max_hp,(227,113,105))
        ui.text(s,f"{b.enemy.hp} / {b.enemy.max_hp}"+(f"   ◇ {b.enemy.block} Block" if b.enemy.block else ""),(x,y+49),17)
        ui.text(s,b.intent.label+("  !" if b.plan.enraged else ""),(x,y+74),17,(244,187,141))
        hover=self.end.collidepoint(mouse) and enabled
        circle=pygame.Surface((174,174),pygame.SRCALPHA)
        pygame.draw.circle(circle,(18,22,33,185),(87,87),70)
        color=GOLD if enabled else (111,113,127)
        if hover: pygame.draw.circle(circle,(225,188,123,35),(87,87),78)
        radius=67 if pressed else 70
        pygame.draw.circle(circle,color,(87,87),radius,2)
        pygame.draw.circle(circle,(*color,140),(87,87),radius-6,1)
        for dx,dy in ((0,-80),(80,0),(0,80),(-80,0)):
            px,py=87+dx,87+dy
            pygame.draw.polygon(circle,color,[(px,py-6),(px+5,py),(px,py+6),(px-5,py)])
        s.blit(circle,(self.end.center[0]-87,self.end.center[1]-87))
        ui.text(s,"End",(1450,772),26,color,True)
        ui.text(s,"Turn",(1450,804),26,color,True)
        ui.text(s,"ESC · Pause",(1450,885),14,MUTED,True)
