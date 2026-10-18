from dataclasses import dataclass
import pygame
import math
import random

@dataclass
class Popup:
    text: str
    position: tuple
    color: tuple
    age: float = 0

class Effects:
    def __init__(self):
        self.popups=[]
        self.bursts=[]

    def add(self, effects, stage, action="attack"):
        for effect in effects:
            spec=stage["player" if effect.target=="player" else "opponent"]
            pos=spec["position"]
            height=spec["size"][1]*spec.get("scale",1.0)
            color={"damage":(255,150,160),"heal":(136,246,192),"block":(142,206,255),"charge":(233,199,255)}[effect.kind]
            label={"damage":f"−{effect.amount}","heal":f"+{effect.amount} HP","block":f"+{effect.amount} BLOCK","charge":"CHARGING"}[effect.kind]
            center=(pos[0],pos[1]-height*0.5)
            heavy=action in ("heavy","special")
            rng=random.Random(len(self.bursts)+effect.amount)
            particles=[(rng.uniform(0,math.tau),rng.uniform(45,140 if heavy else 90)) for _ in range(14 if heavy else 7)]
            self.bursts.append({"kind":effect.kind,"heavy":heavy,"center":center,"color":color,"age":0.0,"particles":particles})
            self.popups.append(Popup(label,(pos[0],pos[1]-height*0.65),color))

    def update(self, dt):
        for burst in self.bursts: burst["age"]+=dt
        self.bursts=[burst for burst in self.bursts if burst["age"]<0.65]
        for popup in self.popups: popup.age+=dt
        self.popups=[p for p in self.popups if p.age<1.1]

    def draw(self,surface,font):
        for burst in self.bursts:
            age=burst["age"]; x,y=burst["center"]; color=burst["color"]
            layer=pygame.Surface((320,320),pygame.SRCALPHA)
            alpha=round(255*max(0,1-age/0.80))
            c=(*color,alpha); kind=burst["kind"]
            if kind=="damage":
                radius=int(20+age*(150 if burst["heavy"] else 95))
                pygame.draw.circle(layer,c,(160,160),radius,5 if burst["heavy"] else 3)
                if age<0.30:
                    length=65 if burst["heavy"] else 42
                    pygame.draw.line(layer,(*color,alpha),(160-length,160+length),(160+length,160-length),10 if burst["heavy"] else 5)
                    if burst["heavy"]:
                        pygame.draw.line(layer,(*color,alpha),(110,115),(210,205),8)
            elif kind=="block":
                r=int(46+12*min(1,age/0.2))
                pygame.draw.polygon(layer,c,[(160,160-r),(160+r,140),(160+r-8,180),(160,220),(160-r+8,180),(160-r,140)],5)
            elif kind=="heal":
                pygame.draw.ellipse(layer,c,(108,185-int(age*45),104,25),4)
                pygame.draw.line(layer,c,(145,135),(175,135),6)
                pygame.draw.line(layer,c,(160,120),(160,150),6)
            else:
                pygame.draw.circle(layer,c,(160,160),int(60-30*age),2)
            for angle,speed in burst["particles"]:
                px=160+math.cos(angle)*speed*age
                py=160+math.sin(angle)*speed*age-(age*45 if kind=="heal" else -age*age*30)
                pygame.draw.polygon(layer,c,[(px,py-4),(px+4,py),(px,py+4),(px-4,py)])
            size=480 if burst["heavy"] else 400
            layer=pygame.transform.smoothscale(layer,(size,size))
            surface.blit(layer,(x-size//2,y-size//2))
        for popup in self.popups:
            label=font.render(popup.text,True,popup.color)
            label=pygame.transform.smoothscale_by(label,1.25)
            label.set_alpha(int(255*min(1,(1.1-popup.age)*3)))
            position=(popup.position[0]-label.get_width()/2,popup.position[1]-popup.age*75)
            shadow=label.copy();shadow.fill((0,0,0,210),special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow,(position[0]+2,position[1]+3))
            surface.blit(label,position)
