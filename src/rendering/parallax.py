"""Manifest-based expanded PNG layers. All displacement is in source pixels."""
import json
import math
import warnings
import struct
import pygame
from src.core.resources import resource


class ParallaxBackground:
    def __init__(self, assets, config):
        path=resource(config["manifest"])
        self.manifest=json.loads(path.read_text(encoding="utf-8"))
        self.options=config.get("parallax",{})
        source=self.manifest["source"]
        original=source["original_size"]
        expanded=source["expanded_size"]
        self.scale=1600/original[0]
        if original[0]*900!=original[1]*1600: raise ValueError("Manifest view must be 16:9")
        self.size=tuple(round(v*self.scale) for v in expanded)
        self.inset=tuple(round(v*self.scale) for v in source["center_offset"])
        self.pivot=tuple(v*self.scale for v in self.manifest["parallax"]["zoom"]["center"])
        self.layers=[]
        for entry in [source["expanded_master"]]+[layer["file"] for layer in self.manifest["layers"]]:
            image_path=path.parent/entry
            if image_path.exists():
                with image_path.open("rb") as file: header=file.read(24)
                if header[:8]!=b"\x89PNG\r\n\x1a\n" or (entry!=source["expanded_master"] and struct.unpack(">II",header[16:24])!=tuple(expanded)):
                    raise ValueError(f"{entry}: expected aligned PNG canvas {expanded}")
        self.master=assets.image(str(path.parent/source["expanded_master"]),self.size)
        if self.master is not None: self.master=self.master.convert()
        by_file={layer["file"]:layer for layer in self.manifest["layers"]}
        order=self.manifest.get("render_order",[layer["file"] for layer in sorted(by_file.values(),key=lambda l:l["z_index"])])
        self.complete=True
        for name in order:
            layer=dict(by_file[name])
            layer.update(self.options.get("layers",{}).get(layer["name"],{}))
            frame=assets.image(str(path.parent/name),self.size)
            if frame is not None and layer.get("alpha")=="opaque": frame=frame.convert()
            self.complete=self.complete and frame is not None
            self.layers.append((layer,frame))
        if not self.complete: warnings.warn("Missing parallax layer; using expanded master for this stage")
        self.actor_factor=next(layer["parallax_factor"] for layer,_ in self.layers if layer["name"]==self.options.get("actor_layer","ground"))
        self.enabled=self.options.get("enabled",True)
        self.compare=False
        self.shift=(0.0,0.0)
        self.composites={}

    def layer_offset(self,layer):
        factor=layer["parallax_factor"] if self.enabled and not self.compare else self.actor_factor
        return tuple((self.shift[i]*factor[axis]+layer.get("default_position",[0,0])[i])*self.scale for i,axis in enumerate(("x","y")))

    @property
    def actor_offset(self):
        return tuple(self.inset[i]+self.shift[i]*self.actor_factor[axis]*self.scale for i,axis in enumerate(("x","y")))

    def draw(self,surface,time=0,foreground=False,shake=(0,0)):
        origin=(0,0) if surface.get_size()==self.size else tuple(-v for v in self.inset)
        if not foreground: surface.fill((27,26,37))
        if self.compare or not self.complete:
            if not foreground and self.master:
                offset=tuple(self.shift[i]*self.actor_factor[axis]*self.scale for i,axis in enumerate(("x","y")))
                surface.blit(self.master,tuple(round(origin[i]+offset[i]) for i in range(2)))
            return
        layers=[(layer,frame) for layer,frame in self.layers
                if (layer["name"] in self.options.get("foreground_layers",["foreground"]))==foreground and frame is not None]
        positions=tuple(tuple(round(v) for v in self.layer_offset(layer)) for layer,_ in layers)
        cached=self.composites.get(foreground)
        if cached is None or cached[0]!=positions:
            composite=cached[1] if cached is not None else pygame.Surface(self.size,pygame.SRCALPHA if foreground else 0)
            composite.fill((0,0,0,0) if foreground else (27,26,37))
            for (_,frame),position in zip(layers,positions): composite.blit(frame,position)
            self.composites[foreground]=(positions,composite)
        surface.blit(self.composites[foreground][1],origin)



