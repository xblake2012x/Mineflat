import pygame
import sys
import time
import math
import os
import datetime
import json
import random
import threading
import noise
from noise import snoise2
import string
from Commands import *

def get_game_age():
    creation_date = datetime.datetime(2025, 8, 30)
    today = datetime.datetime.now()
    age = today - creation_date
    return age.days

print(f"Mineflat is {get_game_age()} days old.")


HP = 20
crouched = False

tick = 0
tick_end = 12000

test_mode = True
test_block = 'oak_log'

chat_input = ''

def check_required_folders():
    required_folders = [
        "Assets",
        "Mods",
        "Screenshots",
        "Logs",
        "Worlds"
    ]
    for folder in required_folders:
        if not os.path.exists(folder):
            log(f"⚠️ Missing folder: {folder}")
            os.makedirs(folder, exist_ok=True)
            log(f"📁 Created missing folder: {folder}")
        else:
            log(f"✅ Found folder: {folder}")

world_seed = None

with open('Assets/Storage/Settings.json') as f:
    setting = json.load(f)

keybind = setting["Keybinds"]

#make all the blocks, add here for more blocks in the inventory
all_blocks = [
    'grass', 'cobble_stone', 'stone', 'bricks', 'oak_planks', 'oak_log', 'dirt', 'oak_leaves', 'glass',
    'oak_door_bottom','oak_door_top','ladder', 'blue_concrete', 'black_concrete', 'brown_concrete', 'cyan_concrete', 'gray_concrete',
    'green_concrete', 'light_blue_concrete', 'light_gray_concrete',
    'lime_concrete', 'magenta_concrete', 'orange_concrete', 'pink_concrete', 'purple_concrete', 'red_concrete',
    'white_concrete', 'yellow_concrete', 'sand', 'gravel', 'water', 'flowing_water', 'glass', 'tinted_glass'
]

mob_drops = {
    'Pig': {
        'porkchop': 100
    },
    'Cow': {
        'leather': 80,
        'beef': 50
    },
    'Sheep': {
        'mutton': 100
    },
    'Zombie': {
        "stick": 50
    }
}

all_items = [
    'porkchop',
    'leather',
    'beef',
    'mutton',
    'wooden_sword',
    'wooden_axe',
    'wooden_pickaxe',
    'wooden_hoe',
    'wooden_shovel',
    'stone_sword',
    'stone_axe',
    'stone_pickaxe',
    'stone_hoe',
    'stone_shovel',
    'stick'
]

all_mobs = [
    'Pig',
    'Cow',
    'Sheep',
    'Zombie'
]

colors = [
    'white', 'orange', 'magenta', 'light_blue', 'yellow', 'lime', 'pink',
    'gray', 'light_gray', 'cyan', 'purple', 'blue', 'brown', 'green', 'red', 'black'
]

all_blocks.extend(f"{color}_stained_glass" for color in colors)
all_blocks.extend(f"{color}_wool" for color in colors)
all_blocks.extend(f"{color}_concrete_powder" for color in colors)
all_blocks.extend(f"{color}_glazed_terracotta" for color in colors)
all_blocks.extend(f"{color}_terracotta" for color in colors)
all_blocks.extend(f"{color}_carpet" for color in colors)

print(all_blocks)

print(f'There are {len(all_blocks)} blocks in MINEFLAT')

remove_blocks = ['oak_door_top','flowing_water']
climbable_blocks = ['ladder']
flowing_water_chunks = {}

base_path = os.path.dirname(sys.executable if hasattr(sys, 'frozen') else __file__)
print_log_making_log = False
if not os.path.exists(f'{os.path.join(base_path, "Logs")}'):
   print_log_making_log= True
logs_path = os.path.join(os.path.dirname(sys.executable if hasattr(sys, 'frozen') else __file__), "Logs")
os.makedirs(logs_path, exist_ok=True)

logs = []

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

log_file = os.path.join(base_path, "Logs", f'Log_{timestamp}.txt')

CHUNK_SIZE = 16  # blocks per chunk
chunk_lookup = {}

def get_chunk_coords(x, y):
    block_x = x // block_size
    block_y = y // block_size
    return (block_x // CHUNK_SIZE, block_y // CHUNK_SIZE)

def get_chunk(x, y):
    block_x = x // block_size
    block_y = y // block_size
    chunk_x = block_x // CHUNK_SIZE
    chunk_y = block_y // CHUNK_SIZE
    chunk_pos = (chunk_x, chunk_y)

    # 🛡️ If chunk doesn't exist or is None, generate it
    if chunk_pos not in chunk_lookup or chunk_lookup[chunk_pos] is None:
        chunk_lookup[chunk_pos] = generate_chunk(chunk_x, chunk_y)

    return chunk_lookup[chunk_pos]


def log(message):
    global logs
    time = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{time}] {message}"
    logs.append(entry)
    print(entry)  # Optional: show in console
    with open(log_file, "w") as f:
        for line in logs:
            f.write(line + "\n")

def hurt_player(damage):
    global HP, player_start_hit
    start_hp = HP
    HP -= damage
    if HP != start_hp:
        player_start_hit = time.time()
    print(f'HIT {start_hp} to {HP}')

check_required_folders()

log('Attempting to start Mine Flat')
if not os.path.exists('Screenshots/'):
    log(f'Making Screenshots folder')
screenshots_path = os.path.join(os.path.dirname(sys.executable if hasattr(sys, 'frozen') else __file__), "Screenshots")
os.makedirs(screenshots_path, exist_ok=True)
if print_log_making_log:
    log(f'Making Logs folder')


# Initialize PyGame
pygame.init()

# Set up the screen (width, height)
log('Setting up window')
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("MineFlat Indev")
player_x = 0
player_y = 0
player_start_hit = None
player_width = 50
player_height_base = 100
player_height = player_height_base
player_height_crouch = 75
jump = False
walked = False
clicked = None
player_y_vel = 0
block_size = 50
latestmsg = 0
invscroll = 0

log('Setting up world')

music_tracks = ['Assets/Sound/BG_music/sweden.ogg','Assets/Sound/BG_music/Minecraft.ogg','Assets/Sound/BG_music/Wet_Hands.ogg']

def play_music_loop():
    time.sleep(30)
    track = random.choice(music_tracks)
    pygame.mixer.music.load(track)
    pygame.mixer.music.play()

    # Wait for track to finish
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    while True:
        time.sleep(300)
        track = random.choice(music_tracks)
        pygame.mixer.music.load(track)
        pygame.mixer.music.play()

        # Wait for track to finish
        while pygame.mixer.music.get_busy():
            time.sleep(1)

def count_json_files(folder_path):
    return sum(
        1 for file in os.listdir(folder_path)
        if file.endswith(".json") and
        not file.startswith("Deafualt_World")
    )

worlds = count_json_files('Worlds/')

world_options = [file for file in os.listdir("Worlds/")
           if file.endswith(".json") and
           not file.startswith("Deafualt_World")
           ]

world_options_filenames = [file for file in os.listdir("Worlds/")
           if file.endswith(".json") and
           not file.startswith("Deafualt_World")
           ]

# --- AESTHETIC CONSTANTS ---
BUTTON_COLOR_NORMAL = (50, 50, 50)
BUTTON_COLOR_HOVER = (80, 80, 80)
TEXT_COLOR_NORMAL = (200, 200, 200)
TEXT_COLOR_TITLE = (30, 30, 30)
TEXT_COLOR_SPLASH = (255, 215, 0)
BUTTON_HEIGHT = 80
BUTTON_SPACING = 30
SCROLL_SPEED = 0.5
BLOCK_SIZE = block_size

# --- MENU STATE SETUP (Retained Globals) ---
play = False  # False: Main Menu | True: World Selection
settings = False
out = False
loaded_world = "Deafualt_World.json"
scroll = 0  # Vertical scroll for worlds (retained for long lists)
options = ['Play', 'Settings', 'Quit']
# world_options and world_options_filenames must be defined globally

def load_texture(path):
    return pygame.image.load(path).convert_alpha()

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

log('Cacheing textures')
try:
    block_textures = {
        None: pygame.image.load("Assets/Images/Blocks/air.png").convert_alpha(),
        '': pygame.image.load("Assets/Images/Blocks/air.png").convert_alpha(),
        'Missing_Block': pygame.image.load("Assets/Images/Blocks/Missing_block.png").convert_alpha()
    }

    ui_textures = {
        "heart_full": pygame.image.load("Assets/Images/Ui/full.png").convert_alpha(),
        'heart_half': pygame.image.load("Assets/Images/Ui/half.png").convert_alpha(),
        'heart_empty': pygame.image.load("Assets/Images/Ui/empty.png").convert_alpha()
    }

    mob_textures = {

    }

    item_textures = {

    }

    all_textures = {

    }

    for block in all_blocks:
        folder = get_block_folder(block)
        path = f"Assets/Images/Blocks/{folder}/{block}.png" if folder else f"Assets/Images/Blocks/{block}.png"
        try:
            image = pygame.image.load(path).convert_alpha()
            if not 'carpet' in block:
                scaled_image = pygame.transform.scale(image, (50, 50))
            else:
                scaled_image = pygame.transform.scale(image, (50, 5))
            block_textures[block] = scaled_image
            all_textures[block] = scaled_image
        except Exception as e:
            log(f"Missing or broken texture for {block} at {path}")

    for mob in all_mobs:
        path = f"Assets/Images/Mobs/{mob}.png"
        try:
            image = pygame.image.load(path).convert_alpha()
            scaled_image = pygame.transform.scale(image, (50, 50))
            mob_textures[mob] = scaled_image
            all_textures[mob] = scaled_image
        except Exception as e:
            log(f"Missing or broken texture for {mob} at {path}")

    for item in all_items:
        path = f"Assets/Images/Items/{item}.png"
        try:
            image = pygame.image.load(path).convert_alpha()
            scaled_image = pygame.transform.scale(image, (50, 50))
            item_textures[item] = scaled_image
            all_textures[item] = scaled_image
            block_textures[item] = scaled_image
        except Exception as e:
            log(f"Missing or broken texture for {item} at {path}")

    for i,name in enumerate(ui_textures):
        scaled_image = pygame.transform.scale(ui_textures[name], (30, 30))
        ui_textures[name] = scaled_image
        all_textures[name] = scaled_image

    for i in range(10):
        try:
            name = f"destroy_stage_{i}"
            path = f"Assets/Images/Ui/{name}.png"
            image = pygame.image.load(path).convert_alpha()
            scaled_image = pygame.transform.scale(image, (50, 50))
            all_textures[name] = scaled_image
            ui_textures[name] = scaled_image
        except Exception as e:
            log(f"Missing or broken texture for {name} at {path}")
    player_torso_texture = pygame.image.load("Assets/Images/Player/Body.png").convert_alpha()
    player_legs_texture = pygame.image.load("Assets/Images/Player/leg.png").convert_alpha()
    player_head_right_texture = pygame.image.load("Assets/Images/Player/Right.png").convert_alpha()
    player_head_left_texture = pygame.image.load("Assets/Images/Player/Left.png").convert_alpha()
    player_arm_texture = pygame.image.load("Assets/Images/Player/Arm.png").convert_alpha()
except FileNotFoundError as e:
    block = str(e).split('.png')[0]
    block = block.split('/')[-1]
    path = str(e).split(f'{block}.png')[0]
    path = path.split(f'\'')[1]
    path = path[:-1]
    log(f'CRASHED CRASHED\nCan\'t find file {block}.png in the in directory {path}')
    os.chdir(os.path.dirname(__file__))
    os.makedirs('Logs', exist_ok=True)
    os.chdir(f'{os.path.dirname(__file__)}/Logs')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    pygame.quit()
    sys.exit()

log('loading recipes')
crafting_recipes = []
for filename in os.listdir("Assets/Crafting"):
    full_path = os.path.join("Assets/Crafting", filename)
    with open(full_path, "r") as file:
        data = json.load(file)
        crafting_recipes.append(data)

# --- MENU STATE SETUP (Retained Globals) ---
play = False  # False: Main Menu | True: World Selection
settings = False
keybinds = False
out = False
rebinding_action = None  # Currently selected action to rebind
loaded_world = "Deafualt_World.json"
scroll = 0  # Vertical scroll for worlds (retained for long lists)
options = ['Play', 'Settings', 'Quit']
# world_options and world_options_filenames must be defined globally

# --- MENU INITIALIZATION (CRITICAL PERFORMANCE FIX) ---
# 1. Initialize Clock
clock = pygame.time.Clock()

# 2. Initialize Fonts ONCE outside the loop
try:
    FONT_TITLE = pygame.font.SysFont('Inter', 120, bold=True)
    FONT_BUTTON = pygame.font.SysFont('Inter', 40)
    FONT_SPLASH = pygame.font.SysFont(None, 35)
    FONT_FPS = pygame.font.SysFont(None, 24)
except pygame.error:
    # Fallback if 'Inter' is not available
    FONT_TITLE = pygame.font.SysFont(None, 120, bold=True)
    FONT_SPLASH = pygame.font.SysFont(None, 40)
    FONT_BUTTON = pygame.font.SysFont(None, 35)
    FONT_FPS = pygame.font.SysFont(None, 24)

# 3. Scale Textures ONCE outside the loop
GRASS_SCALED = None
DIRT_SCALED = None
if 'BLOCK_SIZE' in globals() and 'all_textures' in globals():
    grass_texture = all_textures.get('grass', None)
    dirt_texture = all_textures.get('dirt', None)
    if grass_texture and dirt_texture:
        GRASS_SCALED = pygame.transform.scale(grass_texture, (BLOCK_SIZE, BLOCK_SIZE))
        DIRT_SCALED = pygame.transform.scale(dirt_texture, (BLOCK_SIZE, BLOCK_SIZE))
# --- END MENU INITIALIZATION ---

class Button:
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.hovered = False

    def draw(self, surface):
        color = BUTTON_COLOR_HOVER if self.hovered else BUTTON_COLOR_NORMAL
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surf = self.font.render(self.text, True, TEXT_COLOR_NORMAL)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos, clicked):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and clicked:
            handle_button_click(self.text)

buttons = []

def make_buttons(option_list, start_y):
    buttons.clear()
    for i, text in enumerate(option_list):
        width = max(FONT_BUTTON.size(text)[0] + 60, 300)
        x = (screen.get_width() - width) // 2
        y = start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING)
        btn = Button(text, x, y, width, BUTTON_HEIGHT, FONT_BUTTON)
        buttons.append(btn)

def handle_button_click(text):
    global play, scroll, out, loaded_world, settings, keybinds, rebinding_action

    if not play and not settings:
        if text == 'Play':
            play = True
            scroll = 0
        elif text == 'Settings':
            settings = True
            scroll = 0
        elif text == 'Quit':
            pygame.quit()
            sys.exit()

    elif settings:
        if text == 'Back':
            if not keybinds:
                settings = False
                with open("Assets/Storage/Settings.json", "w") as f:
                    json.dump(setting, f, indent=4)
            else:
                keybinds = False
            scroll = 0
        elif keybinds:
            print(f"Clicked keybind: {text}")
            rebinding_action = text  # Start listening for new input
        else:
            print(f"Clicked setting: {text}")
            if text == 'KeyBinds':
                keybinds = True

    elif play:
        if text == 'Back':
            play = False
            scroll = 0
        else:
            index = current_options.index(text)
            loaded_world = current_filenames[index]
            out = True


