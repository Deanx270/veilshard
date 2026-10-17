"""Original procedural fantasy card faces; cached by the hand renderer."""
import pygame

COLORS={"attack":(229,128,96),"heavy":(198,145,232),"shield":(111,190,232),"heal":(155,213,117)}

def card_face(ui, card, size, affordable=True, highlight=False):
    w,h=size
    s=pygame.Surface(size,pygame.SRCALPHA)
    color=COLORS.get(card.id,(150,190,220))
    pygame.draw.rect(s,(19,21,31,248),(0,0,w,h),border_radius=8)
    for y in range(5,h-5):
        t=1-y/h
        shade=tuple(int(c*(0.14+0.22*t)) for c in color)
        pygame.draw.line(s,shade,(5,y),(w-6,y))
    gold=(218,191,139) if highlight else (155,137,106)
    pygame.draw.rect(s,gold,(1,1,w-2,h-2),2,border_radius=8)
    pygame.draw.rect(s,(*color,150),(6,6,w-12,h-12),1,border_radius=5)
    for x,y in ((9,9),(w-10,9),(9,h-10),(w-10,h-10)):
        pygame.draw.polygon(s,gold,[(x,y-4),(x+4,y),(x,y+4),(x-4,y)])
    cx,cy=w//2,91
    # Faceted magical illustrations, distinct even within the attack category.
    for i in range(5):
        pygame.draw.circle(s,(*color,25),(cx,cy),48-i*6,1)
    if card.id=="heavy":
        for dx,dy in ((-25,9),(0,-8),(25,12)):
            pygame.draw.polygon(s,color,[(cx+dx,cy+dy-43),(cx+dx+12,cy+dy),(cx+dx-9,cy+dy+34),(cx+dx-15,cy+dy)])
            pygame.draw.line(s,(247,211,242),(cx+dx,cy+dy-36),(cx+dx-8,cy+dy+15),2)
    elif card.category=="attack":
        pygame.draw.polygon(s,color,[(cx+35,cy-46),(cx+18,cy+3),(cx-34,cy+39),(cx-12,cy-3)])
        pygame.draw.polygon(s,(255,215,146),[(cx+35,cy-46),(cx-5,cy+8),(cx-34,cy+39),(cx+10,cy-19)])
        pygame.draw.line(s,color,(cx-30,cy-5),(cx+10,cy+33),4)
    elif card.category=="block":
        pygame.draw.polygon(s,color,[(cx,cy-43),(cx+37,cy-27),(cx+30,cy+14),(cx,cy+43),(cx-30,cy+14),(cx-37,cy-27)])
        pygame.draw.polygon(s,(39,81,125),[(cx,cy-30),(cx+25,cy-19),(cx+20,cy+9),(cx,cy+28),(cx-20,cy+9),(cx-25,cy-19)])
        pygame.draw.polygon(s,(150,224,255),[(cx,cy-30),(cx,cy+28),(cx-20,cy+9),(cx-25,cy-19)])
    else:
        pygame.draw.line(s,color,(cx,cy+40),(cx,cy-38),3)
        for direction,dy in ((-1,0),(1,17),(-1,29)):
            pygame.draw.polygon(s,color,[(cx,cy+dy),(cx+direction*32,cy+dy-32),(cx+direction*28,cy+dy-5)])
        pygame.draw.polygon(s,(213,241,145),[(cx,cy-47),(cx+12,cy-21),(cx,cy-6),(cx-12,cy-21)])
    pygame.draw.line(s,gold,(17,150),(w-17,150))
    ui.text(s,card.name,(cx,170),19,(244,233,212),True)
    lines=[]; line=""
    for word in card.description.split():
        candidate=(line+" "+word).strip()
        if ui.font(16).size(candidate)[0]>w-24 and line:
            lines.append(line); line=word
        else: line=candidate
    lines.append(line)
    for i,line in enumerate(lines):
        ui.text(s,line,(cx,199+i*18),16,(224,221,217),True)
    # Cost remains above the art, readable in overlapping hands.
    pygame.draw.polygon(s,gold,[(23,9),(40,29),(23,49),(7,29)])
    ui.text(s,str(card.cost),(23,28),25,(27,25,34),True)
    if not affordable:
        veil=pygame.Surface(size,pygame.SRCALPHA); veil.fill((8,12,23,115)); s.blit(veil,(0,0))
        ui.text(s,"LOW ENERGY",(cx,h-17),13,(212,191,172),True)
    return s