class ParallaxCamera:
    def __init__(self, background, config):
        self.background=background
        settings=background.manifest["parallax"]
        self.options=background.options
        self.limits=self.options.get("max_offset_px",settings["max_offset_px"])
        self.jitter=self.options.get("max_jitter",settings["camera_shake"]["max_jitter"])
        self.zoom_range=self.options.get("zoom_range",settings["zoom"]["range"])
        self.base_zoom=max(self.zoom_range[0],min(self.zoom_range[1],config.get("zoom",1.0)))
        self.target_zoom=self.base_zoom
        self.current_zoom=self.base_zoom
        self.impact_zoom=self.options.get("impact_zoom",config.get("impact_zoom",0.035))
        self.target=[0.0,0.0]; self.pan=[0.0,0.0]
        self.clock=0.0; self.remaining=0.0; self.strength=1.0
        self.buffer=None
        self.debug=False
        # Respect overscan even if artists increase the requested pan range.
        safe={}
        for i,axis in enumerate(("x","y")):
            pivot=background.pivot[i]; inset=background.inset[i]; view=(1600,900)[i]
            left=pivot+(inset-pivot)/self.zoom_range[0]
            right=pivot+(inset+view-pivot)/self.zoom_range[0]
            margin=min(left,background.size[i]-right)
            factor=max(abs(layer["parallax_factor"][axis]) for layer,_ in background.layers)
            offsets=max(abs(layer.get("default_position",[0,0])[i]) for layer,_ in background.layers)
            safe[axis]=max(0,margin/background.scale/max(factor,0.001)-self.jitter-offsets-2)
        self.limits={axis:min(abs(self.limits[axis]),safe[axis]) for axis in ("x","y")}

    def impact(self,strength=1.0):
        self.remaining=0.28; self.strength=strength

    def reset(self):
        self.target=[0.0,0.0]; self.pan=[0.0,0.0]
        self.current_zoom=self.target_zoom=self.base_zoom
        self.remaining=0.0; self.background.shift=(0,0)

    def debug_key(self,key):
        if not self.options.get("debug_controls",False): return False
        if key==pygame.K_F1: self.debug=not self.debug; return True
        if not self.debug: return False
        if key==pygame.K_F2: self.background.enabled=not self.background.enabled
        elif key==pygame.K_F3: self.background.compare=not self.background.compare
        elif key==pygame.K_F4: self.impact()
        elif key==pygame.K_F5:
            self.target_zoom=self.zoom_range[0] if self.target_zoom==self.base_zoom else self.zoom_range[1] if self.target_zoom==self.zoom_range[0] else self.base_zoom
        elif key==pygame.K_HOME: self.reset()
        elif key in (pygame.K_LEFT,pygame.K_RIGHT): self.target[0]=self.limits["x"]*(-1 if key==pygame.K_LEFT else 1)
        elif key in (pygame.K_UP,pygame.K_DOWN): self.target[1]=self.limits["y"]*(-1 if key==pygame.K_UP else 1)
        else: return False
        return True

    def update(self,dt):
        self.clock+=dt; self.remaining=max(0,self.remaining-dt)
        ease=1-math.exp(-self.options.get("smoothing",9)*dt)
        for i,axis in enumerate(("x","y")):
            goal=max(-self.limits[axis],min(self.limits[axis],self.target[i]))
            self.pan[i]+=(goal-self.pan[i])*ease
        self.current_zoom+=(self.target_zoom-self.current_zoom)*ease
        decay=self.remaining/0.28
        shift=[]
        for i,axis in enumerate(("x","y")):
            kick=math.sin(math.pi*decay)*self.options.get("impact_pan",8)*(1 if i==0 else 0.35)
            shake=math.sin(self.clock*(95 if i==0 else 81))*min(self.jitter,self.jitter*self.strength)*decay
            shift.append(max(-self.limits[axis]-self.jitter,min(self.limits[axis]+self.jitter,self.pan[i]+kick+shake)))
        self.background.shift=tuple(shift)

    @property
    def zoom(self):
        return max(self.zoom_range[0],min(self.zoom_range[1],self.current_zoom+self.impact_zoom*self.strength*math.sin(math.pi*self.remaining/0.28)))

    def present(self,world,destination):
        # Zoom the overscanned composite, not the already cropped viewport.
        zoom=round(self.zoom*200)/200
        size=tuple(round(v*zoom) for v in world.get_size())
        if zoom==1: frame=world
        else:
            flags=world.get_flags() & pygame.SRCALPHA
            if self.buffer is None or self.buffer.get_size()!=size or (self.buffer.get_flags() & pygame.SRCALPHA)!=flags:
                self.buffer=pygame.Surface(size,flags)
            pygame.transform.smoothscale(world,size,self.buffer)
            frame=self.buffer
        pivot=self.background.pivot; inset=self.background.inset
        position=tuple(round(pivot[i]*(1-zoom)-inset[i]) for i in range(2))
        destination.blit(frame,position)
