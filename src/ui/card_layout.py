"""Pure fan geometry and inverse-transform hit testing in logical pixels."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class FanConfig:
    width: int = 170
    height: int = 248
    center_x: float = 800
    base_y: float = 758
    spacing: float = 158
    max_width: float = 710
    arc: float = 14
    angle: float = 7
    hover_lift: float = 32
    hover_scale: float = 1.06
    speed: float = 14

@dataclass
class Pose:
    x: float
    y: float
    angle: float = 0
    scale: float = 1

    def toward(self, target, dt, speed):
        t = 1-math.exp(-speed*max(0,dt))
        for key in ("x","y","angle","scale"):
            setattr(self,key,getattr(self,key)+(getattr(target,key)-getattr(self,key))*t)


def fan_layout(count: int, config=FanConfig()) -> list[Pose]:
    spacing = min(config.spacing, config.max_width/max(count-1,1))
    half = (count-1)/2
    arc = config.arc * min(1.25, max(0, count-1)/2)
    angle = config.angle * min(1.25, max(0, count-1)/2)
    poses=[]
    for i in range(count):
        offset=i-half
        normalized=offset/max(half,1)
        poses.append(Pose(config.center_x+offset*spacing,
                          config.base_y-arc*(1-normalized**2),
                          -normalized*angle))
    return poses


def card_contains(point, pose: Pose, config=FanConfig()) -> bool:
    # Inverse of Pygame's counterclockwise image rotation, including scale.
    dx,dy=point[0]-pose.x,point[1]-pose.y
    angle=math.radians(pose.angle)
    x=(math.cos(angle)*dx-math.sin(angle)*dy)/pose.scale+config.width/2
    y=(math.sin(angle)*dx+math.cos(angle)*dy)/pose.scale+config.height/2
    if not (0<=x<config.width and 0<=y<config.height): return False
    # Match the rounded visible card corners; shadows do not accept clicks.
    radius=8
    cx=max(radius,min(config.width-radius,x))
    cy=max(radius,min(config.height-radius,y))
    return (x-cx)**2+(y-cy)**2<=radius**2
