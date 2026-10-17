import pygame

INK=(232,236,249)
MUTED=(148,160,188)

class UI:
    def __init__(self):
        self.fonts={}

    def font(self,size):
        if size not in self.fonts:
            self.fonts[size]=pygame.font.SysFont("segoeui",size)
        return self.fonts[size]

    def text(self,surface,text,pos,size=24,color=INK,center=False):
        label=self.font(size).render(text,True,color)
        rect=label.get_rect(center=pos) if center else label.get_rect(topleft=pos)
        surface.blit(label,rect)

    def panel(self,surface,rect,fill=(20,27,46),border=(58,69,99),radius=16):
        pygame.draw.rect(surface,fill,rect,border_radius=radius)
        pygame.draw.rect(surface,border,rect,1,border_radius=radius)

    def button(self,surface,rect,label,mouse,accent,enabled=True):
        hover=rect.collidepoint(mouse) and enabled
        self.panel(surface,rect,tuple(int(c*0.28) for c in accent) if hover else (29,37,59),accent if enabled else (59,65,83),12)
        self.text(surface,label,rect.center,24,INK if enabled else MUTED,True)

    def wrap(self,surface,text,rect,size=26,color=MUTED):
        words=text.split(); line=""; y=rect.y
        for word in words:
            candidate=(line+" "+word).strip()
            if self.font(size).size(candidate)[0]>rect.width and line:
                self.text(surface,line,(rect.x,y),size,color)
                y+=size+12; line=word
            else: line=candidate
        self.text(surface,line,(rect.x,y),size,color)

    def health(self,surface,name,fighter,rect,accent):
        self.panel(surface,rect)
        self.text(surface,name,(rect.x+20,rect.y+12),24)
        self.text(surface,f"{fighter.hp} / {fighter.max_hp}",(rect.right-105,rect.y+16),20)
        bar=pygame.Rect(rect.x+20,rect.y+54,rect.width-40,8)
        pygame.draw.rect(surface,(48,54,75),bar,border_radius=4)
        if fighter.hp:
            pygame.draw.rect(surface,accent,(bar.x,bar.y,int(bar.width*fighter.hp/fighter.max_hp),8),border_radius=4)
        if fighter.block:
            self.text(surface,f"BLOCK  {fighter.block}",(rect.x+20,rect.bottom+8),20,(142,206,255))

    def card(self,surface,card,rect,hover,affordable):
        colors={"attack":(240,145,158),"block":(131,197,244),"heal":(137,225,187)}
        color=colors[card.category] if affordable else (95,103,124)
        self.panel(surface,rect,(35,42,66) if hover and affordable else (24,31,51),color if hover else (63,73,102),14)
        self.text(surface,card.name,(rect.x+16,rect.y+14),22,color)
        pygame.draw.circle(surface,color,(rect.right-28,rect.y+30),16)
        self.text(surface,str(card.cost),(rect.right-28,rect.y+29),21,(14,22,35),True)
        cx,cy=rect.centerx,rect.y+92
        if card.category=="attack":
            pygame.draw.polygon(surface,color,[(cx+24,cy-30),(cx+15,cy+7),(cx-22,cy+28),(cx-12,cy-10)],3)
            pygame.draw.line(surface,color,(cx-25,cy-12),(cx+15,cy+28),3)
        elif card.category=="block":
            pygame.draw.polygon(surface,color,[(cx-26,cy-24),(cx+26,cy-24),(cx+22,cy+9),(cx,cy+31),(cx-22,cy+9)],3)
        else:
            pygame.draw.line(surface,color,(cx-23,cy),(cx+23,cy),5)
            pygame.draw.line(surface,color,(cx,cy-23),(cx,cy+23),5)
        self.text(surface,card.category.upper(),(rect.x+16,rect.y+140),15,color)
        self.text(surface,card.description,(rect.x+16,rect.y+169),18,INK if affordable else MUTED)
        if not affordable:
            self.text(surface,"Not enough energy",(rect.x+16,rect.y+195),14,MUTED)
