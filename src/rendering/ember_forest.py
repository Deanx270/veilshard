"""Stage 1 composition study made from flat-shaded polygons, not final art."""
import random
import pygame


def draw_ember_forest(surface):
    rng = random.Random(41)
    # Elevated diamond clearing: front-left player, far-right guardian.
    pygame.draw.polygon(surface,(29,39,49),[(80,460),(780,245),(1530,430),(810,770)])
    pygame.draw.polygon(surface,(20,27,38),[(80,460),(810,770),(810,815),(80,505)])
    pygame.draw.polygon(surface,(24,31,42),[(810,770),(1530,430),(1530,475),(810,815)])
    pygame.draw.polygon(surface,(49,52,57),[(250,485),(820,310),(1370,450),(790,695)])
    pygame.draw.polygon(surface,(59,57,59),[(250,485),(820,310),(800,505)])
    pygame.draw.polygon(surface,(43,47,54),[(800,505),(1370,450),(790,695)])
    pygame.draw.lines(surface,(103,89,78),True,[(250,485),(820,310),(1370,450),(790,695)],2)
    for a,b in [((440,427),(990,610)),((630,368),(1180,530)),((435,555),(1005,357)),((620,625),(1190,403))]:
        pygame.draw.line(surface,(69,65,65),a,b,2)
    # Small broken Core plinth on the back rim.
    pygame.draw.polygon(surface,(86,82,94),[(738,316),(802,294),(865,316),(803,340)])
    pygame.draw.polygon(surface,(44,48,65),[(738,316),(803,340),(803,363),(738,339)])
    pygame.draw.polygon(surface,(61,61,80),[(803,340),(865,316),(865,339),(803,363)])
    pygame.draw.polygon(surface,(255,185,114),[(804,225),(828,267),(803,303),(781,267)])
    pygame.draw.polygon(surface,(192,101,89),[(804,225),(803,303),(781,267)])
    for x,y,h in [(165,390,230),(300,335,200),(480,280,215),(1040,280,220),(1260,330,250),(1460,390,235)]:
        pygame.draw.polygon(surface,(55,40,43),[(x-13,y),(x-10,y-h),(x+10,y-h),(x+17,y)])
        pygame.draw.polygon(surface,(80,51,46),[(x,y),(x,y-h),(x+10,y-h),(x+17,y)])
        pygame.draw.polygon(surface,(80,60,58),[(x-85,y-h+95),(x-65,y-h+20),(x+5,y-h-30),(x+95,y-h+45),(x+70,y-h+110)])
        pygame.draw.polygon(surface,(131,75,58),[(x-65,y-h+20),(x+5,y-h-30),(x+20,y-h+60),(x-85,y-h+95)])
        pygame.draw.polygon(surface,(103,55,53),[(x+5,y-h-30),(x+95,y-h+45),(x+20,y-h+60)])
    for _ in range(25):
        x,y=rng.randrange(160,1440),rng.randrange(375,640)
        if 350<x<1230: continue
        pygame.draw.polygon(surface,(92,66,59),[(x,y),(x+18,y-22),(x+37,y-7),(x+30,y+12)])
        pygame.draw.polygon(surface,(52,48,52),[(x,y),(x+30,y+12),(x+37,y-7),(x+15,y+2)])
