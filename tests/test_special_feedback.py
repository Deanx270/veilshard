from types import SimpleNamespace
import pytest
from src.core.app import App
from src.core.resources import read_data
from src.rendering.action_timeline import ActionTimeline
from src.rendering.battlefield import Battlefield
from src.rendering.effects import Effects


@pytest.mark.parametrize("kind,heavy",[("attack",False),("special",False),("heavy",True)])
def test_stormcaller_special_normal_impact_keeps_clip_timing(kind,heavy):
    app=App.__new__(App)
    app.campaign=SimpleNamespace(stage=read_data("stages")[2])
    app.effects=Effects();app.timeline=ActionTimeline();app.pending_card=None
    app.actors_busy_time=lambda:0
    field=Battlefield.__new__(Battlefield);field.reactions={}
    triggered=[];strength=[];clips=[]
    field.actors={"player":SimpleNamespace(clips={"hit":1,"hit_heavy":1},trigger=triggered.append),
                  "opponent":SimpleNamespace(clips={"attack":1,"special":1,"heavy":1},trigger=clips.append,action_timing=lambda clip:(.7,1.1))}
    field.camera=SimpleNamespace(impact=lambda value,**kwargs:strength.append(value))
    app.battlefield=field
    calls=[]
    effect=SimpleNamespace(kind="damage",target="player",amount=6)
    def resolve():
        calls.append(1)
        return [effect]
    app.begin_action(kind,"opponent",resolve)
    assert clips==[kind] and app.timeline.impact==.7
    app.timeline.update(.69)
    assert not calls
    app.timeline.update(.02);app.timeline.update(2)
    assert calls==[1]
    assert triggered==["hit_heavy" if heavy else "hit"]
    assert app.effects.popups[0].bold is heavy
    assert strength==[2.3 if heavy else 1.2]
    assert field.reactions["player"][1]==(36 if heavy else 19)
