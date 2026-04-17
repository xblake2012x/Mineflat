import pygame

pygame.init()

screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption('Key Name Example')

font = pygame.font.Font(None, 32)

running = True
while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.KEYDOWN:
      # Get the name of the pressed key
      key_name = pygame.key.name(event.key)
      print(f"{key_name}:{pygame.key.key_code(key_name)}")

pygame.quit()
