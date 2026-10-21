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
        click(app,(app.hand.views[0].pose.x,app.hand.views[0].pose.y))
        assert len(app.hand.views)==old-1 and len(b.deck.hand)==old
        app.update(app.timeline.impact)
        assert len(b.deck.hand)==old-1
        app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        lock=app.lock; app.update(1); app.draw()
        assert app.paused and app.lock==lock
        click(app,(800,440)); assert not app.paused
        app.update(2); app.draw(); click(app,(1420,780)); assert b.turn==1
        app.update(app.timeline.impact); assert b.turn==2
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


def test_character_frames_anchor_scale_flash_and_shadow(tmp_path):
    from src.rendering.characters import CharacterSprite
    from src.rendering.assets import Assets
    pygame.init(); pygame.display.set_mode((64,64))
    try:
        paths=[]
        for index,color in enumerate(((60,20,10),(10,70,20))):
            frame=pygame.Surface((20,20),pygame.SRCALPHA)
            pygame.draw.rect(frame,(*color,255),(5,5,10,10))
            path=tmp_path/f"{index}.png"; pygame.image.save(frame,path); paths.append(str(path))
        spec={"path":paths[0],"size":[20,20],"scale":2,"position":[80,80],"anchor":[0.5,0.5],
              "shadow":{"size":[30,10],"enabled":False},
              "animations":{"idle":{"frames":paths,"fps":10},"attack":{"frames":paths,"fps":10,"loop":False}}}
        actor=CharacterSprite(Assets(),spec,(100,100,100))
        assert actor.frame().get_size()==(40,40)
        first=actor.frame(); actor.update(0.11)
        assert actor.frame() is not first
        actor.update(0.1); assert actor.frame() is first
        actor.trigger("attack"); actor.update(0.21); assert actor.state=="idle"
        actor.trigger("hit")
        assert actor.frame().get_at((20,20)).r>first.get_at((20,20)).r
        assert actor.frame().get_at((0,0)).a==0
        target=pygame.Surface((160,160),pygame.SRCALPHA); actor.draw(target)
        assert target.get_at((80,80)).a>0 and target.get_at((59,59)).a==0
        actor.update(0.2); assert actor.hit_time==0
        spec["shadow"]["enabled"]=True
        target.fill((0,0,0,0)); actor.draw(target)
        assert target.get_at((55,80)).a>0
    finally: pygame.quit()


def test_render_order_camera_and_pause():
    from src.combat.battle import Effect
    app=App()
    try:
        app.action("start"); app.action("battle"); app.update(0.3)
        field=app.battlefield
        assert [key for key in sorted(field.actors,key=lambda key:field.actors[key].order)]==["opponent","player"]
        field.feedback([Effect("enemy","damage",6)],"player","attack")
        app.update(0.1)
        assert field.camera.zoom>1 and field.actors["opponent"].hit_time>0
        remaining=field.camera.remaining
        app.paused=True; app.update(0.1)
        assert field.camera.remaining==remaining
        app.paused=False; app.update(0.4)
        assert field.camera.zoom==1 and field.actors["opponent"].hit_time==0
        # Verify actual overlapping sprite pixels honor configurable draw order.
        for key,color in (("player",(255,0,0)),("opponent",(0,255,0))):
            actor=field.actors[key]; actor.spec=dict(actor.spec,position=[800,450],anchor=[0,0])
            frame=pygame.Surface((40,40),pygame.SRCALPHA); frame.fill(color)
            actor.clips={"idle":([frame],8,True)}
        field.draw(app.canvas,0,app.effects,app.ui.font(24))
        assert app.canvas.get_at((810,460))[:3]==(255,0,0)
        field.actors["player"].spec["render_order"]=0
        field.draw(app.canvas,0,app.effects,app.ui.font(24))
        assert app.canvas.get_at((810,460))[:3]==(0,255,0)
        # Impact transform must cover all pixels rather than leave stale borders.
        field.camera.impact(); field.camera.update(0.1)
        app.canvas.fill((255,0,255)); field.draw(app.canvas,0,app.effects,app.ui.font(24))
        assert app.canvas.get_at((0,0))[:3]!=(255,0,255)
    finally: pygame.quit()


def test_card_feedback_survives_update():
    app=App()
    try:
        app.action("start"); app.action("battle"); app.update(0.3); app.draw()
        click(app,(app.hand.views[0].pose.x,app.hand.views[0].pose.y))
        app.update(0.1)
        assert app.hand.ghost is not None and app.hand.ghost_age>0
        app.update(0.3); assert app.hand.ghost is None
    finally: pygame.quit()
