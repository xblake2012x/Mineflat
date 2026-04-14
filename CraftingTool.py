import pygame
import json
import os
import re

# Initialize PyGame
pygame.init()

# Set up the screen (width, height)
clock = pygame.time.Clock()
screen = pygame.display.set_mode((815, 600), pygame.RESIZABLE)
pygame.display.set_caption("Crafting Tool")

# Set up variables
Crafting_Type = "shaped"
Crafting_Table = [['' for i in range(3)] for ii in range(3)]
Current_Item = None
Item_Width = 50
Item_Height = 50
Key = {}
Used_blocks = []
Output_Item = ''
scroll_offset = 0
scroll_speed = 20  # pixels per scroll
Output_Count = 1


with open("Assets/Storage/Blocks.json") as f:
    Textures = json.load(f)

def get_block_folder(block_name):
    if 'concrete' in block_name:
        if 'powder' in block_name:
            return 'concrete/powder'
        return 'concrete'
    elif 'terracotta' in block_name:
        if 'glazed' in block_name:
            return 'terracotta/glazed'
        return 'terracotta'
    elif 'water'  in block_name:
        return 'Liquids/water'
    elif 'carpet' in block_name:
        return 'carpet'
    elif 'door' in block_name:
        return 'doors'
    elif 'glass' in block_name:
        return 'glass'
    elif 'wool' in block_name:
        return 'wool'
    else:
        return ''

Textures2 = {
    None: pygame.image.load("Assets/Images/Blocks/air.png").convert_alpha(),
    '': pygame.image.load("Assets/Images/Blocks/air.png").convert_alpha(),
    'Missing_Block': pygame.image.load("Assets/Images/Blocks/Missing_block.png").convert_alpha()
}

Items = []

for block in Textures["Blocks"]:
    folder = get_block_folder(block)
    path = f"Assets/Images/Blocks/{folder}/{block}.png" if folder else f"Assets/Images/Blocks/{block}.png"
    try:
        image = pygame.image.load(path).convert_alpha()
        if not 'carpet' in block:
            scaled_image = pygame.transform.scale(image, (Item_Width, Item_Height))
        else:
            scaled_image = pygame.transform.scale(image, (Item_Width, Item_Height / 10))
        Textures2[block] = scaled_image
        Items.append(block)
    except Exception as e:
        print(f"Missing or broken texture for {block} at {path}")

for item in Textures["Items"]:
    path = f"Assets/Images/Items/{item}.png"
    try:
        image = pygame.image.load(path).convert_alpha()
        scaled_image = pygame.transform.scale(image, (Item_Width, Item_Height))
        Textures2[item] = scaled_image
        Items.append(item)
    except Exception as e:
        print(f"Missing or broken texture for {item} at {path}")
Textures = Textures2

class Button:
    def __init__(self, rect, color, hover_color, font, text,extra, left = None,right = None, draw = None):
        self.button_rect = rect
        self.button_color = color
        self.hover_color = hover_color
        self.font = font
        self.text = text
        self.left = left
        self.right = right
        self.extra = extra
        self.draw_function = draw

    def left_click(self):
        if self.left is not None:
            self.left(self)

    def right_click(self):
        if self.right is not None:
            self.right(self)

    def draw(self,mouse_pos):
        if self.draw_function is None:
            if self.button_rect.collidepoint(mouse_pos):
                color = button.hover_color
            else:
                color = button.button_color
            pygame.draw.rect(screen, color, self.button_rect)
            text_rect = self.text.get_rect(center=self.button_rect.center)
            screen.blit(self.text, text_rect)
        else:
            self.draw_function(button,mouse_pos)

def draw_slot(button,mouse_pos):
    row, col = button.extra
    if button.button_rect.collidepoint(mouse_pos):
        color = button.hover_color
    else:
        color = button.button_color
    pygame.draw.rect(screen, color, button.button_rect)
    text_rect = button.text.get_rect(center=button.button_rect.center)
    screen.blit(button.text, text_rect)
    image = Textures[Crafting_Table[row][col]]
    target_rect = pygame.Rect(button.button_rect[0],button.button_rect[1], 75, 75)
    image_rect = image.get_rect(center=target_rect.center)
    screen.blit(image, image_rect)

def ChangeType(button):
    global Crafting_Type
    if Crafting_Type == "shaped":
        button.text = button.font.render("Shapeless", True, (0, 0, 0))
        Crafting_Type = "shapeless"
    elif Crafting_Type == "shapeless":
        button.text = button.font.render("Shaped", True, (0, 0, 0))
        Crafting_Type = "shaped"

def CraftingSlot(button):
    row, col = button.extra

    if Current_Item is not None:
        Crafting_Table[row][col] = Current_Item

        if Current_Item not in Used_blocks:
            Used_blocks.append(Current_Item)
            new_key = 1
            for i in range(9):
                if not i in Key:
                    new_key = i
                    break
            Key[new_key] = {"item": Current_Item}

    crafting_view = [item for row_items in Crafting_Table for item in row_items]

    keys_to_remove = [k for k, v in Key.items() if v['item'] not in crafting_view]
    for k in keys_to_remove:
        Key.pop(k)

def DeleteSlot(button):
    row, col = button.extra
    Item = Crafting_Table[row][col]
    Crafting_Table[row][col] = ''
    crafting_view = [item for row_items in Crafting_Table for item in row_items]
    keys_to_remove = [k for k, v in Key.items() if v['item'] not in crafting_view]
    for k in keys_to_remove:
        Key.pop(k)

