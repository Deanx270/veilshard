"""Shared cached geometric spell/attunement icons. No combat dependencies."""
from functools import lru_cache
import math
import pygame

FROST=(127,220,249)
GLACIAL=(145,191,255)


@lru_cache(maxsize=48)
def icon_surface(kind: str, size: int = 120):
    s=pygame.Surface((128,128),pygame.SRCALPHA)
    white=(230,250,255); cyan=(115,227,255); blue=(63,132,202)
    def shard(points, color=cyan):
        tip,right,tail,left=points
        center=((right[0]+left[0])/2,(right[1]+left[1])/2)
        pygame.draw.polygon(s,color,points)
        pygame.draw.polygon(s,white,[tip,center,left])
        pygame.draw.polygon(s,blue,[center,right,tail])
        pygame.draw.line(s,(183,246,255),tip,tail,1)
    if kind in ("attack","heavy"):
        heavy=kind=="heavy"
        color=(148,162,233) if heavy else (113,184,208)
        pygame.draw.circle(s,(*color,65),(64,64),48,1)
        pygame.draw.circle(s,(*color,160),(64,64),42,2)
        if heavy:
            pygame.draw.circle(s,(*color,110),(64,64),35,1)
            for i in range(8):
                a=i*math.pi/4
                p=(64+math.cos(a)*47,64+math.sin(a)*47)
                q=(64+math.cos(a)*53,64+math.sin(a)*53)
                pygame.draw.line(s,color,p,q,2)
            shard([(97,12),(87,66),(29,109),(34,51)])
            shard([(37,29),(32,47),(15,60),(20,41)],(151,180,255))
            shard([(110,70),(105,90),(87,105),(93,84)],(151,180,255))
        else:
            for p,q in [((64,16),(64,23)),((105,64),(112,64)),((64,105),(64,112)),((16,64),(23,64))]:
                pygame.draw.line(s,color,p,q,2)
            shard([(89,29),(78,65),(39,94),(45,57)])
            pygame.draw.line(s,(*cyan,90),(29,94),(16,106),2)
        for x,y in ((26,72),(92,39),(67,108)):
            pygame.draw.line(s,white,(x-3,y),(x+3,y),1)
            pygame.draw.line(s,white,(x,y-3),(x,y+3),1)
    elif kind=="hp":
        pts=[(64,100),(24,61),(24,39),(42,27),(64,43),(86,27),(104,39),(104,61)]
        pygame.draw.polygon(s,(225,104,145),pts)
        pygame.draw.polygon(s,(255,186,204),[(24,39),(42,27),(64,43),(64,100),(24,61)])
        pygame.draw.polygon(s,(255,231,240),[(64,48),(75,66),(64,86),(53,66)],2)
    elif kind=="shield":
        pts=[(64,18),(101,35),(94,79),(64,109),(34,79),(27,35)]
        pygame.draw.polygon(s,(65,139,192),pts)
        pygame.draw.polygon(s,(166,227,255),[(64,18),(64,109),(34,79),(27,35)])
        pygame.draw.polygon(s,(217,247,255),pts,2)
        pygame.draw.polygon(s,(58,111,174),[(64,38),(78,61),(64,84),(50,61)])
        pygame.draw.line(s,white,(64,38),(64,84),2)
    elif kind=="heal":
        # Crescent contour, no opaque cutout against the transparent background.
        outer=[(64+36*math.cos(a),61+36*math.sin(a)) for a in [math.radians(60+i*240/40) for i in range(41)]]
        inner=[(78+31*math.cos(a),61+31*math.sin(a)) for a in [math.radians(300-i*240/40) for i in range(41)]]
        pygame.draw.polygon(s,(175,238,215),outer+inner)
        for x,y,r in ((86,57,10),(69,102,4),(100,87,4)):
            pygame.draw.polygon(s,(224,255,241),[(x,y-r),(x+r/2,y),(x,y+r),(x-r/2,y)])
        pygame.draw.arc(s,(98,175,153),(18,87,92,25),math.pi,math.tau,2)
    else:
        pygame.draw.circle(s,(186,164,101,110),(64,64),43,1)
        shard([(64,19),(85,58),(64,108),(43,58)],(243,213,132))
        pygame.draw.polygon(s,(255,244,186),[(64,19),(64,108),(43,58)])
        for y in (44,83):
            pygame.draw.lines(s,(234,208,133),False,[(27,y-9),(27,y),(40,y)],2)
            pygame.draw.lines(s,(234,208,133),False,[(88,y),(101,y),(101,y+9)],2)
    return pygame.transform.smoothscale(s,(size,size))
