"""Exactly-once, nonblocking presentation timing; no combat rules live here."""
class ActionTimeline:
    def __init__(self):
        self.elapsed=0.0
        self.active=False
        self.resolved=False
        self.callback=None
        self.impact=0.0
        self.duration=0.0
        self.kind="attack"
        self.source="player"

    def start(self, kind, source, callback, timing=None):
        if self.active: return False
        self.kind=kind; self.source=source
        self.impact=0.34 if kind in ("heavy","special") else 0.22
        self.duration=self.impact+(0.42 if kind in ("heavy","special") else 0.30)
        if timing is not None:
            self.impact, self.duration = timing
        self.elapsed=0; self.resolved=False; self.active=True; self.callback=callback
        return True

    def update(self, dt):
        if not self.active: return
        self.elapsed+=max(0,dt)
        if not self.resolved and self.elapsed>=self.impact:
            self.resolved=True
            callback=self.callback; self.callback=None
            callback()
        if self.elapsed>=self.duration: self.active=False

    def cancel(self):
        self.active=False; self.callback=None

    @property
    def remaining(self):
        return max(0,self.duration-self.elapsed) if self.active else 0

    def offset(self):
        if not self.active: return (0,0)
        if self.kind not in ("attack","heavy","special"):
            import math
            return (0,-5*math.sin(math.pi*min(1,self.elapsed/self.duration)))
        t=self.elapsed; heavy=self.kind in ("heavy","special")
        windup=self.impact-0.08
        if t<windup: amount=-18*(t/windup)**2
        elif t<self.impact: amount=-18+(94 if heavy else 66)*((t-windup)/0.08)
        else: amount=(76 if heavy else 48)*max(0,1-(t-self.impact)/(self.duration-self.impact))**2
        direction=1 if self.source=="player" else -1
        return (direction*amount,-abs(amount)*0.12)
