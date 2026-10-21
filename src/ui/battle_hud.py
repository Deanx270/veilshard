"""Compact floating overlays, with no reserved battlefield region."""
import pygame
import math
from src.core.resources import resource
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
        self.portrait=self._build_portrait()

    def _build_portrait(self):
        dw,dh=124,144
        cx,cy=dw//2,dh//2
        pad_top=24
        pad_side=16
        surf_w=dw+pad_side*2
        surf_h=dh+pad_top+8

        portrait=pygame.Surface((surf_w,surf_h),pygame.SRCALPHA)
        dx0=pad_side
        dy0=pad_top
        diamond_poly=[
            (dx0+cx,dy0),
            (dx0+dw,dy0+cy),
            (dx0+cx,dy0+dh),
            (dx0,dy0+cy)
        ]

        # Background fill
        pygame.draw.polygon(portrait,(22,29,44,230),diamond_poly)
        # Upper diamond frame behind hair
        pygame.draw.lines(portrait,GOLD,False,[diamond_poly[3],diamond_poly[0],diamond_poly[1]],2)

        loaded=False
        try:
            icon_path=resource("assets/characters/icon_char_01_default.png")
            if icon_path.exists():
                icon_raw=pygame.image.load(str(icon_path)).convert_alpha()
                sw=int(dw*1.16)
                sh=sw
                scaled=pygame.transform.smoothscale(icon_raw,(sw,sh))
                ix=dx0+cx-int(sw*0.5)
                iy=dy0+cy-int(sh*0.49)

                char_layer=pygame.Surface((surf_w,surf_h),pygame.SRCALPHA)
                char_layer.blit(scaled,(ix,iy))

                mask=pygame.Surface((surf_w,surf_h),pygame.SRCALPHA)
                # Top half allows the head/hair to override the diamond
                pygame.draw.rect(mask,(255,255,255,255),(0,0,surf_w,dy0+cy))
                # Bottom half clips strictly within the lower diamond so it won't overlap the bottom half
                lower_tri=[
                    (dx0+2,dy0+cy),
                    (dx0+dw-2,dy0+cy),
                    (dx0+cx,dy0+dh-3)
                ]
                pygame.draw.polygon(mask,(255,255,255,255),lower_tri)
                char_layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
                portrait.blit(char_layer,(0,0))
                loaded=True
        except Exception:
            loaded=False

        if not loaded:
            # Fallback procedural placeholder
            pygame.draw.polygon(portrait,(88,106,154),[(dx0+cx,dy0+78),(dx0+24,dy0+109),(dx0+cx,dy0+135),(dx0+100,dy0+109)])
            pygame.draw.polygon(portrait,(226,204,199),[(dx0+35,dy0+49),(dx0+64,dy0+33),(dx0+90,dy0+51),(dx0+81,dy0+85),(dx0+61,dy0+101),(dx0+40,dy0+81)])
            pygame.draw.polygon(portrait,(206,215,237),[(dx0+25,dy0+73),(dx0+29,dy0+34),(dx0+62,dy0+17),(dx0+95,dy0+41),(dx0+98,dy0+81),(dx0+80,dy0+55),(dx0+66,dy0+47),(dx0+50,dy0+70),(dx0+47,dy0+47)])

        # Crisp gold frame on the bottom half of the diamond (never overlapped by the character image)
        pygame.draw.lines(portrait,GOLD,False,[diamond_poly[3],diamond_poly[2],diamond_poly[1]],2)
        pygame.draw.lines(portrait,(140,120,85),False,[(dx0+4,dy0+cy),(dx0+cx,dy0+dh-4),(dx0+dw-4,dy0+cy)],1)

        return portrait

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
        # Player status panel: slightly wider, proportionally enlarged elements, clear of card fan.
        gx,gy,gw,gh=38,712,396,154
        glass(s,(gx,gy,gw,gh),130)
        s.blit(self.portrait,(gx-26,gy-20))
        content_x=gx+124
        ui.text(s,"THE QUIET CODEX",(content_x,gy+12),18,GOLD)
        ui.text(s,f"{b.player.hp} / {b.player.max_hp} HP",(content_x,gy+38),26)
        bar(s,(content_x,gy+74,242,15),self.display_hp.get("player",b.player.hp),b.player.max_hp,(125,208,160))
        for i in range(2):
            ex=content_x+10+i*28
            ey=gy+106
            color=(173,204,255) if i<b.energy else (68,74,91)
            pygame.draw.polygon(s,color,[(ex,ey-9),(ex+9,ey),(ex,ey+9),(ex-9,ey)],0 if i<b.energy else 1)
        ui.text(s,f"{b.energy}/2 ENERGY",(content_x+70,gy+96),17,(191,208,239))
        if b.player.block: ui.text(s,f"◇ BLOCK {b.player.block}",(content_x,gy-26),20,(151,207,248))
        ui.text(s,f"Draw {len(b.deck.draw_pile)}   ·   Discard {len(b.deck.discard)}",(content_x,gy+126),15,MUTED)
        # Float above the configured sprite's head, clamped to the viewport.
        spec=c.stage['opponent']; scale=spec.get('scale',1)
        width=spec['size'][0]*scale; height=spec['size'][1]*scale
        anchor=spec.get('anchor',[0.5,1])
        ground=spec.get('shadow',{}).get('ground',anchor)
        crop=spec.get('shadow',{}).get('crop',[0,0,1,1])
        actor_x=spec['position'][0]+(ground[0]-anchor[0])*width
        head_y=spec['position'][1]-height*anchor[1]+height*crop[1]
        x=max(570,min(1250,round(actor_x-145)))
        y=max(122,min(490,round(head_y-100)))
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
