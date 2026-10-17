import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
from src.core.app import App
from src.core.input import viewport, logical_mouse
from src.rendering.background import Background

def test_letterbox_mouse():
    assert viewport((1000,1000))==pygame.Rect(0,219,1000,562)
    assert logical_mouse((500,500),(1000,1000))==(800,450)
    assert logical_mouse((500,20),(1000,1000))==(-1,-1)

def click(app,point):
    area=viewport(app.window.get_size())
    pos=(int(area.x+point[0]*area.width/1600),int(area.y+point[1]*area.height/900))
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))

def test_scene_rendering_and_input(tmp_path):
    app=App()
    try:
        app.draw(); click(app,(800,615)); assert app.campaign.scene=="intro"
        app.draw(); click(app,(800,615)); assert app.campaign.scene=="battle"
        app.update(0.3); app.draw()
        b=app.campaign.battle; old=len(b.deck.hand)
        click(app,app.card_rects[0].center)
        assert len(b.deck.hand)==old-1
        app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        lock=app.lock; app.update(1); app.draw()
        assert app.paused and app.lock==lock
        click(app,(800,440)); assert not app.paused
        app.update(1); app.draw(); click(app,(1420,780)); assert b.turn==2
        for i in range(5):
            app.campaign.index=i; app.load_stage()
            for scene in ("intro","battle","clear","over","victory"):
                if scene=="battle": app.campaign.enter_battle(seed=0)
                app.campaign.scene=scene; app.update(0.01); app.draw()
        pygame.display.set_mode((1000,1000),pygame.RESIZABLE)
        app.draw()
    finally: pygame.quit()

def test_png_background_and_sequence(tmp_path):
    app=App()
    try:
        path=tmp_path/"layer.png"
        image=pygame.Surface((1920,1080),pygame.SRCALPHA); image.fill((20,80,120,255)); pygame.image.save(image,path)
        stage=dict(app.campaign.stage)
        stage["background"]={"layers":[{"path":str(path),"depth":0}],"sequences":[{"frames":[str(path)],"foreground":True,"fps":12}]}
        bg=Background(app.assets,stage)
        bg.draw(app.canvas,1); assert all(abs(a-b)<=3 for a,b in zip(app.canvas.get_at((800,800))[:3],(20,80,120)))
        bg.draw(app.canvas,1,True)
        assert len(app.assets.cache)>0
    finally: pygame.quit()
