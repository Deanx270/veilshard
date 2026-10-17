import pygame

SIZE = (1600, 900)

def viewport(window_size):
    scale = min(window_size[0] / SIZE[0], window_size[1] / SIZE[1])
    width, height = max(1, round(SIZE[0] * scale)), max(1, round(SIZE[1] * scale))
    return pygame.Rect((window_size[0]-width)//2, (window_size[1]-height)//2, width, height)

def logical_mouse(position, window_size):
    area = viewport(window_size)
    if not area.collidepoint(position):
        return (-1, -1)
    return ((position[0]-area.x)*SIZE[0]/area.width, (position[1]-area.y)*SIZE[1]/area.height)
