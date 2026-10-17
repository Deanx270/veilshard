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