def draw_scrolling_background(surface, offset):
    num_tiles_x = (surface.get_width() // BLOCK_SIZE) + 2
    num_tiles_y = surface.get_height() // BLOCK_SIZE
    horizon_y = num_tiles_y - 2
    for row in range(num_tiles_y + 1):
        for col in range(num_tiles_x):
            x = (col * BLOCK_SIZE) - offset
            y = row * BLOCK_SIZE
            if row == horizon_y:
                surface.blit(GRASS_SCALED, (x, y))
            elif row > horizon_y:
                surface.blit(DIRT_SCALED, (x, y))

def draw_title(surface, play_state, settings_state):
    if play_state:
        title = "Worlds"
    elif settings_state:
        title = "Settings"
    else:
        title = "Mine Flat"

    title_surf = FONT_TITLE.render(title, True, TEXT_COLOR_TITLE)
    title_rect = title_surf.get_rect(center=(surface.get_width() // 2, 70))
    surface.blit(title_surf, title_rect)


def draw_splash_text(surface, text):
    y_offset = int(math.sin(time.time() * 3) * 5)
    splash_surf = FONT_SPLASH.render(text, True, TEXT_COLOR_SPLASH)
    splash_rect = splash_surf.get_rect(center=(surface.get_width() // 2, 135 + y_offset))
    surface.blit(splash_surf, splash_rect)

def generate_buttons(option_list, surface, font, scroll_offset):
    buttons = []
    y_start = 200
    for i, text in enumerate(option_list):
        display_text = text
        if keybinds and text != "Back":
            code = setting["Keybinds"].get(text)
            if isinstance(code, int):
                display_text = f"{text}: {pygame.key.name(code)}"
        width = max(font.size(display_text)[0] + 60, 300)
        x = (surface.get_width() - width) // 2
        y = y_start + i * (BUTTON_HEIGHT + BUTTON_SPACING) + scroll_offset
        btn = Button(text, x, y, width, BUTTON_HEIGHT, font)
        buttons.append(btn)
    return buttons


splash_texts = []
with open('Assets/Storage/SplashText.txt') as f:
    for line in f:
        splash_texts.append(line.strip())
splash_text = random.choice(splash_texts)

while True:
    # --- Timing & Input ---
    dt = clock.tick(60) / 1000  # Delta time for smooth animations
    timed = time.time() * 100
    mouse_pos = pygame.mouse.get_pos()
    clicked = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = True
        elif event.type == pygame.MOUSEWHEEL:
            scroll += event.y * 50
        if rebinding_action:
            if event.type == pygame.KEYDOWN:
                key_code = event.key
                setting["Keybinds"][rebinding_action] = key_code
                with open("keybinds.json", "w") as f:
                    json.dump({"Keybinds": setting["Keybinds"]}, f, indent=4)
                print(f"Rebound {rebinding_action} to {pygame.key.name(key_code)}")
                rebinding_action = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                key_code = event.button
                setting["Keybinds"][rebinding_action] = key_code
                with open("keybinds.json", "w") as f:
                    json.dump({"Keybinds": setting["Keybinds"]}, f, indent=4)
                print(f"Rebound {rebinding_action} to mouse button {key_code}")
                rebinding_action = None
                keybind = setting['Keybinds']

    # --- Background ---
    screen.fill((135, 206, 235))
    scroll_offset = int((timed * SCROLL_SPEED) % BLOCK_SIZE)

    if GRASS_SCALED and DIRT_SCALED:
        draw_scrolling_background(screen, scroll_offset)

    # --- Title & Splash ---
    draw_title(screen, play, settings)
    draw_splash_text(screen, splash_text if not play else "")

    if rebinding_action:
        waiting_text = FONT_BUTTON.render(f"Press a key for '{rebinding_action}'...", True, (255, 255, 0))
        screen.blit(waiting_text, (screen.get_width() // 2 - waiting_text.get_width() // 2, 160))

    # --- Buttons ---
    if not play and not settings:
        current_options = ['Play', 'Settings', 'Quit']
        current_filenames = ['', '', '']
    elif settings:
        if not keybinds:
            current_options = ['KeyBinds', 'Back']
            current_filenames = ['', '']
        elif keybinds:
            current_options = list(setting["Keybinds"].keys()) + ['Back']
        current_filenames = ['' for setting in current_options]
    elif play:
        current_options = ['Back','New World'] + [os.path.splitext(f)[0] for f in world_options]
        current_filenames = ['','Deafualt_World.json'] + world_options

    buttons = generate_buttons(current_options, screen, FONT_BUTTON, scroll)
    for button in buttons:
        button.update(mouse_pos, clicked)
        button.draw(screen)

    if out:
        break

    # --- FPS Display ---
    fps = int(clock.get_fps())
    fps_text = FONT_FPS.render(f"FPS: {fps}", True, TEXT_COLOR_TITLE)
    screen.blit(fps_text, (10, 10))

    # --- Final Flip ---
    pygame.display.flip()


mods_path = 'Mods/'
mod_blocks = []

for folder_name in os.listdir(mods_path):
    folder_path = os.path.join(mods_path, folder_name)

    if os.path.isdir(folder_path):

        if folder_path == 'Mods/example mods':
            continue

        try:
            with open("Main.json") as file:
                mod_file = json.load(file)
        except Exception as e:
            log(f'Cant fild Main.json in mod {folder_path}')
        block_name = 'None'
        try:
            for block_name, block_info in mod_file.items():
                mod_blocks.append(block_name)
        except Exception as e:
            log(f'Block {block_name} is broken')


missing_blocks = []

def set_block(x, y, block_type):
    chunk_x = x // (block_size * CHUNK_SIZE)
    chunk_y = y // (block_size * CHUNK_SIZE)
    chunk_pos = (chunk_x, chunk_y)

    if chunk_pos not in chunk_lookup or chunk_lookup[chunk_pos] is None:
        chunk_lookup[chunk_pos] = {}

    chunk_lookup[chunk_pos][(x, y)] = block_type

block_palette = {
    'air': 0,
    "grass": 1,
    "dirt": 2,
    "stone": 3
}

structures = {}

folder_path = 'Assets/Structures/'

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        try:
            with open(os.path.join(folder_path, filename)) as f:
                print(f'{folder_path} name {filename}')
                structures[filename.replace('.json','')] = json.load(f)
        except Exception as e:
            print(f'[ERROR] {e}')

def compute_height_map(chunk_x):
    """Return a dict mapping block‐column bx→surface_y for this chunk."""
    height_map = {}
    for bx in range(CHUNK_SIZE):
        wx = chunk_x * CHUNK_SIZE * block_size + bx * block_size
        height_map[bx] = layered_height(wx)
    return height_map

def layered_height(x):
    """Return terrain height in pixels using multi-octave Perlin + ridged noise."""
    scale = 0.001
    octaves = 5
    persistence = 0.5
    lacunarity = 2.0

    # Base rolling hills
    n = noise.pnoise1((x + world_seed) * scale,
                      octaves=octaves,
                      persistence=persistence,
                      lacunarity=lacunarity,
                      repeat=999999) * 100

    # Ridged mountains
    ridge = abs(noise.pnoise1((x + world_seed) * scale * 0.5 + 1000,
                              octaves=3,
                              persistence=0.8,
                              lacunarity=2.0,
                              repeat=999999))
    ridge = (1.0 - ridge) * 200  # sharper peaks

    base_height = 300
    return int(base_height + n + ridge)

def carve_caves(bx, by):
    cave_scale = 1          # controls cave size
    threshold = -0.3            # carve where val < 0
    # sample at block-center, not raw integer
    sample_x = (bx + 0.5) * cave_scale
    sample_y = (by + 0.5) * cave_scale
    seed_offset = (world_seed % 1000) * 10

    val = noise.pnoise2((bx + 0.5 + seed_offset) * cave_scale,
                        (by + 0.5 + seed_offset) * cave_scale,
                        octaves=3,
                        persistence=0.5,
                        lacunarity=2.0)

    print(val)

    return val < threshold


def is_cave_at(wx, wy):
    """Return True if (wx, wy) should be air, carving large curving caves."""
    # Low-freq for main corridors
    low = snoise2(wx * 0.003,
                        wy * 0.003,
                        octaves=2,
                        )

    # High-freq for smaller branches
    high = snoise2(
        wx * 0.02 + world_seed * 0.001,
        wy * 0.02 + world_seed * 0.001,
        octaves=5
    )

    # Combine: carve if both layers dip below thresholds
    return (low < 0.0  and high < 0.02)


def smooth_mask(mask, passes=3):
    for _ in range(passes):
        new = [[False]*CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                # count neighboring carve cells
                count = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE:
                            if mask[ny][nx]:
                                count += 1
                # carve if at least 4 of 8 neighbors are caves
                new[y][x] = (count >= 4)
        mask = new
    return mask

def place_structure_block(x, y, block_type):
    global is_generating_chunk
    chunk_x = x // (block_size * CHUNK_SIZE)
    chunk_y = y // (block_size * CHUNK_SIZE)
    chunk_pos = (chunk_x, chunk_y)

    if chunk_pos not in chunk_lookup or chunk_lookup[chunk_pos] is None:
        if not is_generating_chunk:
            chunk_lookup[chunk_pos] = generate_chunk(chunk_x, chunk_y)
        else:
            return  # Skip placing into unloaded chunk during generation

    chunk_lookup[chunk_pos][(x, y)] = block_type



def spawn_structure(structure, origin_x, origin_y):
    for dx, dy, block_type in structures[structure]:
        # Scale offsets to match grid
        gx = origin_x + (dx // block_size) * block_size
        gy = origin_y + (dy // block_size) * block_size

        # Snap origin to grid
        gx = (gx // block_size) * block_size
        gy = (gy // block_size) * block_size
        place_structure_block(gx, gy, block_type)

def smooth_cave_mask(mask, passes=2):
    for _ in range(passes):
        new = [[False]*CHUNK_SIZE for _ in range(CHUNK_SIZE)]
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                count = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE:
                            if mask[ny][nx]:
                                count += 1
                # Carve if at least 5 neighbors are cave
                new[y][x] = (count >= 5)
        mask = new
    return mask
spawns = []
def spawn_mob(wx, wy, biome, rng):
    """Random chance to spawn a mob at (wx, wy) based on biome."""
    with open('Assets/Storage/MobStats.json') as f:
        stats = json.load(f)

    spawn_chance = {
        'plains': 0.05,
        'forest': 0.08,
        'cave': 0.02  # if you add cave biomes later
    }

    if rng.random() < spawn_chance.get(biome, 0):
        mob_type = rng.choice(all_mobs)  # customize per biome
        stats = stats[mob_type]

        for _ in stats:
            if stats[_] == 'BLOCK_SIZE':
                stats[_] = block_size

        spawns.append({
            "name": mob_type,
            "HP": float(stats["HP"]),
            "DMG": float(stats["DMG"]),
            "Pos": (float(wx), float(wy)),
            "speed": float(stats["Speed"]),
            "max_speed": float(stats["Max_speed"]),
            "left_hitbox": float(stats['Left']),
            "right_hitbox": float(stats['Right']),
            "width": float(stats['Width']),
            "height": float(stats['Height']),  # <-- Element separated by comma
            "Behavior": stats["Type"],
            "texture": mob_textures[mob_type],
            "range": stats["Range"],
            "drops": mob_drops[mob_type]
        })




is_generating_chunk = False

def generate_chunk(chunk_x, chunk_y):
    global is_generating_chunk
    biome = 'forest'
    is_generating_chunk = True

    rng        = random.Random(world_seed
                               + chunk_x * 73856093
                               + chunk_y * 19349663)
    height_map = compute_height_map(chunk_x)
    world_y0   = chunk_y * CHUNK_SIZE * block_size
    raw_mask   = [[False]*CHUNK_SIZE for _ in range(CHUNK_SIZE)]

    # 1) Initial carve
    for bx in range(CHUNK_SIZE):
        for by in range(CHUNK_SIZE):
            wx = chunk_x * CHUNK_SIZE * block_size + bx * block_size
            wy = world_y0 + by * block_size

            # Only carve below ground
            if wy > height_map[bx]:
                raw_mask[by][bx] = is_cave_at(wx, wy)

    # 2) Smooth for curving, expansive caves
    cave_mask = smooth_cave_mask(raw_mask, passes=3)

    # 3) Place blocks, skipping cave_mask cells
    chunk_data = {}
    for bx in range(CHUNK_SIZE):
        surface_y = height_map[bx]
        for by in range(CHUNK_SIZE):
            wy = world_y0 + by * block_size
            if wy <= surface_y or cave_mask[by][bx]:
                continue

            depth = wy - surface_y
            if depth < block_size:
                block = 'grass'
            elif depth < block_size * 4:
                block = 'dirt'
            else:
                block = 'stone'

            if block == 'grass':
                spawn_mob(wx,wy - block_size,biome,rng)

            chunk_data[(chunk_x * CHUNK_SIZE * block_size + bx * block_size, wy)] = block

    # 6) Spawn structures, finish up
    if rng.random() < (0.2 if biome=='forest' else 0.1):
        tree_x = rng.randint(0, CHUNK_SIZE-1) * block_size\
            + chunk_x * CHUNK_SIZE * block_size
        tree_y = (layered_height(tree_x) // block_size) * block_size
        spawn_structure('oak_tree', tree_x, tree_y)

    is_generating_chunk = False
    return chunk_data





chunk_lookup = {}
def generate_world(center_chunk_x, center_chunk_y, radius=5):
    global chunk_lookup
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            chunk_x = center_chunk_x + dx
            chunk_y = center_chunk_y + dy
            chunk_pos = (chunk_x, chunk_y)

            if chunk_pos not in chunk_lookup:
                chunk_lookup[chunk_pos] = generate_chunk(chunk_x, chunk_y)


def export_generated_world():
    platforms = []
    lookup = {}


    for chunk in chunk_lookup.values():
        try:
            for (x, y), block_type in chunk.items():
                platforms.append([x, y, block_type])
                lookup[str((x, y))] = block_type
        except Exception as e:
            print(f'{chunk},{e}')

    return {
        "platforms": platforms,
        "lookup": lookup,
        "water": []  # You can populate this later if needed
    }

# --- START OF WORLD LOADING EXECUTION ---

import json
import random
import time
import os
import sys


# NOTE: The following variables/classes MUST be defined globally
# for this script to function correctly:
# global HP, INVENTORY, mobs, items_on_ground, Mob, block_size, CHUNK_SIZE, world_seed,
# flowing_water_chunks, chunk_lookup, all_blocks, mod_blocks, missing_blocks
# (The Mob class is needed to re-instantiate mob objects from saved data.)

invselected = 1
player_inventory = [[('',0)],[('',0)],[('',0)]]
for i, row in enumerate(player_inventory):
    while len(row) < 9:
        player_inventory[i].append(('',0))
        row.append(('',0))

crafting_grid = [[('',0)],[('',0)],[('',0)]]
crafting_output = ('', 0)

for i, row in enumerate(crafting_grid):
    while len(row) < 3:
        crafting_grid[i].append(('',0))
        row.append(('',0))

no_block = ('',0)

player_hotbar_base = []
while len(player_hotbar_base) < 9:
    player_hotbar_base.append(('',0))
player_hotbar_selected = 0
player_hotbar = player_hotbar_base
player_offhand = ('',0)

# --- HELPER FUNCTION FOR DYNAMIC STATE LOADING ---
def load_dynamic_state(world_data):
    """
    Extracts and deserializes dynamic game state (HP, Inventory, Mobs, Items)
    from the loaded world dictionary. Updates the global state.

    Returns: The restored HP, items_on_ground, mobs, player_x, and player_y values.
    """
    # Assuming these are accessible global variables for updating state:
    global HP, mobs, items_on_ground, player_x, player_y

    # Player position fallback (using static 'player_pos')
    player_x_loaded = world_data.get("player_pos", [0, 0])[0]
    player_y_loaded = world_data.get("player_pos", [0, 0])[1]

    game_state = world_data.get('game_state')

    if not game_state:
        print("[LOAD] No dynamic game state found. Starting fresh HP, Inventory, Mobs.")
        # Return default dynamic states if no save game state exists
        return 20.0, [], [], player_x_loaded, player_y_loaded, [], []

    print("[LOAD] Dynamic game state found. Restoring player status and entities.")

    # 1. Player HP (The fix for your lost health!)
    restored_HP = game_state.get("player_hp", 20.0)

    # 2. Restore Inventory
    player_inventory_loaded = game_state.get("inventory", player_inventory)

    # 3. Load Hotbar
    player_hotbar_loaded = game_state.get("hotbar", player_hotbar)

    # 4. Dropped Items
    restored_items = game_state.get("items_on_ground", [])

    # 5. Mobs (Deserialization - requires the global Mob class)
    restored_mobs = []

    for mob_data in game_state.get('mobs', []):
        try:
            # Re-instantiate Mob using saved properties
            mob = {
                "name": mob_data['type'],
                "HP": mob_data['health'],
                "X": mob_data['position'][0],
                "Y": mob_data['position'][1],
                "DMG": mob_data['damage'],
                "speed": mob_data['speed'],
                "max_speed": mob_data['max_speed'],
                "width": mob_data['width'],
                "height": mob_data['height'],
                "left_hitbox": mob_data['left_hitbox'],
                "right_hitbox": mob_data['right_hitbox'],
                "range": mob_data['Range'],
                "Behavior": mob_data['Behavior']
            }
            # Restore health
            restored_mobs.append(mob)
        except Exception as e:
            print(f"[ERROR] Failed to restore mob {mob_data.get('type')}: {e}")

    return restored_HP, restored_items, restored_mobs, player_x_loaded, player_y_loaded, player_inventory_loaded, player_hotbar_loaded


start = time.time()
platforms = set()
# Assuming these exist globally:
# flowing_water_chunks = {}
# chunk_lookup = {}
# all_blocks, mod_blocks, missing_blocks = ...

try:
    with open(f'Worlds/{loaded_world}', 'r') as f:
        world = json.load(f)
except FileNotFoundError:
    print(f"[ERROR] World file 'Worlds/{loaded_world}' not found.")
    pygame.quit()
    sys.exit()

# Set initial player position from file (used as fallback/default)
player_x_default = world.get("player_pos", [0, 0])[0]
player_y_default = world.get("player_pos", [0, 0])[1]

# Check if we are loading a new world template ('Deafualt_World.json')
if loaded_world == 'Deafualt_World.json':
    # --- NEW WORLD GENERATION LOGIC ---
    print("[WORLD] Starting new generated world.")
    loaded_world = f'Save{count_json_files("Worlds/") + 1}.json'

    # Set seed and generate
    world_seed = world.get("seed", random.randint(0, 999999999))

    # FIX: Ensure world_seed is an integer if it was loaded as None from the template
    if world_seed is None:
        world_seed = random.randint(0, 999999999)

    print(f"[SEED] Generated world seed: {world_seed}")

    spawn_chunk_x = player_x_default // (block_size * CHUNK_SIZE)
    spawn_chunk_y = player_y_default // (block_size * CHUNK_SIZE)
    generate_world(spawn_chunk_x, spawn_chunk_y, 5)
    world = export_generated_world()

    # Dynamic state is default: HP=20.0, mobs=[], items_on_ground=[], INVENTORY={}
    HP = 20.0
    mobs = []
    items_on_ground = []
    # No need to set INVENTORY={} as it's assumed to be initialized outside this block

    player_x = player_x_default
    player_y = player_y_default

else:
    # --- EXISTING WORLD LOAD LOGIC ---
    print(f"[WORLD] Loading existing world: {loaded_world}")

    # 1. Load Dynamic State (The critical step!)
    # This call updates the global HP, INVENTORY, mobs, and items_on_ground
    HP, items_on_ground, mob, player_x, player_y, player_inventory, player_hotbar = load_dynamic_state(world)

    mobs = []

    for _ in mob:
        # mob = {
        #     "name": mob_data['type'],
        #     "HP": mob_data['health'],
        #     "X": mob_data['position'][0],
        #     "Y": mob_data['position'][1],
        #     "DMG": mob_data['damage'],
        #     "speed": mob_data['speed'],
        #     "max_speed": mob_data['max_speed'],
        #     "width": mob_data['width'],
        #     "height": mob_data['height'],
        #     "left_hitbox": mob_data['left_hitbox'],
        #     "right_hitbox": mob_data['right_hitbox'],
        #     "range": mob_data['Range'],
        #     "Behavior": mob_data['Behavior']
        # }
        # name, health, damage, position,speed,max_speed,left_hitbox,right_hitbox,width,height, sprite, type, range, drops = None
        spawns.append({"name":_['name'],"HP":float(_['HP']),"DMG":float(_['DMG']),"Pos":(float(_['X']),float(_['Y'])),"speed":float(_['speed']),"max_speed":float(_['max_speed']),"left_hitbox":float(_['left_hitbox']),"right_hitbox":float(_['right_hitbox']),"width":float(_['width']),"height":float(_['height']),"texture":mob_textures[_['name']],"B"
                                                                                                                                                                                                                                                                                                                                                        "havior":_['Behavior'],"range":_['range'],"drops":mob_drops[_['name']]})
    # 2. Load Static World Data
    world_seed = world.get("seed", random.randint(0, 999999999))

    # FIX: Ensure world_seed is an integer if it was loaded as None from the save file
    if world_seed is None:
        world_seed = random.randint(0, 999999999)

    print(f"[SEED] Loaded world seed: {world_seed}")

    # ... (Your existing logic to process platforms, lookup, and water follows) ...
    # This logic is complex, so I'm summarizing it, but your block below should execute:
    for _ in world.get("platforms", []):
        if _[2] not in all_blocks and _[2] not in mod_blocks:
            if not _[2] in missing_blocks and not _[2] in (None, 'None'):
                missing_blocks.append(_[2])
        reformat = (_[0], _[1], _[2])
        platforms.add(reformat)

    lookup = world.get("lookup", {})
    platform_lookup = {}
    for key, value in lookup.items():
        if value not in all_blocks and value not in mod_blocks:
            if value not in missing_blocks and value not in (None, 'None'):
                missing_blocks.append(value)

        x, y = map(float, key.strip("()").split(","))
        set_block(x, y, value)
        platform_lookup[(x, y)] = value

    water = world.get("water", [])

    for x, y, px, py in water:
        chunk = get_chunk_coords(x, y)
        flowing_water_chunks.setdefault(chunk, {})[(x, y)] = (px, py)
# ... (End of your existing block loading logic) ...
print(player_x,player_y)

# Final checks remain the same
if missing_blocks:
    print(missing_blocks)
    log("Missing modded blocks detected:")
    for block in missing_blocks:
        log(f" - {block}")
    log("Closing to avoid world corruption.")
    pygame.quit()
    sys.exit()

print(f"[LOAD TIME] {time.time() - start:.2f}s")

fallingblocks = ['sand','gravel']
fallingblocks.extend(f"{color}_concrete_powder" for color in colors)
not_collidable = ["oak_door_top", "oak_door_bottom",'water','flowing_water','', None]
not_collidable.extend(f"{color}_carpet" for color in colors)
not_collidable.extend(f"{block}" for block in climbable_blocks)
breakable_by_water = []
breakable_by_water.extend(f"{color}_carpet" for color in colors)
liquid = ['water','lava']
fallingblocksbreak = ['torch']
fallingblocksbreak.extend(f"{color}_carpet" for color in colors)
unbreakable_blocks = ['flowing_water']

# for (x, y), name in platform_lookup.items():
#     log(f'Making {name} at ({x},{y})')

#load all textures

animated_blocks = {
    "flowing_water": {
        "frames": [
            pygame.image.load("Assets/Images/Blocks/Liquids/water/flowing_water.png").convert_alpha(),
            pygame.image.load("Assets/Images/Blocks/Liquids/water/flowing_water2.png").convert_alpha()
        ],
        "current_frame": 0,
        "last_frame_update": 0.0,
        'frame_duration':1
    }
}


def save_world(platforms, chunk_lookup, mobs, items_on_ground, inventory,hotbar, HP, filename=f"Worlds/{loaded_world}"):
    """
    Saves all game data, including static world structure and dynamic entities.

    NOTE: This function assumes that 'world_seed', 'player_x', 'player_y', and
    'flowing_water_chunks' are available in the global scope where this function is called.

    Args:
        platforms (list): List of platform tuples.
        chunk_lookup (dict): Lookup table for blocks by chunk.
        mobs (list): List of Mob objects to be serialized.
        items_on_ground (list): List of item dictionaries for dropped items.
        inventory (dict): The player's current item counts.
        HP (float): The player's current health.
        filename (str): The full path to the world file.
    """

    # --- 1. Static World Data Serialization ---
    # Lookup table for all existing blocks
    lookup = {
        f"({x}, {y})": block_type
        for chunk in chunk_lookup.values()
        for (x, y), block_type in chunk.items()
    }

    platforms_list = [
        [x, y, block_type if block_type is not None else None]
        for (x, y, block_type) in platforms
    ]

    # Water flow data
    water_list = [
        [x, y, px, py]
        for chunk in flowing_water_chunks.values()
        for (x, y), (px, py) in chunk.items()
    ]

    # --- 2. Dynamic Entity Serialization ---
    # Convert Mob objects to dictionaries for saving (Requires mob.to_dict())
    mobs_data = [mob.to_dict() for mob in mobs]

    # Combine all dynamic state into one section
    dynamic_state = {
        "mobs": mobs_data,
        "items_on_ground": items_on_ground,
        "inventory": inventory,
        "hotbar": hotbar,
        "player_hp": HP
    }

    # --- 3. Compile Final World Data ---
    world_data = {
        "seed": world_seed,
        "player_pos": [player_x, player_y],
        "lookup": lookup,
        "platforms": platforms_list,
        "water": water_list,
        "game_state": dynamic_state  # The new dynamic data block
    }

    # --- 4. Write to File ---
    try:
        with open(filename, "w") as file:
            json.dump(world_data, file, indent=2)
        print(f"World saved to {filename}")
    except Exception as e:
        print(f"ERROR: Could not save world data to {filename}. Details: {e}")


def animate_blocks():
    for _ in animated_blocks:
        if time.time() > animated_blocks[_].get("last_frame_update", 0) + animated_blocks[_].get("frame_duration", 1):
            animated_blocks[_]["last_frame_update"] = time.time()
            target_frame = animated_blocks[_]['frames'][int(animated_blocks[_]['current_frame'])]
            scaled_image = pygame.transform.scale(target_frame, (50, 50))
            block_textures[_] = scaled_image
            if not animated_blocks[_]['current_frame'] == len(animated_blocks[_]['frames']) - 1:
                animated_blocks[_]['current_frame'] += 1
            else:
                animated_blocks[_]['current_frame'] = 0

def add_block(block):
    global player_inventory, player_hotbar
    try:

        # Try to stack in hotbar
        for i, item in enumerate(player_hotbar):
            if item[0] == block:
                player_hotbar[i] = (block, item[1] + 1)
                return

        # Try to stack in inventory
        for row in range(len(player_inventory)):
            for slot in range(len(player_inventory[row])):
                item = player_inventory[row][slot]
                if item[0] == block:
                    player_inventory[row][slot] = (block, item[1] + 1)
                    return

        # Try to place in empty hotbar slot
        for i, item in enumerate(player_hotbar):
            if str(item) == str(no_block):
                player_hotbar[i] = (block, 1)
                return

        # Try to place in empty inventory slot
        for row in range(len(player_inventory)):
            for slot in range(len(player_inventory[row])):
                item = player_inventory[row][slot]
                if str(item) == str(no_block):
                    player_inventory[row][slot] = (block, 1)
                    return

    except Exception as e:
        print(f'Add Block Broke: {e}')

def remove_block(inv,slot):
    if inv == 'Hot':
        item = player_hotbar[slot]
        stack = int(item[1]) - 1
        item = (item[0],stack)
        if item[1] == 0:
            item = no_block
        player_hotbar[slot] = item
    elif inv == 'Inv':
        slot_x = slot[0]
        slot_y = slot[1]
        item = player_inventory[slot_x][slot_y]
        stack = int(item[1]) - 1
        item = (item[0],stack)
        if item[1] == 0:
            item = no_block
        player_inventory[slot_x][slot_y] = item

def drop_item(item,x,y):
    global item_drops
    item_drops.append((item, (x,y)))

# Define colors (RGB format)
WHITE = (255, 255, 255)
BLACK = (0,0,0)
BLUE = (0,0,255)
GRAY = (48, 48, 48)
LIGHT_GRAY = (80, 80, 80)
LIGHTER_GRAY = (160, 160, 160)

#set up mods
log('Setting up Mods')

mods_path = "Mods/"

mod_blocks = {}
player_inventory_modded = [['','','','','','','','',''],['','','','','','','','',''],['','','','','','','','','']]
all_lines = []

missingfiles = []
messedupmods = []

for folder_name in os.listdir(mods_path):
    folder_path = os.path.join(mods_path, folder_name)

    if os.path.isdir(folder_path):

        if folder_path == 'Mods/example mods':
            continue

        # This is a mod folder—do your loading here
        print(f"Loading mod from: {folder_path}")
        log(f"Loading mod from: {folder_path}")

        # Example: set this folder as the current working directory
        os.chdir(folder_path)

        try:
            with open("Main.json") as file:
                mod_file = json.load(file)
            lines = []
            for line in mod_file:
                lines.append(line)
                all_lines.append(line)
            image_path = 'None'
            for block_name, block_info in mod_file.items():
                try:
                    image_path = block_info.get("image")
                    mod_blocks[block_name] = pygame.image.load(image_path).convert_alpha()
                    block_textures[block_name] = pygame.image.load(image_path).convert_alpha()
                    if block_info.get("gravity"):
                        fallingblocks.append(block_name)
                    if not block_info.get("is_collidable"):
                        not_collidable.append(block_name)
                    animation = block_info.get("animation",None)
                    if not animation is None:
                        for i,_ in enumerate(animation.get("frames", [])):
                            animation["frames"][i] = pygame.image.load(_).convert_alpha()
                        animated_blocks[block_name] = animation
                except Exception as e:
                        path = f"{folder_path}/{image_path.split('/')[0]}"
                        block = image_path.split('/')[1]
                        missingfiles.append(f'block:{block},path:{path}')
                        if not folder_name in messedupmods:
                            messedupmods.append(folder_name)
        except Exception as e:
            block = str(e).split('\'')[1]
            block = block.split('\'')[0]
            path = folder_path
            log(f'CRASHED CRASHED\nCan\'t find file {block} in the in directory {path}')
            os.chdir(os.path.dirname(__file__))
            os.makedirs('Logs', exist_ok=True)
            os.chdir(f'{os.path.dirname(__file__)}/Logs')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            pygame.quit()
            sys.exit()

        # Return to base directory after processing
        os.chdir(os.path.dirname(__file__))

if len(missingfiles) > 0:
    log(f'CRASHED CRASHED')
    log('Can\'t find file(s)')

    for _ in missingfiles:
        image = _.split('block:')[1]
        image = image.split(',path')[0]
        path = _.split(',path:')[1]
        log(f'{image} at directory {path}')

    log(f'This is from the mod(s)')

    for _ in messedupmods:
        log(_)

    log('Please disable them, or fix them to continue')

    pygame.quit()
    sys.exit()

log('Setting up Modded hotbar')

player_hotbar_modded = []
for _ in list(mod_blocks.keys()):
    player_hotbar_modded += [_]

while len(player_hotbar_modded) < 9:
    player_hotbar_modded.append('')

def save_screenshot(screen):
    global latestmsg
    # Make sure the folder exists
    if not os.path.exists('Screenshots/'):
        log(f'Making Screenshots folder')
    os.makedirs(screenshots_path, exist_ok=True)

    # Create a timestamped filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(screenshots_path, filename)

    # Save the screen surface as PNG
    pygame.image.save(screen, filepath)
    print(f"Screenshot saved to: {filepath}")
    latestmsg = time.time()
    chat.append(f"Screenshot saved to: {filepath}")
    log(f'Screenshot saved to: {filepath}')


def draw_transparent_square(surface, x, y, width, height, color=(255, 0, 0), alpha=128):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, (x, y))

def is_collidable(x, y):
    block = get_block_at(x, y)
    return block not in not_collidable

def is_collidable_block(block):
    return block not in not_collidable

def on_block():
    feet_y = player_y + player_height
    feet_x = player_x + player_width // 2

    grid_x = (feet_x // block_size) * block_size
    grid_y = (feet_y // block_size) * block_size

    return is_collidable(grid_x, grid_y)

def on_block_item(x,y,size,x_offset = 0,y_offset = 0):
    feet_y = y + size + y_offset
    feet_x = x + size // 2 + x_offset

    grid_x = (feet_x // block_size) * block_size
    grid_y = (feet_y // block_size) * block_size

    return is_collidable(grid_x, grid_y)

def block_player_inside():
    feet_y = player_y + block_size + block_size // 2
    feet_x = player_x + player_width // 2

    grid_x = (feet_x // block_size) * block_size
    grid_y = (feet_y // block_size) * block_size

    return get_block_at(grid_x, grid_y)

def above_block():
    feet_y = player_y
    feet_x = player_x + player_width // 2

    grid_x = (feet_x // block_size) * block_size
    grid_y = (feet_y // block_size) * block_size

    return is_collidable(grid_x, grid_y)

def side_block(offset_x):
    check_points = [
        player_y + player_height - 25,
        player_y + player_height // 2 - 25
    ]

    for side_y in check_points:
        side_x = player_x + player_width // 2 + offset_x
        grid_x = (side_x // block_size) * block_size
        grid_y = (side_y // block_size) * block_size

        if is_collidable(grid_x, grid_y):
            return True

    return False

def left_block():
    return side_block(-5)

def right_block():
    return side_block(+5)

startfall = None
def updatemovement():
    global player_x, player_y, player_y_vel, jump, startfall, HP, player_start_hit

    player_width = 50
    player_height = 100

    # Check if player is standing on the block
    on_platform = on_block()

    # Apply gravity if NOT standing on the block
    if startfall is not None and on_platform:

        if player_y > startfall + block_size * 2:
            startfall = startfall // block_size
            player_fall = player_y // block_size

            startfall += 3

            hurt_player(max(0, player_fall - startfall))


        startfall = None
    if on_platform and not jump:
        player_y_vel = 0
        while on_platform:
            player_y -= 1
            on_platform = on_block()

    if not on_platform and not jump:
        player_y_vel += 1
        if startfall is None:
            startfall = player_y
    else:
        if jump:
            if player_y_vel > 0:
                jump = False
                if startfall is None:
                    startfall = player_y
            player_y_vel += 1
            roof = above_block()
            if roof:
                player_y_vel = 0
            tries = 0
            max_tries = 100
            while roof and not tries >= max_tries:
                player_y += 1
                roof = above_block()
                tries += 1

    player_y += player_y_vel

def player_jump():
    global jump, player_y_vel
    jump = True
    player_y_vel = -12

def get_block_at(x, y):
    chunk = get_chunk(x, y)
    try:
        return chunk.get((x, y))
    except:
        return None


def draw_hotbar():
    font = pygame.font.SysFont(None, 30)

    slot_size = 65

    for i in range(9):
        slot_x = screen.get_width() // 2 - 20 + ((i - 4) * slot_size)

        # 1. Draw the light gray background and the selected border
        slot_y = screen.get_height() - slot_size - 10
        slot_rect_def = (slot_x, slot_y, slot_size, slot_size)

        pygame.draw.rect(screen, LIGHT_GRAY, slot_rect_def)
        pygame.draw.rect(screen, GRAY if not i == player_hotbar_selected else BLACK, slot_rect_def, 5)

        try:
            item = player_hotbar[i]
            screen.blit(block_textures[item[0]], (slot_x + 8, slot_y + 8))

            stack_count = item[1]
            text_str = str(stack_count)
            if stack_count > 0:
                shadow_surface = font.render(text_str, True, (0, 0, 0))  # BLACK
                text_surface = font.render(text_str, True, (255, 255, 255))  # WHITE

                slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)

                text_rect = text_surface.get_rect()

                padding = 5
                text_rect.bottomright = (slot_rect.right - padding, slot_rect.bottom - padding)

                screen.blit(shadow_surface, (text_rect.x + 2, text_rect.y + 2))

                screen.blit(text_surface, text_rect)

        except:
            # Item is missing or error
            screen.blit(block_textures['Missing_Block'], (slot_x + 8, slot_y + 8))

    # --- Offhand Drawing ---
    slot_x = screen.get_width() // 2 - 20 + ((-1.5 - 4) * slot_size)

    # 1. Draw the light gray background and the selected border
    slot_y = screen.get_height() - slot_size - 10
    slot_rect_def = (slot_x, slot_y, slot_size, slot_size)

    pygame.draw.rect(screen, LIGHT_GRAY, slot_rect_def)
    pygame.draw.rect(screen, GRAY if not i == player_hotbar_selected else BLACK, slot_rect_def, 5)

    try:
        item = player_offhand
        screen.blit(block_textures[item[0]], (slot_x + 8, slot_y + 8))

        stack_count = item[1]
        text_str = str(stack_count)
        if stack_count > 0:
            shadow_surface = font.render(text_str, True, (0, 0, 0))  # BLACK
            text_surface = font.render(text_str, True, (255, 255, 255))  # WHITE

            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)

            text_rect = text_surface.get_rect()

            padding = 5
            text_rect.bottomright = (slot_rect.right - padding, slot_rect.bottom - padding)

            screen.blit(shadow_surface, (text_rect.x + 2, text_rect.y + 2))

            screen.blit(text_surface, text_rect)

    except:
        # Item is missing or error
        screen.blit(block_textures['Missing_Block'], (slot_x + 8, slot_y + 8))

    # --- HP/Heart Drawing ---
    for i in range(10):
        heart_x = screen.get_width() // 2 - 30 + ((i - 10) * 30)
        heart_index = i + 1
        if HP >= heart_index * 2:
            heart_type = 'heart_full'
        elif HP == heart_index * 2 - 1:
            heart_type = 'heart_half'
        else:
            heart_type = 'heart_empty'
        screen.blit(ui_textures[heart_type], (heart_x + 50, screen.get_height() - slot_size - 40))


held_inv_block = None

#–– Globals: add these at top of your module ––#
dragging        = False
dragged_item    = None
drag_source     = None   # ("base", row, col) or ("hotbar", None, col)

#–– Helper: return ("base"/"hotbar", row, col) if mouse over slot, else None ––#
def get_slot_under_mouse():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    slot_size = 60
    padding = 10
    cols = 9
    rows = 3
    craft_rows = 3
    craft_cols = 3

    inv_width = cols * slot_size
    inv_height = rows * (slot_size - padding) + slot_size * 2  # includes hotbar

    center_x = screen.get_width() // 2 - inv_width // 2 + 50
    center_y = screen.get_height() // 2 - inv_height // 2 + 25

    # Base inventory
    for row in range(rows):
        for col in range(cols):
            slot_x = center_x + col * (slot_size - padding)
            slot_y = center_y + row * (slot_size - padding)
            rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)
            if rect.collidepoint(mouse_x, mouse_y):
                return ("base", row, col)

    # Crafting grid
    for row in range(craft_rows):
        for col in range(craft_cols):
            y_offset = -((row + 2.26) * slot_size)
            slot_x = center_x + (cols // 2 - (col + 1)) * (slot_size + padding)
            slot_y = center_y + (slot_size + padding) + y_offset
            rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)
            if rect.collidepoint(mouse_x, mouse_y):
                return ("crafting", row, col)

    # Crafting output slot
    y_offset = -((1 + 2.26) * slot_size)
    slot_x = center_x + (cols // 2 - -1) * (slot_size + padding)
    slot_y = center_y + (slot_size + padding) + y_offset
    rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)
    if rect.collidepoint(mouse_x, mouse_y):
        return ("output", 0, 0)

    # Hotbar
    hot_y = center_y + rows * (slot_size - padding) + slot_size // 4
    for col in range(cols):
        slot_x = (center_x - padding * 5) + col * slot_size
        rect = pygame.Rect(slot_x, hot_y, slot_size, slot_size)
        if rect.collidepoint(mouse_x, mouse_y):
            return ("hotbar", 0, col)

    # Offhand
    slot_x = (center_x - padding * 5) + -1.5 * slot_size
    rect = pygame.Rect(slot_x, hot_y, slot_size, slot_size)
    if rect.collidepoint(mouse_x, mouse_y):
        return ("offhand", 0, 0)

    return None

flow_depth = {}  # (x, y): depth
MAX_DEPTH = 8    # tweak this to control spread

#–– Modified draw_inventory with drag preview ––#
def _draw_item_stack_count(screen, stack_count, slot_rect):
    """
    Draws the item stack count (e.g., '64') aligned to the bottom-right
    of the given slot_rect. Includes a shadow for readability.
    Matches the style used in draw_hotbar().
    """

    if stack_count <= 0:
        return

    font = pygame.font.SysFont(None, 30)
    text_str = str(stack_count)

    shadow_surface = font.render(text_str, True, (0, 0, 0))
    text_surface = font.render(text_str, True, (255, 255, 255))

    # Increase padding to avoid clipping
    padding = 10  # was 5
    text_rect = text_surface.get_rect()
    text_rect.bottomright = (slot_rect.right - padding, slot_rect.bottom - padding)

    # Reduce shadow offset to avoid overflow
    screen.blit(shadow_surface, (text_rect.x + 1, text_rect.y + 1))
    screen.blit(text_surface, text_rect)



def draw_inventory():
    global crafting_output
    mouse_x, mouse_y = pygame.mouse.get_pos()
    slot_size = 60
    cols = 9
    rows = 3
    craft_rows = 3
    craft_cols = 3
    padding = 10

    inv_width = cols * (slot_size)
    inv_height = rows * (slot_size - padding) + slot_size * 2  # includes hotbar

    center_x = screen.get_width() // 2 - inv_width // 2 + 50
    center_y = screen.get_height() // 2 - inv_height // 2 + 25

    pygame.draw.rect(
        screen, LIGHTER_GRAY,
        (center_x - 20 - (padding * 5), center_y - 20, inv_width + 40, inv_height + 40)
    )

    # Draw base inventory
    for row in range(rows):
        for col in range(cols):
            slot_x = center_x + col * (slot_size - padding)
            slot_y = center_y + row * (slot_size - padding)
            rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)

            pygame.draw.rect(screen, BLACK if rect.collidepoint(mouse_x, mouse_y) else LIGHT_GRAY, rect)

            if dragging and drag_source == ("base", row, col):
                continue

            full_item = player_inventory[row + invscroll][col]
            item = full_item[0]
            stack = full_item[1]

            try:
                screen.blit(block_textures[item], (slot_x, slot_y))
            except:
                screen.blit(block_textures['Missing_Block'], (slot_x, slot_y))

            if full_item is not None:
                _draw_item_stack_count(screen, stack, rect)

    for row in range(craft_rows):
        for col in range(craft_cols):
            # X = (cols - col)
            y = -((row + 2.26) * slot_size)
            slot_x = center_x + (cols // 2 - (col + 1)) * (slot_size + padding)
            slot_y = center_y + (slot_size + padding) + y

            rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)
            pygame.draw.rect(screen, BLACK if rect.collidepoint(mouse_x, mouse_y) else LIGHT_GRAY, rect)

            full_item = crafting_grid[row][col]
            if full_item is not None:
                item, stack = full_item

                try:
                    screen.blit(block_textures[item], (slot_x, slot_y))
                except:
                    screen.blit(block_textures['Missing_Block'], (slot_x, slot_y))

                _draw_item_stack_count(screen, stack, rect)

    # Check Recipe
    crafting_items = []
    for crafting_row in crafting_grid:
        for crafting_item in crafting_row:
            crafting_items.append(crafting_item[0])
    crafting_items.append('')
    crafted = False
    output_recipe = None
    for recipe in crafting_recipes:
        crafted = False
        type = recipe["type"]
        pattern = recipe["pattern"]
        output = recipe["result"]
        key = recipe["key"]
        for item in key:
            key[item] = recipe["key"][item]
        key['_'] = {'item': ''}
        next = False
        shapeless_craft = crafting_items
        for row, row_item in enumerate(reversed(pattern)):
            for col, col_item in enumerate(reversed(row_item)):
                item = str(key[col_item]['item']).lower()
                if type == 'shapeless':
                    if not item in shapeless_craft:
                        next = True
                        break
                    else:
                        shapeless_craft.remove(item)
                elif type == 'shaped':
                    if not item == crafting_grid[row][col][0]:
                        next = True
                        break
            if next:
                break
        if not next:
            if not crafting_output == (output["item"],output["count"]):
                crafting_output = (output["item"],output["count"])
            break
        else:
            if crafting_output == (output["item"],output["count"]):
                crafting_output = ('',0)

    # Draw Output
    y = -((1 + 2.26) * slot_size)
    slot_x = center_x + (cols // 2 - -1) * (slot_size + padding)
    slot_y = center_y + (slot_size + padding) + y

    rect = pygame.Rect(slot_x, slot_y, slot_size - padding, slot_size - padding)
    pygame.draw.rect(screen, BLACK if rect.collidepoint(mouse_x, mouse_y) else LIGHT_GRAY, rect)

    full_item = crafting_output
    item = full_item[0]
    stack = full_item[1]

    try:
        screen.blit(block_textures[item], (slot_x, slot_y))
    except:
        screen.blit(block_textures['Missing_Block'], (slot_x, slot_y))

    if full_item is not None:
        _draw_item_stack_count(screen, stack, rect)

    # Draw hotbar
    hot_y = center_y + rows * (slot_size - padding) + slot_size // 4
    for col in range(cols):
        slot_x = (center_x - padding * 5) + col * slot_size
        rect = pygame.Rect(slot_x, hot_y, slot_size, slot_size)
        pygame.draw.rect(screen, GRAY, rect, 5)

        if dragging and drag_source == ("hotbar", None, col):
            continue

        full_item = player_hotbar[col]
        item = full_item[0]
        stack = full_item[1]

        try:
            screen.blit(block_textures[item], (slot_x + 5, hot_y + 5))
        except:
            screen.blit(block_textures['Missing_Block'], (slot_x + 13, hot_y + 10))

        if full_item is not None:
            _draw_item_stack_count(screen, stack, rect)

    slot_x = (center_x - padding * 5) + -1.5 * slot_size
    rect = pygame.Rect(slot_x, hot_y, slot_size, slot_size)
    pygame.draw.rect(screen, LIGHTER_GRAY, rect)
    pygame.draw.rect(screen, GRAY, rect, 5)

    full_item = player_offhand
    item = full_item[0]
    stack = full_item[1]

    try:
        screen.blit(block_textures[item], (slot_x + 5, hot_y + 5))
    except:
        screen.blit(block_textures['Missing_Block'], (slot_x + 5, hot_y + 5))

    if full_item is not None:
        _draw_item_stack_count(screen, stack, rect)

    # Draw dragged item under cursor
    if dragging and dragged_item is not None:
        item,stack = dragged_item
        tex = block_textures[item]
        w, h = tex.get_size()
        item_x = mouse_x - w // 2
        item_y = mouse_y - h // 2
        screen.blit(tex, (item_x,item_y))
        rect = pygame.Rect(item_x, item_y, w, h)
        _draw_item_stack_count(screen, stack, rect)

def typechat():
    global chat_input, inchat
    while True:
        if inchat:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter to send
                        inchat = False
                        chat_input = ""

                    elif event.key == pygame.K_ESCAPE:  # Escape to cancel
                        inchat = False
                        chat_input = ""

                    elif event.key == pygame.K_BACKSPACE:  # Delete last character
                        chat_input = chat_input[:-1]

                    else:
                        # Add the character to input
                        chat_input += event.unicode

def getchatinput():
    return chat_input

def display_chat():
    global chat_input, inchat
    i = 0
    size = 50
    y = (i + 1) * size
    draw_transparent_square(screen, 0, screen.get_height() - y - 10, 9 * len(getchatinput()), size, BLACK, 200)
    for _ in chat:
        y = (i + 2) * size
        draw_transparent_square(screen, 0, screen.get_height() - y - 10, 9 * len(_), size,BLACK,200)

        font = pygame.font.SysFont(None, 24)
        text = font.render(f"{_}", True, WHITE)
        screen.blit(text, (0, screen.get_height() - y - 10))

        i += 1

    # Render the text
    font = pygame.font.SysFont(None, 36)
    text_surface = font.render(getchatinput(), True, (255, 255, 255))
    screen.blit(text_surface, (15, screen.get_height() - 55))

    if pygame.time.get_ticks() % 1000 < 500:  # Blinks every 0.5s
        cursor_x = 15 + text_surface.get_width()
        pygame.draw.line(screen, (255, 255, 255),
                        (cursor_x, screen.get_height() - 55),
                        (cursor_x, screen.get_height() - 20), 2)

def display_newmsg():
    try:
        msg = chat[-1]

        size = 50
        y = size
        draw_transparent_square(screen, 0, screen.get_height() - y - 10, 9 * len(msg), size, BLACK, 200)

        font = pygame.font.SysFont(None, 24)
        text = font.render(f"{msg}", True, WHITE)
        screen.blit(text, (0, screen.get_height() - y - 10))
    except Exception as e:
        pass

def blocks_8_dir(x,y):
    blocks = []
    blocks.append(get_block_at(x + block_size,y))
    blocks.append(get_block_at(x + block_size, y + block_size))
    blocks.append(get_block_at(x, y + block_size))
    blocks.append(get_block_at(x - block_size, y + block_size))
    blocks.append(get_block_at(x - block_size, y))
    blocks.append(get_block_at(x - block_size, y - block_size))
    blocks.append(get_block_at(x, y - block_size))
    blocks.append(get_block_at(x + block_size, y - block_size))
    return blocks

def try_flow_from(x, y):
    directions = [(0, block_size), (block_size, 0), (-block_size, 0)]
    parent_chunk = get_chunk_coords(x, y)
    parent = flowing_water_chunks.get(parent_chunk, {}).get((x, y))
    source_block = get_block_at(x, y)

    # ✅ Only allow flow from true source or valid flowing water
    if source_block not in ("water", "flowing_water"):
        return

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        target = (nx, ny)

        # ✅ Prevent self-parenting
        if target == (x, y):
            continue

        # ✅ Prevent re-parenting to siblings
        if target == parent:
            continue

        if get_block_at(nx, ny) is None or get_block_at(nx, ny) in breakable_by_water:
            if dy == 0:
                below = get_block_at(x, ny + block_size)
                if below in ("water", "flowing_water") or below is None:
                    continue

            depth = flow_depth.get((x, y), 0)
            if depth >= MAX_DEPTH:
                break

            flow_depth[target] = depth + 1
            if dx == 0:
                flow_depth[target] = 0
            set_block(nx, ny, 'flowing_water')
            chunk = get_chunk_coords(nx, ny)
            flowing_water_chunks.setdefault(chunk, {})[target] = (x, y)
            active_water.add(target)
            break

all_ids = set()

random_chars = string.ascii_letters + string.digits

def generate_id(type,length):
    newid = ''
    while newid in all_ids or newid == '':
        newid = ''
        for char in range(length):
            newid += random.choice(random_chars)
    all_ids.add(newid)
    return f'{type}-{newid}'

item_drops = [

]

class Mob:
    def __init__(self, name, health, damage, position,speed,max_speed,left_hitbox,right_hitbox,width,height, sprite, type, range, drops = None):
        self.name = name
        self.health = health
        self.damage = damage
        self.position = position
        self.sprite = sprite
        self.frame_counter = 0
        self.last_position = self.position
        self.stuck_counter = 0
        self.base_speed = speed
        self.speed = self.base_speed
        self.base_max_speed = max_speed
        self.max_speed = self.base_max_speed
        self.left_hitbox = left_hitbox
        self.right_hitbox = right_hitbox
        self.height = height
        self.width = width
        self.y_vel = 0
        self.x_vel = 0
        self.start_hit = 0
        self.last_hit = 0
        self.last_sky_check = 0
        self.behavior = type
        self.range = block_size * int(range)
        self.emotion = 'Neutral'
        self.dead = False
        self.start_fall = None
        self.mob_id = generate_id('MOB',10)

        if drops is None:
            try:
                self.drops = mob_drops[name]
            except:
                self.drops = None
        else:
            self.drops = drops

        self.target_position = (random.randint(-10, 10) * block_size + position[0],random.randint(-5, 5) * block_size + position[1])
        target_x = self.target_position[0]
        target_y = self.target_position[1]

        max_tries = 100
        tries = 0

        chunk = get_chunk(target_x, target_y)
        if not chunk:
            self.target_position = self.position
            return
        while chunk.get((target_x, target_y)) is not None and tries <= max_tries:
            target_y -= block_size
            tries += 1
        # If target is in air, descend to surface
        tries = 0
        while chunk.get((target_x, target_y)) is None and tries <= max_tries:
            target_y += block_size
            tries += 1
        self.target_position = (target_x, target_y - block_size)

    def get_stat(self, stat):
        return getattr(self, stat, None)

    def to_dict(self):
        """
        Converts the Mob object's critical state into a dictionary for JSON saving.
        This includes current health and position, plus all defining properties
        like speed, damage, and hitboxes for robust loading.
        """
        return {
            'type': self.name,
            'health': self.health,
            'position': [int(self.position[0]), int(self.position[1])],

            # --- All defining stats saved for robustness ---
            'damage': self.damage,
            'speed': self.speed,
            'max_speed': self.max_speed,
            'width': self.width,
            'height': self.height,
            'left_hitbox': self.left_hitbox,
            'right_hitbox': self.right_hitbox,
            'Range': self.range,
            'Behavior': self.behavior

            # Note: We omit 'sprite' and 'drops' as they are defined in mob_definitions.py
            # and should not be saved directly.
        }

    def hit(self,dmg):
        mob_x, mob_y = self.position
        self.health -= dmg
        self.start_hit = time.time()
        if self.health <= 0.0:
            self.dead = True
            chance = random.uniform(1,100)
            for drop in self.drops:
                if int(self.drops[drop]) >= chance:
                    drop_item(drop,self.position[0],self.position[1])
        if not self.dead:
            knockback = min(7.5,dmg * 8)
            if mob_x > player_x:
                self.y_vel = -knockback
                self.x_vel = knockback / 2
            elif mob_x < player_x:
                self.y_vel = -knockback
                self.x_vel = -knockback / 2
            else:
                side = random.randint(1,2)
                if side == 1:
                    self.y_vel = -knockback
                    self.x_vel = knockback / 2
                elif side == 2:
                    self.y_vel = -knockback
                    self.x_vel = -knockback / 2
    def hurt(self,amount):
        mob_x, mob_y = self.position
        self.health -= amount
        self.start_hit = time.time()
        if self.health <= 0.0:
            self.dead = True
            chance = random.uniform(1, 100)
            for drop in self.drops:
                if int(self.drops[drop]) >= chance:
                    drop_item(drop, self.position[0], self.position[1])

    def on_block(self,offset,x = None,y= None):
        if x is None and y is None:
            mob_x, mob_y = self.position
        else:
            mob_x, mob_y = x, y
            if mob_x is None:
                mob_x = self.position[0]
            if mob_y is None:
                mob_y = self.position[1]
        feet_y = mob_y + self.height
        feet_x = mob_x + self.width - offset

        grid_x = (feet_x // block_size) * block_size
        grid_y = (feet_y // block_size) * block_size

        feet_x_2 = mob_x + offset

        grid_x_2 = (feet_x_2 // block_size) * block_size

        return is_collidable(grid_x, grid_y) or is_collidable(grid_x_2, grid_y)

    def above_block(self,offset,x = None,y= None):
        if x is None and y is None:
            mob_x, mob_y = self.position
        else:
            mob_x, mob_y = x, y
            if mob_x is None:
                mob_x = self.position[0]
            if mob_y is None:
                mob_y = self.position[1]
        feet_y = mob_y
        feet_x = mob_x + self.width - offset

        grid_x = (feet_x // block_size) * block_size
        grid_y = (feet_y // block_size) * block_size

        feet_x_2 = mob_x + offset

        grid_x_2 = (feet_x_2 // block_size) * block_size

        return is_collidable(grid_x, grid_y) or is_collidable(grid_x_2, grid_y)

    def side_block(self, offset_x):
        mob_x, mob_y = self.position
        check_points = [
            mob_y,  # top
            mob_y + self.height // 2,  # middle
            mob_y + self.height - 1  # bottom
        ]

        for side_y in check_points:
            side_x = mob_x + offset_x
            grid_x = (side_x // block_size) * block_size
            grid_y = (side_y // block_size) * block_size

            if is_collidable(grid_x, grid_y):
                return True

        return False

    def left_block(self, offset = 0):
        return self.side_block(0)

    def right_block(self, offset = 0):
        return self.side_block(self.right_hitbox)

    def get_new_target(self):
        self.target_position = (
            random.randint(-10, 10) * block_size + self.position[0],
            random.randint(-5, 5) * block_size + self.position[1]
        )
        target_x = self.target_position[0]
        target_y = self.target_position[1]
        chunk = get_chunk(target_x, target_y)
        if not chunk:
            self.target_position = self.position
            return

        # Ascend to find air
        while chunk.get((target_x, target_y)) is not None:
            target_y -= block_size

        # Descend to surface with safety limit
        descent_limit = 10  # max blocks to descend
        descent_count = 0
        while chunk.get((target_x, target_y)) is None and descent_count < descent_limit:
            target_y += block_size
            descent_count += 1

    def move(self):
        mob_x, mob_y = self.position
        target_x, target_y = self.target_position
        chunk = get_chunk(mob_x, mob_y)
        if not chunk:
            return

        if self.start_hit > time.time() - 20 and self.behavior != "Hostile":
            self.emotion = 'Scared'
        else:
            self.emotion = 'Neutral'

        if self.emotion == 'Scared':
            self.speed = self.base_speed + 0.5
            self.max_speed = self.base_max_speed + 3
            if player_x < mob_x:
                self.target_position = (mob_x + block_size * 5, mob_y - block_size * 5)
            elif player_x > mob_x:
                self.target_position = (mob_x - block_size * 5, mob_y - block_size * 5)
            else:
                if random.randint(1,2) == 1:
                    self.target_position = (mob_x - block_size * 5, mob_y - block_size * 5)
                else:
                    self.target_position = (mob_x + block_size * 5, mob_y - block_size * 5)
        elif self.emotion == 'Neutral':
            self.speed = self.base_speed
            self.max_speed = self.base_max_speed

        if self.behavior == "Hostile":
            self.speed = self.base_speed
            self.max_speed = self.base_max_speed
            if player_x > mob_x:
                self.target_position = (mob_x + block_size * 5, mob_y - block_size * 5)
            elif player_x < mob_x:
                self.target_position = (mob_x - block_size * 5, mob_y - block_size * 5)

            start_x = player_x - self.range
            end_x = player_x + self.range

            start_y = player_y - self.range
            end_y = player_y + self.range

            if end_x >= mob_x >= start_x and start_y <= mob_y <= end_y and not self.last_hit > time.time() - 1:
                hurt_player(1)
                self.last_hit = time.time()

            if time.time() - self.last_sky_check > 1:
                self.last_sky_check = time.time()
                exposed = True
                for i in range(1, 10):  # limit to 10 blocks above
                    check_y = self.position[1] - i * block_size
                    if self.above_block(0,y=check_y):
                        exposed = True
                        break
                if exposed:
                    self.hurt(0.5)

        self.frame_counter += 1

        # Retarget if stuck too long
        if self.frame_counter > 600:
            self.get_new_target()
            self.frame_counter = 0
            return

        first_vel = self.x_vel

        # Horizontal movement
        dx = target_x - mob_x
        vel = self.x_vel + self.speed if dx > 0 else self.x_vel - self.speed if dx < 0 else 0
        self.x_vel += self.speed if dx > 0 else -self.speed if dx < 0 else 0
        if not self.x_vel == 0:
            if self.x_vel > 0:
                self.x_vel -= self.speed / 5
                if self.x_vel < 0:
                    self.x_vel = 0
            elif self.x_vel < 0:
                self.x_vel += self.speed / 5
                if self.x_vel > 0:
                    self.x_vel = 0

        if self.x_vel > self.max_speed:
            self.x_vel = self.max_speed
        if self.x_vel < -self.max_speed:
            self.x_vel = -self.max_speed

        step_x = self.x_vel
        if self.x_vel < 0:
            check = self.left_block()
        elif self.x_vel > 0:
            check = self.right_block()
        else:
            check = None

        first = "Right" if mob_x > target_x else "Left" if mob_x < target_x else "On"

        if not check:
            mob_x += step_x
            new_x = mob_x
        else:
            new_x = mob_x
            self.x_vel = 0

        second = "Right" if mob_x > target_x else "Left" if mob_x < target_x else "On"
        if not self.start_hit > time.time() - 0.5 and self.on_block(5):
            if first == "Left":
                if second == "Right":
                    mob_x = target_x
                    self.x_vel = 0
                    self.get_new_target()
                elif second == "On":
                    mob_x = target_x
                    self.x_vel = 0
                    self.get_new_target()
            elif first == "Right":
                if second == "Left":
                    mob_x = target_x
                    self.x_vel = 0
                    self.get_new_target()
                elif second == "On":
                    mob_x = target_x
                    self.x_vel = 0
                    self.get_new_target()
            elif first == "On":
                mob_x = target_x
                self.x_vel = 0
        elif self.start_hit > time.time() - 0.5:
            self.x_vel = first_vel
        new_x = mob_x

        new_y = mob_y

        # Grid snap for terrain checks
        grid_x = int(new_x // block_size) * block_size
        grid_y = int(new_y // block_size) * block_size

        # Check for falling: both hitbox edges must be unsupported
        if self.y_vel < 0:
            self.y_vel += 0.1


        if not self.on_block(5):
            self.y_vel += 1
        elif not self.start_hit > time.time() - 0.1:
            self.y_vel = 0
            y = self.position[1]
            self.position = (self.position[0], y)

        # Smooth jump: if block ahead but space above
        block_ahead = chunk.get((grid_x - block_size, grid_y)) if dx < 0 else chunk.get((grid_x + block_size, grid_y)) if dx > 0 else None
        block_above = chunk.get((grid_x, grid_y - block_size))
        if (block_ahead is not None or self.emotion == "Scared") and self.on_block(5) and not self.start_hit > time.time() - 0.1:
            self.y_vel = -10  # smooth jump

        # Stuck detection
        if self.position == self.last_position:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_position = self.position

        if self.stuck_counter > 60:
            self.get_new_target()
            self.stuck_counter = 0

        while self.on_block(5,y=new_y - 1) and self.x_vel == 0:
            new_y -= 1
        new_temp_y = new_y + self.y_vel
        if self.y_vel < 0:
            above = self.above_block(offset=5,y=new_temp_y)
            if above:
                self.y_vel = 0
        new_y += self.y_vel

        self.position = (new_x, new_y)


        x = self.position[0] - camera_offset[0]
        y = self.position[1] - camera_offset[1]
        screens = 3
        left = screen.get_width() * -(screens - 1)
        if left == -0:
            left = 0
        right = screen.get_width() * screens
        bottom = screen.get_height() * -(screens - 1)
        if bottom == -0:
            bottom = 0
        top = screen.get_height() * screens
        if x + self.width < left or x > right or y < bottom or y + self.height > top:
            self.dead = True

        on_platform = self.on_block(5)


        mob_y = self.position[1]
        if self.start_fall is None and not on_platform and self.y_vel > 0:
            self.start_fall = mob_y

        FALL_DAMAGE_THRESHOLD_BLOCKS = 2

        if on_platform:
            if self.start_fall is not None:

                # Calculate TOTAL distance fallen in PIXEL units
                fall_distance_pixels = mob_y - self.start_fall

                # Calculate TOTAL distance fallen in BLOCK units
                fall_distance_blocks = fall_distance_pixels // block_size

                # --- THE FIX: Damage Calculation ---

                # dmg will be 0 if fall_distance_blocks is 3 or less
                dmg = max(0, fall_distance_blocks - FALL_DAMAGE_THRESHOLD_BLOCKS)

                # Only check the hit-flash if there's actual damage
                if dmg > 0:
                    self.start_hit = time.time()
                    self.hurt(dmg)

                self.start_fall = None



    def draw(self):
        camera_offset = [player_x - screen.get_width() // 2, player_y - screen.get_height() // 2]
        x = self.position[0] - camera_offset[0]
        y = self.position[1] - camera_offset[1]
        screen.blit(self.sprite,(x,y))
        if self.start_hit > time.time() - 0.25:
            mob_width = self.width
            mob_height = self.height

            flash_surface = pygame.Surface((mob_width, mob_height), pygame.SRCALPHA)

            RED_TRANSLUCENT = (255, 0, 0, 128)  # R=255, G=0, B=0, A=128 (50% opaque)

            flash_surface.fill(RED_TRANSLUCENT)

            screen.blit(flash_surface, (x,y))

        # 2. Draw the F3 debug stats if enabled
        if debug and not (x + self.width < 0 or x > screen.get_width() or y < 0 or y + self.height > screen.get_height()):
            stats_lines = [
                f"Name: {self.name}",
                f"Pos: ({int(self.position[0])}, {int(self.position[1])})",
                f"Target Position: ({int(self.target_position[0])},{int(self.target_position[1])})",
                f"Velocity: ({int(self.x_vel)},{int(self.y_vel)})",
                f"Stuck Timer: {self.stuck_counter}",
                f"Path Counter: {self.frame_counter}",
                f"Last Hit: {self.start_hit}",
                f"Last Position: ({int(self.last_position[0])},{int(self.last_position[1])})",
                f"Speed: {self.speed}",
                f"Max Speed: {self.max_speed}",
                f"Is Dead: {self.dead}",
                f"On Platform: {self.on_block(5)}",
                f"Start Fall: {self.start_fall}",
                f"Emotion: {self.emotion}",
                f"Mob ID: {self.mob_id}",
                f"Drops: {self.drops}",
                f"HP: {self.health}",
            ]

            font = pygame.font.Font(None, 25)
            line_height = 25
            padding = 5
            max_width = max(font.render(line, True, (255, 255, 255)).get_width() for line in stats_lines)
            bg_width = max_width + 2 * padding
            bg_height = len(stats_lines) * line_height + 2 * padding

            # Background surface
            bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))

            # Position above mob
            x_pos = self.position[0] + self.width // 2 - bg_width // 2 - camera_offset[0]
            y_pos = self.position[1] - bg_height - 10 - camera_offset[1]

            screen.blit(bg_surface, (x_pos, y_pos))

            # Render each line
            for i, line in enumerate(stats_lines):
                text_surface = font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (x_pos + padding, y_pos + padding + i * line_height))

def blocks_4_dir(x,y):
    blocks = []
    blocks.append(get_block_at(x + block_size, y))
    blocks.append(get_block_at(x - block_size, y))
    blocks.append(get_block_at(x, y - block_size))
    blocks.append(get_block_at(x, y + block_size))
    return blocks

active_water = set()  # contains (x, y) of blocks that should tick
last_tick=0
last_save=0


mob = random.choice(all_mobs)

light_map = {}

BLOCK_SIZE = 50
MAX_LIGHT = 15
AIR_FALLOFF = 0
SOLID_FALLOFF = 2

CHUNK_CALC_RADIUS = 3

def get_day_brightness(tick):
    t = ((tick + 3000) % tick_end) / float(tick_end)
    brightness = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    return brightness  # Value between 0 (night) and 1 (day)


# --- Updated check_tick function ---

def get_tick():
    return tick

def get_sky_light_level(tick):
    brightness = get_day_brightness(tick)
    return round(brightness * 15)  # Scale to 0–15 light level

def update_lighting():
    global light_map
    chunk_pixel_size = block_size * CHUNK_SIZE
    player_chunk_x = player_x // chunk_pixel_size
    player_chunk_y = player_y // chunk_pixel_size

    visible_chunks_list, rendered_chunks_count = calculate_dynamic_range(
        player_chunk_x,
        player_chunk_y,
        chunk_lookup,
        generate_chunk  # <-- Your chunk generator function
    )
    for chunk_pos in visible_chunks_list:
        chunk = chunk_lookup.get(chunk_pos, {})

        # Loop over a copy of the items to allow modification during iteration
        for (x, y), block_type in list(chunk.items()):
            # Light Logic
            default = get_sky_light_level(get_tick())
            block_lights = []
            block_lights.append(light_map.get((x, y + block_size), default))
            block_lights.append(light_map.get((x, y - block_size), default))
            block_lights.append(light_map.get((x + block_size, y), default))
            block_lights.append(light_map.get((x - block_size, y), default))
            light = max(block_lights) - 1
            light_map[(x, y)] = light

lighting_thread_active = False

def update_lighting_wrapper():
    global lighting_thread_active
    update_lighting()
    lighting_thread_active = False

dirty_chunks = set()

def check_tick():
    global last_tick, last_save, tick, tick_end, light_map
    global platforms, chunk_lookup, HP, mobs, items_on_ground, player_inventory
    global player_x, player_y, block_size, CHUNK_SIZE
    global door_variants, fallingblocks, active_water, lighting_thread_active

    # --- 1. Save Logic ---
    if time.time() >= last_save + 5:
        last_save = time.time()
        # --- Using the required full save signature ---
        save_world(platforms, chunk_lookup, mobs, items_on_ground, player_inventory,player_hotbar, HP)

    # --- 2. Tick Check (Runs every 0.1s) ---
    if time.time() >= last_tick + 0.1:
        if not lighting_thread_active:
            lighting_thread_active = True
            threading.Thread(target=update_lighting_wrapper).start()

        tick += 1
        if tick >= tick_end:
            tick = 0
        last_tick = time.time()

        chunk_pixel_size = block_size * CHUNK_SIZE
        player_chunk_x = player_x // chunk_pixel_size
        player_chunk_y = player_y // chunk_pixel_size

        radius = CHUNK_CALC_RADIUS

        player_chunk_x = player_x // chunk_pixel_size
        player_chunk_y = player_y // chunk_pixel_size

        visible_chunks_list, rendered_chunks_count = calculate_dynamic_range(
            player_chunk_x,
            player_chunk_y,
            chunk_lookup,
            generate_chunk  # <-- Your chunk generator function
        )

        # --- PHASE 1: BLOCK BEHAVIOR AND LIGHT SOURCE SEEDING/CLEARING ---
        for chunk_pos in list(dirty_chunks):
            chunk = chunk_lookup.get(chunk_pos, {})

            # Loop over a copy of the items to allow modification during iteration
            for (x, y), block_type in list(chunk.items()):

                # 🪵 Door logic (Top part breaks if bottom is gone)
                if block_type in door_variants.get("top", []):
                    if get_block_at(x, y + block_size) != "oak_door_bottom":
                        platforms.discard((x, y, block_type))
                        get_chunk(x, y).pop((x, y), None)
                        continue

                # 🪵 Door logic (Bottom part breaks if top is gone)
                if block_type in door_variants.get("bottom", []):
                    # Check block ABOVE (y - block_size is up)
                    if get_block_at(x, y - block_size) not in door_variants.get("top", []):
                        platforms.discard((x, y, block_type))
                        get_chunk(x, y).pop((x, y), None)
                        continue

                # 🌱 Grass/Dirt swap (Check block ABOVE for collision)
                if block_type == "grass":
                    if is_collidable_block(get_block_at(x, y - block_size)):
                        platforms.add((x, y, "dirt"))
                        get_chunk(x, y)[(x, y)] = "dirt"
                        continue

                if block_type == "dirt":
                    if not is_collidable_block(get_block_at(x, y - block_size)):
                        platforms.add((x, y, "grass"))
                        get_chunk(x, y)[(x, y)] = "grass"
                        continue

                # 🪨 Falling blocks (Check block BELOW for emptiness)
                if block_type in fallingblocks:
                    block = get_block_at(x, y + block_size)
                    if "powder" in block_type:
                        blocks = blocks_4_dir(x,y)
                        if 'water' in blocks or 'flowing_water' in blocks:
                            platforms.discard((x, y, block_type))
                            get_chunk(x, y).pop((x, y), None)

                            new_block = block_type.split('_powder')[0]
                            new_x = x
                            new_y = y + block_size if block is None or (not is_collidable_block(block)) else y

                            platforms.add((new_x, new_y, new_block))
                            get_chunk(new_x, new_y)[(new_x, new_y)] = new_block
                            continue
                    if block is None or (not is_collidable_block(block)):
                        if block in fallingblocksbreak:
                            platforms.discard((x, y, block_type))
                            get_chunk(x, y).pop((x, y), None)
                            drop_item(block_type,x,y + block_size)
                            continue
                        platforms.add((x, y + block_size, block_type))
                        get_chunk(x, y + block_size)[(x, y + block_size)] = block_type
                        platforms.discard((x, y, block_type))
                        get_chunk(x, y).pop((x, y), None)
                        continue

                # 🧶 Carpet logic (Check block BELOW for emptiness)
                if "carpet" in block_type:
                    if get_block_at(x, y + block_size) is None:
                        platforms.discard((x, y, block_type))
                        get_chunk(x, y).pop((x, y), None)
                        continue

                # 💧 Water logic
                if block_type in ("water", "flowing_water"):
                    try_flow_from(x, y)

        dirty_chunks.clear()

        decay_flowing_water()


def decay_flowing_water():
    player_chunk_x, player_chunk_y = get_chunk_coords(player_x, player_y)

    for dx in range(-1, 2):
        for dy in range(-1, 2):
            chunk_pos = (player_chunk_x + dx, player_chunk_y + dy)
            chunk = flowing_water_chunks.get(chunk_pos, {})
            for (fx, fy), (px, py) in list(chunk.items()):
                parent_block = get_block_at(px, py)
                if parent_block not in ("water", "flowing_water"):
                    platforms.discard((fx, fy, "flowing_water"))
                    get_chunk(fx, fy).pop((fx, fy), None)
                    chunk.pop((fx, fy), None)
                    active_water.discard((fx, fy))
                    flow_depth.pop((fx, fy), None)

door_variants = {
    "bottom": ["oak_door_bottom_closed", "oak_door_bottom_open", "oak_door_bottom"],
    "top": ["oak_door_top_closed", "oak_door_top_open", "oak_door_top"]
}

def safe_int(n):
    try:
        return int(n)
    except:
        return None

def valid_chunk(x, y):
    chunk_x = x // (block_size * CHUNK_SIZE)
    chunk_y = y // (block_size * CHUNK_SIZE)
    chunk_pos = (chunk_x, chunk_y)
    return chunk_pos in chunk_lookup and chunk_lookup[chunk_pos] is not None

with open('Assets/Storage/stats.json') as f:
    item_stats = json.load(f)

CHUNK_SIZE = 16
SCROLL_BUFFER = 1
CHUNK_PIXEL_SIZE = CHUNK_SIZE * BLOCK_SIZE

def get_screen_dimensions():
    """Fetches the current screen width and height."""
    # NOTE: You MUST update these variables whenever the window resizes or goes fullscreen
    surface = pygame.display.get_surface()
    return surface.get_width(), surface.get_height()


def calculate_dynamic_range(chunk_x, chunk_y, chunk_lookup, generate_chunk):  # <-- FIXED: Added generate_chunk argument
    current_width, current_height = get_screen_dimensions()

    # CHUNK_PIXEL_SIZE is assumed to be defined globally or passed in

    # 1. Calculate the absolute minimum chunks needed to cover the screen half-width
    chunks_needed_x_half = (current_width / CHUNK_PIXEL_SIZE) / 2
    chunks_needed_y_half = (current_height / CHUNK_PIXEL_SIZE) / 2

    # 2. Determine the final radius for the iteration
    range_x = math.ceil(chunks_needed_x_half) + SCROLL_BUFFER
    range_y = math.ceil(chunks_needed_y_half) + SCROLL_BUFFER

    visible_chunks = []
    rendered_chunks = 0

    # 3. Iterate using the calculated ranges
    for dx in range(-range_x, range_x + 1):
        for dy in range(-range_y, range_y + 1):
            cx = chunk_x + dx
            cy = chunk_y + dy
            chunk_pos = (cx, cy)

            # 🌱 Auto-generate if missing
            if chunk_pos not in chunk_lookup or chunk_lookup[chunk_pos] is None:
                # This works because generate_chunk is now a local argument
                chunk_lookup[chunk_pos] = generate_chunk(cx, cy)

            visible_chunks.append(chunk_pos)
            rendered_chunks += 1

    # print(f"Loaded {rendered_chunks} chunks. Required Radius: X={range_x}, Y={range_y}")
    return visible_chunks, rendered_chunks

def darkness(light):
     amount = 17 * light
     amount = 255 - amount

     if amount < 0:
         amount = 0
     if amount > 255:
         amount = 255

     return int(amount)

with open('Assets/Storage/BlockStats.json') as f:
    BlockStats = json.load(f)

with open('Assets/Storage/ToolStats.json') as f:
    ToolStats = json.load(f)

start_eat = 0
def updatedisplay():
    global platforms, walked, clicked, HP, item_drops, start_eat, mobs

    if HP > 20:
        HP = 20

    draw_self_as_hit = False

    if not player_start_hit is None:
        if player_start_hit > time.time() - 0.25:
            draw_self_as_hit = True

    if not ininv:
        check_tick()

    animate_blocks()

    rendered_blocks = 0
    rendered_entitys = 1
    rendered_chunks = 0

    if not ininv:
        updatemovement()

    mouse_x, mouse_y = pygame.mouse.get_pos()
    head_x = player_x + 12
    head_y = player_y
    timed = pygame.time.get_ticks()

    camera_offset = [player_x - screen.get_width() // 2, player_y - screen.get_height() // 2]

    world_mouse_x = mouse_x + camera_offset[0]
    world_mouse_y = mouse_y + camera_offset[1]

    # Draw player
    if walked:
        leg_offset = math.sin(timed * 0.01) * 5
        walked = False
        screen.blit(player_legs_texture, (player_x + 19 - camera_offset[0], (player_y - 30) + player_height + leg_offset - camera_offset[1]))
        screen.blit(player_torso_texture, (player_x - camera_offset[0], player_y + 25 - camera_offset[1]))
        screen.blit(player_legs_texture, (player_x + 19 - camera_offset[0], (player_y - 30) + player_height - leg_offset - camera_offset[1]))
    else:
        screen.blit(player_torso_texture, (player_x - camera_offset[0], player_y + 25 - camera_offset[1]))
        screen.blit(player_legs_texture, (player_x + 19 - camera_offset[0], player_y + (player_height - 28) - camera_offset[1]))

    if draw_self_as_hit:
        # Create a transparent surface
        overlay = pygame.Surface((player_width - 38, player_height), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 200))  # Red with 100 alpha (adjust for intensity)

        # Position it over the player
        overlay_x = player_x + 19 - camera_offset[0]
        overlay_y = player_y + 3 - camera_offset[1]

        # Draw it last so it overlays everything
        screen.blit(overlay, (overlay_x, overlay_y))

    # Arm logic
    if clicked is not None:
        angle = -45
        if world_mouse_x < player_x:
            angle = -135
            x_offset = player_x - 5 if angle == -135 else player_x + 19
        else:
            x_offset = player_x + 19
        rotated_arm = pygame.transform.rotate(player_arm_texture, angle)
        screen.blit(rotated_arm, (x_offset - camera_offset[0], player_y + 25 - camera_offset[1]))
        if draw_self_as_hit:
            # Create a transparent red overlay
            overlay = pygame.Surface((player_arm_texture.get_width(), player_arm_texture.get_height()), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 200))

            # Rotate the overlay
            rotated_overlay = pygame.transform.rotate(overlay, angle)

            # Get the new rect and center it on the arm
            overlay_rect = rotated_overlay.get_rect(
                center=(x_offset + 18 - camera_offset[0], player_y + 43 - camera_offset[1]))

            # Draw it
            screen.blit(rotated_overlay, overlay_rect.topleft)

    else:
        rotated_arm = pygame.transform.rotate(player_arm_texture, -90)
        screen.blit(rotated_arm, (player_x + 19 - camera_offset[0], player_y + 25 - camera_offset[1]))
        if draw_self_as_hit:
            # Create a transparent red overlay
            overlay = pygame.Surface((player_arm_texture.get_width(), player_arm_texture.get_height()), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 200))

            # Rotate the overlay
            rotated_overlay = pygame.transform.rotate(overlay, -90)

            # Get the new rect and center it on the arm
            overlay_rect = rotated_overlay.get_rect(
                center=(player_x + 25 - camera_offset[0], player_y + 45 - camera_offset[1]))

            # Draw it
            screen.blit(rotated_overlay, overlay_rect.topleft)

    # Head rotation
    dx = world_mouse_x - head_x
    dy = world_mouse_y - head_y
    angle = math.degrees(math.atan2(-dy, dx))
    head_texture = player_head_right_texture if world_mouse_x >= player_x else player_head_left_texture
    rotated_head = pygame.transform.rotate(head_texture, angle)
    rotated_rect = rotated_head.get_rect(center=(head_x + 13 - camera_offset[0], head_y + 13 - camera_offset[1]))
    screen.blit(rotated_head, rotated_rect.topleft)
    if draw_self_as_hit:
        # Create a transparent surface
        overlay = pygame.Surface((head_texture.get_width(), head_texture.get_height()), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 200))  # Red with 100 alpha (adjust for intensity)

        # Position it over the player
        overlay_x = player_x + 19 - camera_offset[0]
        overlay_y = player_y + 3 - camera_offset[1]

        rotated_overlay = pygame.transform.rotate(overlay, angle)

        rotated_rect = rotated_head.get_rect(center=(head_x + 13 - camera_offset[0], head_y + 13 - camera_offset[1]))

        # Draw it last so it overlays everything
        screen.blit(rotated_overlay, rotated_rect.topleft)

    # A. Calculate the current chunk the camera is centered on (in chunk coordinates)
    # camera_offset[0] is the world coordinate of the top-left of the screen
    current_chunk_x = int(camera_offset[0] // CHUNK_PIXEL_SIZE)  # Use CHUNK_PIXEL_SIZE here
    current_chunk_y = int(camera_offset[1] // CHUNK_PIXEL_SIZE)  # Use CHUNK_PIXEL_SIZE here

    # B. Load/Get the list of chunks currently visible
    # <-- FIXED: Unpack the tuple into two variables and pass the generate_chunk function
    visible_chunks_list, rendered_chunks_count = calculate_dynamic_range(
        current_chunk_x,
        current_chunk_y,
        chunk_lookup,
        generate_chunk  # <-- Your chunk generator function
    )

    # Update your local tracking variable
    rendered_chunks = rendered_chunks_count

    visible_rect = pygame.Rect(
        camera_offset[0] - block_size,
        camera_offset[1] - block_size,
        screen.get_width() + block_size * 2,
        screen.get_height() + block_size * 2
    )

    # Draw blocks
    # <-- FIXED: Iterate directly over the visible_chunks_list
    for chunk_pos in visible_chunks_list:
        chunk = chunk_lookup.get(chunk_pos, None)
        try:
            # Your chunk data is assumed to be a dictionary where keys are (block_x, block_y)
            # You might want to ensure 'chunk' is not None before iterating
            if chunk:
                for (block_x, block_y), name in chunk.items():
                    # The chunk key coordinates (cx, cy) are in CHUNK units,
                    # but the data inside the chunk seems to be in PIXEL units already.
                    # block_x and block_y are the world pixel coordinates of the block.

                    if visible_rect.collidepoint(block_x, block_y):
                        draw_x = block_x
                        # You may need to revisit this 'carpet' logic if it causes issues
                        draw_y = block_y if 'carpet' not in name else block_y + 45
                        light = light_map[(int(block_x), int(block_y))] if (int(block_x), int(block_y)) in light_map else 15
                        texture = block_textures.get(name, block_textures['Missing_Block'])

                        # Apply camera offset to world coordinates to get screen coordinates
                        light_overlay = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
                        dark_color = (0,0,0,darkness(light))
                        light_overlay.fill(dark_color)
                        screen.blit(texture, (draw_x - camera_offset[0], draw_y - camera_offset[1]))
                        screen.blit(light_overlay,(draw_x - camera_offset[0],draw_y - camera_offset[1]))
                        rendered_blocks += 1
        except Exception as e:
            # Catching exceptions during drawing is good for debugging
            print(f"Error drawing chunk {chunk_pos}: {e}")
            pass  # Keep it running
    FIXED_PULL_SPEED = 9

    picked_up_info = []  # Stores (item_name) for processing (healing/inventory)
    new_item_drops = []  # List for items that remain on the ground after this frame

    player_center_y = player_y + player_height // 2
    player_center_x = player_x + player_width // 2

    for item_name, position in item_drops:

        # Unpack item position
        current_x, current_y = position

        animation = math.sin(timed * 0.01) * 5
        size = 25
        pickup_range = block_size + block_size // 2

        x = player_center_x
        y = player_center_y

        item_center_x = current_x + size // 2
        item_center_y = current_y + size // 2

        is_picked_up = False
        new_position = position
        start_x = current_x - pickup_range
        end_x = current_x + pickup_range
        start_y = current_y - pickup_range
        end_y = current_y + pickup_range

        if start_x <= x <= end_x and start_y <= y <= end_y:
            dx = player_center_x - item_center_x
            dy = player_center_y - item_center_y

            distance = math.sqrt(dx ** 2 + dy ** 2)

            # Immediate pickup check (if very close)
            if distance < FIXED_PULL_SPEED:
                picked_up_info.append(item_name)
                is_picked_up = True

            else:
                vx = dx / distance
                vy = dy / distance

                new_x = current_x + (vx * FIXED_PULL_SPEED)
                new_y = current_y + (vy * FIXED_PULL_SPEED)
                new_position = (new_x, new_y)
            if not is_picked_up:
                new_item_drops.append((item_name, new_position))
        else:
            if not on_block_item(position[0],position[1],25, y_offset=25):
                y = position[1] + 5
                x = position[0]
                position = (x,y)
            new_item_drops.append((item_name, position))

        if not is_picked_up:
            texture = pygame.transform.scale(all_textures[item_name], (size, size))
            screen.blit(
                texture,
                (new_position[0] - camera_offset[0] + size // 2,
                 new_position[1] - camera_offset[1] + animation + size // 2)
            )
            rendered_entitys += 1

    item_drops = new_item_drops

    for item_name in picked_up_info:
        add_block(item_name)

    for _ in spawns:
        mobs.append(Mob(_['name'],_['HP'],_["DMG"],_["Pos"],_["speed"],_["max_speed"],_['left_hitbox'],_['right_hitbox'],_['width'],_['height'],_['texture'],_['Behavior'],_['range']))
        spawns.remove(_)

    # Grid highlight

    grid_x = (world_mouse_x // block_size) * block_size
    grid_y = (world_mouse_y // block_size) * block_size

    reach_blocks_x = 4
    reach_blocks_y = 4

    # Convert player position to grid
    player_grid_x = (player_x // block_size) * block_size
    player_grid_y = (player_y // block_size) * block_size

    dx = grid_x - player_grid_x
    dy = grid_y - player_grid_y

    # Clamp X
    if abs(dx) > block_size * reach_blocks_x:
        grid_x = player_grid_x + block_size * reach_blocks_x * (1 if dx > 0 else -1)

    # Clamp Y
    if abs(dy) > block_size * reach_blocks_y:
        grid_y = player_grid_y + block_size * reach_blocks_y * (1 if dy > 0 else -1)

    pygame.draw.rect(screen, BLACK, (grid_x - camera_offset[0], grid_y - camera_offset[1], block_size, block_size), 2)

    # Block placement/breaking
    if clicked is not None:
        if not pygame.mouse.get_pressed()[2] and not pygame.mouse.get_pressed()[0]:
            clicked = None

    block = get_block_at(grid_x, grid_y)
    selected_block = player_hotbar[player_hotbar_selected][0]

    if not ininv:
        if pygame.mouse.get_pressed()[keybind['Place'] - 1]:  # Right click
            player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
            block_rect = pygame.Rect(grid_x, grid_y, block_size, block_size)
            if selected_block != '' and selected_block not in item_textures and block is None and not player_rect.colliderect(block_rect):
                if clicked is not None:
                    clicked += 1
                else:
                    clicked = 1
                set_block(grid_x, grid_y, selected_block)
                remove_block('Hot',player_hotbar_selected)

                if selected_block in door_variants["bottom"]:
                    if get_block_at(grid_x, grid_y - block_size) is None:
                        set_block(grid_x, grid_y - block_size, "oak_door_top")
                    else:
                        block = get_block_at(grid_x, grid_y)
                        platforms.discard((grid_x, grid_y, block))
                        get_chunk(grid_x, grid_y).pop((grid_x, grid_y), None)

                    if get_block_at(grid_x, grid_y + block_size) is None:
                        block = get_block_at(grid_x, grid_y)
                        platforms.discard((grid_x, grid_y, block))
                        get_chunk(grid_x, grid_y).pop((grid_x, grid_y), None)
                        block = get_block_at(grid_x, grid_y - block_size)
                        platforms.discard((grid_x, grid_y - block_size, block))
                        get_chunk(grid_x, grid_y - block_size).pop((grid_x, grid_y - block_size), None)
            elif selected_block in item_textures:
                if start_eat < time.time() - 0.5:
                    stats = item_stats[selected_block]
                    if stats['Usable']:
                        remove_block('Hot', player_hotbar_selected)
                        HP += stats['Heal']
                    start_eat = time.time()

        if pygame.mouse.get_pressed()[keybind['Attack'] - 1]:  # Left click
            if clicked is not None:
                clicked += 1
            else:
                clicked = 1
            click_length_ticks = clicked // 6
            block = get_block_at(grid_x, grid_y)
            tool_speed = ToolStats.get(selected_block, {}).get("Speed", 1.0)
            if float(tool_speed) < 1:
                tool_speed = 1
            block_stats = BlockStats[block] if block is not None else {"hardness": 0.0,"tool": "all","dropabletool": ["all"],"transparent": True,"drops": ['']}
            required_ticks = max(0.1,float(block_stats['hardness']) * 30 / float(tool_speed))
            crack_stage = min(9, int((click_length_ticks / required_ticks) * 10))
            if not required_ticks == 0.1:
                screen.blit(all_textures[f'destroy_stage_{crack_stage}'],(grid_x - camera_offset[0],grid_y - camera_offset[1]))
            if not block in unbreakable_blocks:
                if click_length_ticks >= required_ticks:
                    clicked = 0
                    platforms.discard((grid_x, grid_y, block))
                    get_chunk(grid_x, grid_y).pop((grid_x, grid_y), None)
                    if not block is None:
                        drop_item(block,grid_x,grid_y)
                    key = (int(grid_x), int(grid_y))
                    if key in light_map:
                        del light_map[key]

                    if block == "oak_door_top":
                        if get_block_at(grid_x, grid_y + block_size) == "oak_door_bottom":
                            platforms.discard((grid_x, grid_y + block_size, "oak_door_bottom"))
                            get_chunk(grid_x, grid_y + block_size).pop((grid_x, grid_y + block_size), None)

    for mob in mobs:
        if not ininv:
            mob.move()
        mob.draw()
        rendered_entitys += 1
    mobs = [m for m in mobs if not m.get_stat('dead')]

    if draw_self_as_hit:
        overlay = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 100))  # Red with 100 alpha (adjust for intensity)

        # Position it over the player
        overlay_x = 0
        overlay_y = 0

        # Draw it last so it overlays everything
        screen.blit(overlay, (overlay_x, overlay_y))

    draw_hotbar()

    if ininv:
        draw_inventory()

    clock.tick(60)

    font = pygame.font.SysFont(None, 24)
    if debug:
        current_fps = int(clock.get_fps())

        debug_text = [
            f"--- PERFORMANCE & TIME ---",
            f"FPS: {current_fps}",
            f"Tick: {tick} / {tick_end}",
            "",
            f"--- PLAYER STATE & MOVEMENT ---",
            f"Player Pos: ({player_x:.2f},{player_y:.2f})",
            f"Player Height: {player_height} px",
            f"Player Width: {player_width} px",
            f"Player Velocity: ({speed:.2f},{player_y_vel:.2f})",
            f"Player Crouching: {not crouched}",
            f"Player Sprinting: {sprint}",
            f"Player Health: {HP}",
            "",
            f"--- INTERACTION & SYSTEM ---",
            f"Selected Grid: ({grid_x},{grid_y})",
            f"Mouse World Pos: ({mouse_x + camera_offset[0]},{mouse_y + camera_offset[1]})",
            f"Selected Slot: {player_hotbar_selected}",
            f"Selected Block: {player_hotbar[player_hotbar_selected]}",
            f"Save File Name: {loaded_world}",
            f"Game Engine:[",
            f"    Python version {sys.version.split(' ')[0]}",
            f"    Pygame version {pygame.version.ver}",
            f"]",
            "",
            f"--- RENDERING ---",
            f"Rendered Blocks: {rendered_blocks}",
            f"Rendered Chunks: {rendered_chunks}",
            f"Rendered Entities: {rendered_entitys}",
            "",
            f"--- GAME INFO ---",
            f"Name: MineFlat InvDev",
            f"Version: InvDev 0.6"
        ]

        # Find all section header indices
        section_indices = [i for i, line in enumerate(debug_text) if line.startswith("---")]

        # Choose split point: slice right before midpoint header
        split_index = section_indices[len(section_indices) // 2]
        left_lines = debug_text[:split_index]
        right_lines = debug_text[split_index:]

        def draw_debug_column(lines, x_offset):
            max_width = max(font.render(line, True, (255, 255, 255)).get_width() for line in lines)
            line_height = 20
            padding = 5
            bg_width = max_width + 2 * padding
            bg_height = len(lines) * line_height + 2 * padding


            if x_offset >= screen.get_height():
                x_offset -= bg_width

            # Semi-transparent background
            s = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, (x_offset, 0))

            # Render each line
            for i, line in enumerate(lines):
                text_surface = font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (x_offset + padding, padding + i * line_height))

        # Draw both columns
        draw_debug_column(left_lines, 0)
        draw_debug_column(right_lines, screen.get_width())

    if inchat:
        display_chat()

def get_sky_color(tick):
    brightness = get_day_brightness(tick)

    day_color   = (135, 206, 235)
    night_color = (20, 24, 45)
    tint_color  = (255, 120, 80)

    r = night_color[0] + (day_color[0] - night_color[0]) * brightness
    g = night_color[1] + (day_color[1] - night_color[1]) * brightness
    b = night_color[2] + (day_color[2] - night_color[2]) * brightness

    t = ((tick-300) % tick_end) / float(tick_end)
    tint_strength = math.sin(t * math.pi) ** 2

    r += (tint_color[0] - r) * tint_strength * 0.3
    g += (tint_color[1] - g) * tint_strength * 0.3
    b += (tint_color[2] - b) * tint_strength * 0.3

    return (int(r), int(g), int(b))



def resolve_inventory_list(inv_type, row):
    if inv_type == "base":
        actual_row = row + invscroll
        if 0 <= actual_row < len(player_inventory):
            return player_inventory[actual_row]
    elif inv_type == "hotbar":
        return player_hotbar
    elif inv_type == "crafting":
        return crafting_grid[row]
    elif inv_type == "output":
        return [crafting_output]
    elif inv_type == "offhand":
        print([player_offhand], [crafting_output])
        return [player_offhand]
    return None


chat = []
inchat = False
ininv = False
music_thread = threading.Thread(target=play_music_loop, daemon=True)
music_thread.start()
typing_thread = threading.Thread(target=typechat, daemon=True)
typing_thread.start()
# add mod option later


# Game loop
running = True
last = None
debug = False

while running:
    player_pos = (player_x,player_y)
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    camera_offset = [player_pos[0] - screen_width // 2, player_pos[1] - screen_height // 2]

    for event in pygame.event.get():
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if event.type == pygame.QUIT:  # Close the window
            running = False

        # --- Mouse Wheel Scrolling (Inventory) ---
        elif event.type == pygame.MOUSEWHEEL and ininv:
            if event.y < 0:  # scroll down
                if not invscroll + 3 >= len(player_inventory):
                    invscroll += 1
            elif event.y > 0:  # scroll up
                if not invscroll < 1:
                    invscroll -= 1

        # --- Key Down Handling (Consolidated) ---
        elif event.type == pygame.KEYDOWN:
            # General Game Keybinds
            if event.key == pygame.K_F2 or event.key == pygame.K_p:
                save_screenshot(screen)
            elif event.key == pygame.K_F3:
                debug = not debug
            elif event.key == keybind["Chat"]:
                inchat = not inchat
            elif event.key == keybind["Inventory"]:
                ininv = not ininv
            elif event.key == keybind["Offhand"]:
                safe = player_offhand
                player_offhand = player_hotbar[player_hotbar_selected]
                player_hotbar[player_hotbar_selected] = safe
            elif event.key == pygame.K_y:
                if not test_mode:
                    add_block(random.choice(all_blocks))
                else:
                    add_block(test_block)

        # --- Mouse Button Down Handling (Inventory Pickup OR Mob Attack) ---
        # Note: Using 'if' here instead of 'elif' to allow multiple non-mutually exclusive events to fire if needed,
        # but the inner logic uses an if/else to prioritize inventory when open.
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_button = event.button  # 1 = left, 3 = right
            right_click = True if int(keybind["Place"]) == int(mouse_button) else False
            left_click = True if int(keybind["Attack"]) == int(mouse_button) else False
            slot = get_slot_under_mouse()

            if slot and ininv:
                inv_type, row, col = slot

                if inv_type == "offhand":
                    item, stack = player_offhand
                    if not dragging and player_offhand != no_block:
                        if left_click:
                            dragged_item = player_offhand
                            drag_source = slot
                            player_offhand = no_block
                            dragging = True
                        elif right_click:
                            half = (stack + 1) // 2
                            dragged_item = (item, half)
                            drag_source = slot
                            player_offhand = (item, stack - half)
                            dragging = True
                    elif dragging:
                        held_item, held_stack = dragged_item
                        if player_offhand == no_block or player_offhand[0] == held_item:
                            if left_click:
                                if player_offhand == no_block:
                                    player_offhand = dragged_item
                                else:
                                    player_offhand = (held_item, player_offhand[1] + held_stack)
                                dragged_item = no_block
                                dragging = False
                                drag_source = None
                            elif right_click:
                                if player_offhand == no_block:
                                    player_offhand = (held_item, 1)
                                else:
                                    player_offhand = (held_item, player_offhand[1] + 1)
                                if held_stack > 1:
                                    dragged_item = (held_item, held_stack - 1)
                                else:
                                    dragged_item = no_block
                                    dragging = False
                                    drag_source = None
                elif inv_type == "output":
                    remove_all = True
                    if not dragging and crafting_output != no_block:
                        if left_click:
                            dragged_item = crafting_output
                            drag_source = slot
                            crafting_output = no_block
                            dragging = True
                    elif dragging and dragged_item[0] == crafting_output[0] and crafting_output != no_block:
                        if left_click:
                            dragged_item = (crafting_output[0], dragged_item[1] + crafting_output[1])
                            drag_source = slot
                            crafting_output = no_block
                            dragging = True
                    else:
                        remove_all = False
                    for row_num, row in enumerate(crafting_grid[:]):
                        for item_num, item in enumerate(row):
                            block, stack = item
                            stack = max(0, int(stack) - 1)
                            if stack == 0:
                                crafting_grid[row_num][item_num] = ('', 0)
                            else:
                                crafting_grid[row_num][item_num] = (block, stack)
                else:
                    current_list = resolve_inventory_list(inv_type, row)
                    if current_list and current_list[col] != no_block:
                        item, stack = current_list[col]
                        if not dragging:
                            if left_click:
                                dragged_item = current_list[col]
                                drag_source = slot
                                current_list[col] = no_block
                                dragging = True
                            elif right_click:
                                half = (stack + 1) // 2
                                dragged_item = (item, half)
                                drag_source = slot
                                current_list[col] = (item, stack - half)
                                dragging = True
                        else:
                            held_item, held_stack = dragged_item
                            if left_click:
                                if item == held_item or item == '':
                                    current_list[col] = (item, stack + held_stack)
                                    dragged_item = no_block
                                    dragging = False
                                    drag_source = None
                            elif right_click:
                                if item == held_item or item == '':
                                    if item == '':
                                        current_list[col] = (held_item, 1)
                                    else:
                                        current_list[col] = (held_item, stack + 1)
                                    if held_stack > 1:
                                        dragged_item = (held_item, held_stack - 1)
                                    else:
                                        dragged_item = no_block
                                        dragging = False
                                        drag_source = None
                    elif dragging and current_list:
                        held_item, held_stack = dragged_item
                        target_item, target_stack = current_list[col]
                        if left_click:
                            if target_item == held_item or target_item == '':
                                current_list[col] = dragged_item
                                dragged_item = no_block
                                dragging = False
                            else:
                                current_list[col], dragged_item = dragged_item, current_list[col]
                        elif right_click:
                            if target_item == held_item or target_item == '':
                                if target_item == '':
                                    current_list[col] = (held_item, 1)
                                else:
                                    current_list[col] = (held_item, target_stack + 1)
                                if held_stack > 1:
                                    dragged_item = (held_item, held_stack - 1)
                                else:
                                    dragged_item = no_block
                                    dragging = False

            elif left_click:
                # Mob attack logic
                click_world_x = mouse_x + camera_offset[0]
                click_world_y = mouse_y + camera_offset[1]
                MAX_PUNCH_RANGE = float(block_size) * 4
                player_center_x = player_x + player_width // 2
                player_center_y = player_y + player_height // 2
                dx_click = click_world_x - player_center_x
                dy_click = click_world_y - player_center_y
                distance_to_click = math.sqrt(dx_click ** 2 + dy_click ** 2)

                if distance_to_click > MAX_PUNCH_RANGE:
                    vx = dx_click / distance_to_click
                    vy = dy_click / distance_to_click
                    clamped_x = player_center_x + (vx * MAX_PUNCH_RANGE)
                    clamped_y = player_center_y + (vy * MAX_PUNCH_RANGE)
                else:
                    clamped_x = click_world_x
                    clamped_y = click_world_y

                for mob in mobs:
                    mobx, moby = mob.get_stat('position')
                    mobwidth = mob.get_stat('width')
                    mobheight = mob.get_stat('height')
                    selected_item = player_hotbar[player_hotbar_selected][0]

                    if (mobx <= clamped_x <= mobx + mobwidth and
                            moby <= clamped_y <= moby + mobheight):
                        mob_center_x = mobx + mobwidth // 2
                        mob_center_y = moby + mobheight // 2
                        dx = mob_center_x - player_center_x
                        dy = mob_center_y - player_center_y
                        distance = math.sqrt(dx ** 2 + dy ** 2)

                        if distance <= MAX_PUNCH_RANGE + mobwidth:
                            tool_dmg = ToolStats.get(selected_item, {}).get("Attack", 0.5)
                            mob.hit(tool_dmg)
                            break

                mobs = [m for m in mobs if not m.get_stat('dead')]

            pass

    if HP <= 0:
        player_x = random.randint(-350,350)
        player_y = 0
        HP = 20

    # Fill the screen with white
    screen.fill(get_sky_color(tick))

    # Detect movement
    # Get all currently held keys
    keys = pygame.key.get_pressed()

    mods = pygame.key.get_mods()

    # Example: Move player with WASD
    crouch = keys[keybind['Crouch']]
    sprint = keys[keybind['Sprint']] and not crouch
    if sprint == 0:
        sprint = False
    speed = 0
    if sprint:
        speed += 3
    if not crouch:
        speed += 5
    else:
        speed += 3
    if keys[keybind['Jump']]:
        if (not jump and on_block()) or (block_player_inside() in ('water','flowing_water')):
            player_jump()
    if keys[keybind['Left']]:
        if not ininv:
            if not left_block():
                player_x -= speed
                safe = not on_block() and crouch and last
                if safe:
                    player_x += speed
            walked = True
    if keys[keybind['Right']]:
        if not ininv:
            if not right_block():
                player_x += speed
                safe = not on_block() and crouch and last
                if safe:
                    player_x -= speed
            walked = True
    if keys[keybind['Climb']]:
        if block_player_inside() in climbable_blocks:
            player_y_vel = 0
            if not above_block():
                player_y -= 5
            startfall = None

    if crouch:
        # Attempt to crouch
        if not crouched and not above_block():
            player_y += player_height_base - player_height_crouch
            crouched = True
        player_height = player_height_crouch
    else:
        # Attempt to uncrouch
        player_height = player_height_base
        if crouched and not above_block():
            player_y -= player_height_base - player_height_crouch
            crouched = False
        elif crouched:
            player_height = player_height_crouch

    max_tries = 100
    left_amt = 0
    right_amt = 0
    start = player_x

    # Test left
    while left_block() and left_amt < max_tries:
        player_x += 1
        left_amt += 1

    # Test right
    player_x = start
    while right_block() and right_amt < max_tries:
        player_x -= 1
        right_amt += 1

    player_x = start

    # Choose direction
    if left_amt < right_amt:
        player_x += left_amt
    elif right_amt < left_amt:
        player_x -= right_amt

    for i in range(1, 10):
        key_code = keybind["Hotbar"][str(i)]
        if keys[key_code]:
            player_hotbar_selected = i - 1

    # Update Visuals

    if not walked:
        speed = 0

    updatedisplay()

    if latestmsg + 2 > time.time():
        display_newmsg()


    # Update the display/home/blake/PycharmProjects

    pygame.display.flip()

    last = on_block()

    clock.tick(60)

# make a log file
log('Game Closed, without bugs (at least, it didnt crash)')
os.chdir(os.path.dirname(__file__))
os.makedirs('Logs', exist_ok=True)
os.chdir(f'{os.path.dirname(__file__)}/Logs')
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# Quit PyGame
pygame.quit()
sys.exit()