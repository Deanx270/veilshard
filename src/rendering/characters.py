import pygame

def placeholder(size, accent, enemy=False, beast=False):
    """Original graphic silhouettes; replace via stage character PNG paths."""
    s=pygame.Surface((360,480),pygame.SRCALPHA)
    pygame.draw.ellipse(s,(0,0,0,65),(50,445,265,28))
    dark=(26,32,57)
    light=(212,221,240)
    if beast:
        pygame.draw.polygon(s,dark,[(40,390),(70,230),(160,170),(260,215),(320,390),(265,450),(230,330),(130,330),(100,455)])
        pygame.draw.polygon(s,accent,[(90,230),(60,110),(170,185),(270,95),(250,240),(180,290)])
        pygame.draw.polygon(s,dark,[(115,222),(175,196),(235,218),(213,280),(151,280)])
        pygame.draw.line(s,light,(135,235),(157,241),5)
        pygame.draw.line(s,light,(201,241),(222,235),5)
    else:
        pygame.draw.polygon(s,accent,[(155,170),(100,235),(52,425),(170,390),(280,440),(250,230),(205,170)])
        pygame.draw.polygon(s,dark,[(147,183),(115,310),(138,420),(128,456),(164,456),(180,330),(196,456),(231,456),(217,420),(245,310),(207,183)])
        pygame.draw.polygon(s,light,[(151,182),(180,205),(207,183),(196,284),(164,284)])
        pygame.draw.polygon(s,accent,[(169,200),(188,200),(200,300),(177,326),(158,300)])
        pygame.draw.ellipse(s,(227,206,213),(141,86,75,99))
        hair=(214,221,245) if not enemy else (56,61,92)
        pygame.draw.polygon(s,hair,[(131,155),(126,102),(150,65),(193,58),(225,92),(229,165),(204,138),(198,100),(176,128),(170,103),(147,142)])
        pygame.draw.line(s,accent,(151,139),(164,139),3)
        pygame.draw.line(s,accent,(191,139),(204,139),3)
        pygame.draw.polygon(s,dark,[(145,194),(112,214),(78,298),(93,310),(156,241)])
        pygame.draw.polygon(s,dark,[(209,194),(239,214),(278,295),(262,311),(199,240)])
        pygame.draw.polygon(s,light,[(74,289),(92,287),(103,314),(84,321)])
        pygame.draw.polygon(s,accent,[(60,260),(91,247),(108,282),(77,295)],3)
        pygame.draw.line(s,accent,(275,315),(307,140),6)
        pygame.draw.polygon(s,light,[(307,100),(322,137),(307,170),(292,137)])
    return pygame.transform.smoothscale(s,size)

def draw_character(surface, image, spec, offset=(0,0)):
    pos=spec["position"]
    anchor=spec.get("anchor",[0.5,1])
    surface.blit(image,(int(pos[0]-image.get_width()*anchor[0]+offset[0]),int(pos[1]-image.get_height()*anchor[1]+offset[1])))