def SetOutput(button):
    global Output_Item
    if Current_Item is not None:
        Output_Item = Current_Item

def RemoveOutput(button):
    global Output_Item
    Output_Item = ''

def DrawOutput(button,mouse_pos):
    if button.button_rect.collidepoint(mouse_pos):
        color = button.hover_color
    else:
        color = button.button_color
    pygame.draw.rect(screen, color, button.button_rect)
    text_rect = button.text.get_rect(center=button.button_rect.center)
    screen.blit(button.text, text_rect)
    image = Textures[Output_Item]
    target_rect = pygame.Rect(button.button_rect[0],button.button_rect[1], 75, 75)
    image_rect = image.get_rect(center=target_rect.center)
    screen.blit(image, image_rect)

    count_text = font.render(f"x{Output_Count}", True, (255, 255, 255))
    screen.blit(count_text, (button.button_rect.x + 5, button.button_rect.y + 5))


def IncreaseCount():
    global Output_Count
    Output_Count += 1

def DecreaseCount():
    global Output_Count
    if Output_Count > 1:
        Output_Count -= 1


def SaveJson(button):
    global Output_Item, Crafting_Table, Crafting_Type

    # Dynamically build the key from the current crafting grid
    Key = {}
    item_to_key = {}
    key_index = 0

    for row in Crafting_Table:
        for item in row:
            if item and item not in item_to_key:
                item_to_key[item] = str(key_index)
                Key[key_index] = {"item": item}
                key_index += 1

    # Build pattern rows
    pattern = []
    for row in Crafting_Table:
        pattern_row = ''.join(item_to_key.get(item, '_') for item in row)
        pattern.append(pattern_row)

    # Build final recipe
    recipe = {
        "type": Crafting_Type,
        "pattern": pattern,
        "key": Key,
        "result": {"item": Output_Item, "count": Output_Count}
    }

    # Optional: save to file
    folder_path = 'Assets/Crafting/'

    amount = 0

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            filename_no_number = re.sub(r'\d', '', filename)
            if filename_no_number == f"{Output_Item}.json":
                amount += 1

    with open(f"Assets/Crafting/{Output_Item}{amount if amount > 0 else ''}.json", "w") as f:
        json.dump(recipe, f, indent=4)
    print("Recipe saved:", recipe)


Buttons = []
font = pygame.font.SysFont(None, 36)
Buttons.append(Button(pygame.Rect(25, 25, 200, 60),(255, 255, 0),(255, 200, 0),font,font.render("Shaped", True, (0, 0, 0)),None,ChangeType))
Buttons.append(Button(pygame.Rect(25, screen.get_height() - 85, 200, 60),(255, 255, 0),(255, 200, 0),font,font.render("Save JSON", True, (0, 0, 0)),None,SaveJson))
Buttons.append(Button(pygame.Rect(400,200,75,75),(100,100,100),(150,150,150),font,font.render("", True, (0, 0, 0)),None,SetOutput,RemoveOutput,DrawOutput))
Buttons.append(Button(pygame.Rect(400, 290, 35, 35), (200, 200, 200), (255, 255, 255), font, font.render("+", True, (0, 0, 0)), None, lambda b: IncreaseCount()))
Buttons.append(Button(pygame.Rect(440, 290, 35, 35), (200, 200, 200), (255, 255, 255), font, font.render("-", True, (0, 0, 0)), None, lambda b: DecreaseCount()))

for row in range(3):
    for col in range(3):
        Buttons.append(Button(pygame.Rect(100 * (col + 0.5), 100 * (row + 1), 75, 75),(100,100,100),(150,150,150),font,font.render("", True, (0, 0, 0)),(row,col),CraftingSlot,DeleteSlot,draw_slot))

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()

    LeftClick = False
    RightClick = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                LeftClick = True
            if event.button == 3:
                RightClick = True
        if event.type == pygame.MOUSEWHEEL:
            scroll_offset -= event.y * scroll_speed
            scroll_offset = max(0, scroll_offset)  # Prevent scrolling above top
            max_scroll = max(0, y + Item_Height - screen.get_height())
            scroll_offset = min(scroll_offset, max_scroll)

    screen.fill((0, 100, 255))
    for button in Buttons:
        button_rect = button.button_rect

        if button_rect.collidepoint(mouse_pos):
            color = button.hover_color
            if LeftClick:
                button.left_click()
            if RightClick:
                button.right_click()
        else:
            color = button.button_color

        button.draw(mouse_pos)
    try:
        s = pygame.Surface((screen.get_width() - 535,screen.get_height()), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        screen.blit(s,(535,0))
    except pygame.error:
        pass
    y = 0
    amt_done = -1
    for i, item in enumerate(Items):
        amt_done += 1
        x = 535 + 75 * amt_done + 5
        if x + Item_Width > screen.get_width():
            y += 75
            amt_done = 0
            x = 535 + 75 * amt_done + 5
        screen.blit(Textures[item], (x, y - scroll_offset))
        item_rect = pygame.Rect(x, y - scroll_offset, Item_Width, Item_Height)
        if Current_Item == item:
            pygame.draw.rect(screen,(255,255,255),(x - 2.5, y - 2.5 - scroll_offset, 55, 55),5)
        if item_rect.collidepoint(mouse_pos) and LeftClick:
            Current_Item = item
            print(f'Switched selected item to {item}')

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
