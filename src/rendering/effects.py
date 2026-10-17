from dataclasses import dataclass
import pygame

@dataclass
class Popup:
    text: str
    position: tuple
    color: tuple
    age: float = 0

class Effects:
    def __init__(self):
        self.popups=[]
        self.flash=0.0
        self.target=(0,0)

    def add(self, effects, stage):
        for effect in effects:
            spec=stage["player" if effect.target=="player" else "opponent"]
            pos=spec["position"]
            height=spec["size"][1]*spec.get("scale",1.0)
            color={"damage":(255,150,160),"heal":(136,246,192),"block":(142,206,255),"charge":(233,199,255)}[effect.kind]
            label={"damage":f"−{effect.amount}","heal":f"+{effect.amount} HP","block":f"+{effect.amount} BLOCK","charge":"CHARGING"}[effect.kind]
            self.popups.append(Popup(label,(pos[0],pos[1]-height*0.65),color))
            if effect.kind=="damage":
                self.flash=0.18
                self.target=(pos[0],pos[1]-height*0.5)

    def update(self, dt):
        self.flash=max(0,self.flash-dt)
        for popup in self.popups: popup.age+=dt
        self.popups=[p for p in self.popups if p.age<1.1]

    def draw(self,surface,font):
        if self.flash:
            radius=int(70*(1-self.flash/0.18))+15
            pygame.draw.circle(surface,(244,225,255),self.target,radius,3)
        for popup in self.popups:
            label=font.render(popup.text,True,popup.color)
            label.set_alpha(int(255*min(1,(1.1-popup.age)*3)))
            surface.blit(label,(popup.position[0]-label.get_width()/2,popup.position[1]-popup.age*75))
