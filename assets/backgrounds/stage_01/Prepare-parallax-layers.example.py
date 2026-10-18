layers = [
  (pygame.image.load("sky.png").convert_alpha(), 0.05),
  (pygame.image.load("distant.png").convert_alpha(), 0.20),
  (pygame.image.load("ground.png").convert_alpha(), 0.50),
  (pygame.image.load("midground.png").convert_alpha(), 0.80),
  (pygame.image.load("foreground.png").convert_alpha(), 1.15),
]
# offset = camera pan
# for img, factor in layers: screen.blit(img, (offset.x*factor, offset.y*factor))