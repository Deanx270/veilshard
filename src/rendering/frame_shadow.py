"""Small cached ground projections of frame alpha; no runtime pixel analysis."""
import math
import pygame


class FrameShadows:
    def __init__(self, frames, config):
        self.config = config
        self.cache = {}
        shared = {}
        for frame in frames:
            if id(frame) not in self.cache:
                if config.get("mode") == "contact":
                    size = frame.get_size()
                    if size not in shared: shared[size] = self.build_contact(frame)
                    self.cache[id(frame)] = shared[size]
                else:
                    self.cache[id(frame)] = self.build(frame)

    def build_contact(self, frame):
        """One feathered contact patch per canvas size, independent of the pose."""
        w, h = frame.get_size()
        small = pygame.Surface((64, 32), pygame.SRCALPHA)
        for y in range(32):
            for x in range(64):
                radius = ((x-31.5)/31.5)**2 + ((y-15.5)/15.5)**2
                alpha = round(255*max(0, 1-radius)**2)
                small.set_at((x,y), (8,10,18,alpha))
        size = (max(1, round(w*.11*self.config.get("width",1))),
                max(1, round(h*.3*self.config.get("depth",.18))))
        shadow = pygame.transform.smoothscale(small,size)
        angle = self.config.get("angle",0)
        if angle: shadow = pygame.transform.rotate(shadow,angle)
        ground = self.config.get("ground",[.5,1])
        return shadow, (round(w*ground[0]-shadow.get_width()/2),
                        round(h*ground[1]-shadow.get_height()/2))

    def build(self, frame):
        w, h = frame.get_size()
        crop = self.config.get("crop", [0, 0, 1, 1])
        rect = pygame.Rect(round(crop[0]*w), round(crop[1]*h), max(1, round(crop[2]*w)), max(1, round(crop[3]*h))).clip(frame.get_rect())
        if not rect.width or not rect.height:
            return pygame.Surface((1, 1), pygame.SRCALPHA), (0, 0)
        if self.config.get("foot_locked", False):
            return self.build_grounded(frame, rect)
        # Downsampling softens the outline and bounds processing cost.
        mask = pygame.transform.smoothscale(frame.subsurface(rect), (96, 96))
        mask.fill((8, 10, 18, 255), special_flags=pygame.BLEND_RGBA_MULT)
        width = self.config.get("width", 1.0)
        depth = self.config.get("depth", .18)
        size = (max(1, round(rect.width*width)), max(1, round(rect.height*depth)))
        shadow = pygame.transform.smoothscale(mask, size)
        ground = self.config.get("ground", [.5, 1.0])
        # Pin the bottom of the source silhouette to the ground, extending away.
        origin = (round(ground[0]*w+(rect.x-ground[0]*w)*width),
                  round(ground[1]*h-(rect.bottom-ground[1]*h)*depth-size[1]))
        angle = self.config.get("angle", 0)
        if angle:
            # Rotate about the ground contact, not the image center.
            pivot = pygame.Vector2(ground[0]*w, ground[1]*h)
            center = pygame.Vector2(origin) + pygame.Vector2(size)/2
            center = pivot + (center-pivot).rotate(-angle)
            shadow = pygame.transform.rotate(shadow, angle)
            origin = (round(center.x-shadow.get_width()/2), round(center.y-shadow.get_height()/2))
        return shadow, origin

    def build_grounded(self, frame, rect):
        # Inspect only the lower character region, excluding distant spell VFX.
        band = pygame.Rect(rect.x, rect.y+round(rect.height*.80), rect.width,
                           max(1, round(rect.height*.20))).clip(rect)
        feet = frame.subsurface(band).get_bounding_rect(min_alpha=128).move(band.topleft)
        ground_y = feet.bottom if feet.width else rect.bottom
        ground_x = feet.centerx if feet.width else rect.centerx
        # Project away from the feet using shear, rather than rotating the entire
        # cutout (which lifts one foot off the contact line).
        mask = pygame.transform.smoothscale(frame.subsurface(rect), (96,96))
        mask.fill((8,10,18,255), special_flags=pygame.BLEND_RGBA_MULT)
        angle = math.radians(self.config.get("angle",0))
        depth = self.config.get("depth",.18)
        vertical = math.cos(angle)
        if abs(vertical)<.15: vertical = .15 if vertical>=0 else -.15
        width = self.config.get("width",1)
        strips = []
        for row in range(96):
            source_y = rect.y+(row+.5)*rect.height/96
            height = max(0,ground_y-source_y)
            blend = min(1,height/max(1,rect.height*.3))
            spread = 1+(width-1)*blend
            strip_width = max(1,round(rect.width*spread))
            strip_height = max(1,math.ceil(rect.height/96*depth*abs(vertical)))
            x = round(ground_x+(rect.x-ground_x)*spread+height*depth*math.sin(angle))
            y = round(ground_y-height*depth*vertical)
            strips.append((row,pygame.Rect(x,y,strip_width,strip_height)))
        bounds = strips[0][1].unionall([r for _,r in strips])
        shadow = pygame.Surface(bounds.size,pygame.SRCALPHA)
        for row, target in strips:
            strip = pygame.transform.smoothscale(mask.subsurface((0,row,96,1)),target.size)
            shadow.blit(strip,(target.x-bounds.x,target.y-bounds.y))
        # Soften small scanline boundaries once, never during playback.
        small = pygame.transform.smoothscale(shadow,(max(1,bounds.width//2),max(1,bounds.height//2)))
        shadow = pygame.transform.smoothscale(small,bounds.size)
        return shadow, bounds.topleft

    def draw(self, surface, frame, top_left):
        if not self.config.get("enabled", True): return
        cached = self.cache.get(id(frame))
        if cached is None: return  # Replaced clips need a cache rebuild, never per-draw work.
        shadow, origin = cached
        shadow.set_alpha(max(0, min(255, self.config.get("opacity", 55))))
        offset = self.config.get("offset", [0, 0])
        surface.blit(shadow, tuple(round(top_left[i]+origin[i]+offset[i]) for i in range(2)))
