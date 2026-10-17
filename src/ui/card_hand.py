"""Presentation-only card instances, easing, draw order, and transformed input."""
from collections import OrderedDict
from dataclasses import dataclass
import pygame
from src.ui.card_layout import FanConfig, Pose, fan_layout, card_contains
from src.ui.card_art import card_face

@dataclass
class CardView:
    card: object
    pose: Pose

class CardHand:
    def __init__(self, ui, config=FanConfig()):
        self.ui=ui
        self.config=config
        self.views=[]
        self.hovered=None
        self.faces={}
        self.transforms=OrderedDict()
        self.ghost=None
        self.ghost_age=0.0

    def sync(self, cards):
        if len(cards)==len(self.views) and all(v.card is c for v,c in zip(self.views,cards)): return
        # Explicit removal on play preserves occurrence identity for repeated cards.
        remaining=list(self.views); views=[]
        for card,pose in zip(cards,fan_layout(len(cards),self.config)):
            match=next((i for i,v in enumerate(remaining) if v.card is card),None)
            views.append(remaining.pop(match) if match is not None else CardView(card,pose))
        self.views=views
        self.hovered=None

    def order(self):
        return [i for i in range(len(self.views)) if i!=self.hovered]+([self.hovered] if self.hovered is not None else [])

    def hit(self, point):
        for i in reversed(self.order()):
            pose=self.views[i].pose
            visible=Pose(pose.x,pose.y,round(pose.angle*2)/2,round(pose.scale*50)/50)
            if card_contains(point,visible,self.config): return i
        return None

    def update(self, dt, mouse, enabled=True):
        bases=fan_layout(len(self.views),self.config)
        # Retain a raised card over its former footprint to avoid hover oscillation.
        if not enabled: self.hovered=None
        elif self.hovered is not None and (card_contains(mouse,self.views[self.hovered].pose,self.config) or card_contains(mouse,bases[self.hovered],self.config)):
            pass
        else: self.hovered=self.hit(mouse)
        for i,(view,base) in enumerate(zip(self.views,bases)):
            target=Pose(base.x,base.y-self.config.hover_lift,0,self.config.hover_scale) if i==self.hovered else base
            view.pose.toward(target,dt,self.config.speed)
        if self.ghost:
            self.ghost_age+=dt
            if self.ghost_age>=0.35: self.ghost=None

    def remove(self,index):
        view=self.views.pop(index)
        self.ghost=CardView(view.card,Pose(view.pose.x,view.pose.y,view.pose.angle,view.pose.scale))
        self.ghost_age=0
        self.hovered=None

    def face(self,card,affordable,highlight):
        key=(card,affordable,highlight)
        if key not in self.faces:
            self.faces[key]=card_face(self.ui,card,(self.config.width,self.config.height),affordable,highlight)
        return self.faces[key]

    def transformed(self,view,energy,highlight):
        # Quantize transient transforms and bound the cache to avoid growth.
        angle=round(view.pose.angle*2)/2
        scale=round(view.pose.scale*50)/50
        key=(view.card,view.card.cost<=energy,highlight,angle,scale)
        if key not in self.transforms:
            face=pygame.transform.rotozoom(self.face(view.card,view.card.cost<=energy,highlight),angle,scale)
            shadow=face.copy()
            shadow.fill((0,0,0,130),special_flags=pygame.BLEND_RGBA_MULT)
            self.transforms[key]=(face,shadow)
            if len(self.transforms)>160: self.transforms.popitem(last=False)
        self.transforms.move_to_end(key)
        return self.transforms[key]

    def draw(self,surface,energy):
        for i in self.order():
            view=self.views[i]; face,shadow=self.transformed(view,energy,i==self.hovered)
            rect=face.get_rect(center=(round(view.pose.x),round(view.pose.y)))
            surface.blit(shadow,(rect.x+4,rect.y+7))
            surface.blit(face,rect)
        if self.ghost:
            face=self.transformed(self.ghost,99,True)[0].copy()
            progress=min(1,self.ghost_age/0.35)
            ease=1-(1-progress)**3
            face.set_alpha(round(255*(1-progress**2)))
            size=(max(1,round(face.get_width()*(1-0.25*ease))),max(1,round(face.get_height()*(1-0.25*ease))))
            face=pygame.transform.smoothscale(face,size)
            x=self.ghost.pose.x+(800-self.ghost.pose.x)*ease*0.35
            surface.blit(face,face.get_rect(center=(round(x),round(self.ghost.pose.y-105*ease))))
