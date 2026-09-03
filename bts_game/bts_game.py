# File Name: bts_game.py

import pygame
import random
import os

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800

# OPTIMIZATION: Use DOUBLEBUF to hardware-accelerate screen redraws
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("Catch the Army Bomb!")
clock = pygame.time.Clock()

# Colors & Fonts
PURPLE = (141, 118, 215)
LIGHT_PURPLE = (90, 50, 100)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)

font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 64)
small_font = pygame.font.SysFont(None, 24)

# CHIBI PROPORTIONS
CHIBI_WIDTH = 75
CHIBI_HEIGHT = 120

# Pre-render static text surfaces
TITLE_SURF = large_font.render("CATCH THE ARMY BOMB!", True, WHITE)
SUBTITLE_SURF = font.render("Use Left/Right Arrows or Click to Select Character, Press Enter/Click to Play", True, WHITE)
GAMEOVER_SURF = large_font.render("GAME OVER", True, WHITE)
RESTART_SURF = font.render("Press Enter or Click to Return to Character Select", True, WHITE)
SELECTED_LABEL = small_font.render("SELECTED", True, YELLOW)
MULT_3X_SURF = font.render("COMEBACK MULTIPLIER: 3x!", True, (255, 120, 255))

# Dynamic Audio Track Switcher
current_track = None

def play_bg_music(filename):
    global current_track
    if current_track == filename:
        return  # Already playing this track

    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check both the script folder and a 'music' subfolder
    file_path = os.path.join(script_dir, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(script_dir, "music", filename)

    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
        current_track = filename
    except Exception as e:
        print(f"Audio notice: '{filename}' not playing ({e})")

# Exact Character Asset Mapping
character_assets = {
    "RM": "images/rm.png",       
    "Jin": "images/jin.png",     
    "Suga": "images/suga.png",   
    "J-Hope": "images/jhope.png", 
    "Jimin": "images/jimin.png", 
    "V": "images/v.png",         
    "Jungkook": "images/jungkook.png"   
}
members = list(character_assets.keys())

# Pre-render member name surfaces
member_name_surfs = {member: font.render(member, True, WHITE) for member in members}

# Load Character Images safely with slim proportions
character_images = {}
for member, filename in character_assets.items():
    try:
        img = pygame.image.load(filename).convert_alpha()
        img = pygame.transform.scale(img, (CHIBI_WIDTH, CHIBI_HEIGHT))
    except Exception:
        img = pygame.Surface((CHIBI_WIDTH, CHIBI_HEIGHT))
        img.fill(PURPLE)
    character_images[member] = img

# Load Game Items safely
def load_item(filename, size):
    try:
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception:
        surf = pygame.Surface(size)
        surf.fill(WHITE)
        return surf

bomb_img = load_item("images/bts_bomb.png", (45, 65))
toast_img = load_item("images/burnttoast.png", (55, 55))
heart_img = load_item("images/heart.png", (35, 35))

# Game Variables & States
game_state = "SELECT"
selected_index = 0

player_width = CHIBI_WIDTH
player_height = CHIBI_HEIGHT
player_x = SCREEN_WIDTH // 2 - player_width // 2
player_y = SCREEN_HEIGHT - 160

score = 0
last_score = -1
score_surf = None
final_score_surf = None

lives = 3
multiplier = 1

falling_items = []
spawn_timer = 0

# Helper function to switch states and music cleanly
def switch_state(new_state):
    global game_state
    game_state = new_state
    if game_state == "PLAYING":
        pygame.mouse.set_visible(False)
        play_bg_music("swim.mp3")
    elif game_state == "SELECT":
        pygame.mouse.set_visible(True)
        play_bg_music("dynamite.mp3")
    elif game_state == "GAMEOVER":
        pygame.mouse.set_visible(True)

def reset_game():
    global score, last_score, score_surf, lives, multiplier, falling_items, player_x
    score = 0
    last_score = -1
    score_surf = font.render("Score: 0", True, WHITE)
    lives = 3
    multiplier = 1
    falling_items = []
    player_x = SCREEN_WIDTH // 2 - player_width // 2

# Start selection screen music on launch
play_bg_music("dynamite.mp3")

running = True
while running:
    screen.fill(PURPLE)
    
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "SELECT":
                reset_game()
                switch_state("PLAYING")
            elif game_state == "GAMEOVER":
                switch_state("SELECT")

        elif event.type == pygame.KEYDOWN:
            if game_state == "SELECT":
                if event.key == pygame.K_LEFT:
                    selected_index = (selected_index - 1) % len(members)
                elif event.key == pygame.K_RIGHT:
                    selected_index = (selected_index + 1) % len(members)
                elif event.key == pygame.K_RETURN:
                    reset_game()
                    switch_state("PLAYING")
                    
            elif game_state == "GAMEOVER":
                if event.key == pygame.K_RETURN:
                    switch_state("SELECT")

    # Gameplay Logic
    if game_state == "PLAYING":
        # Smooth Mouse Control with boundary checks
        mouse_x, _ = pygame.mouse.get_pos()
        player_x = mouse_x - player_width // 2
        player_x = max(20, min(SCREEN_WIDTH - player_width - 20, player_x))

        # Item Spawning
        spawn_timer += 1
        if spawn_timer > 30:
            spawn_timer = 0
            item_type = "toast" if random.random() < 0.3 else "bomb"
            item_x = random.randint(50, SCREEN_WIDTH - 100)
            falling_items.append({"x": item_x, "y": -70, "speed": random.randint(5, 8), "type": item_type})

        # Update Item Positions and Collisions
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for item in falling_items[:]:
            item["y"] += item["speed"]
            
            item_rect = pygame.Rect(item["x"], item["y"], 45, 55)
            if player_rect.colliderect(item_rect):
                if item["type"] == "bomb":
                    score += 10 * multiplier
                elif item["type"] == "toast":
                    lives -= 1
                    if lives == 1:
                        multiplier = 3  
                    elif lives <= 0:
                        final_score_surf = font.render(f"Final Score: {score}", True, YELLOW)
                        switch_state("GAMEOVER")
                falling_items.remove(item)
            elif item["y"] > SCREEN_HEIGHT:
                falling_items.remove(item)

        # Update score surface only on value change
        if score != last_score:
            score_surf = font.render(f"Score: {score}", True, WHITE)
            last_score = score

    # Drawing Screens
    if game_state == "SELECT":
        screen.blit(TITLE_SURF, (SCREEN_WIDTH // 2 - TITLE_SURF.get_width() // 2, 80))
        screen.blit(SUBTITLE_SURF, (SCREEN_WIDTH // 2 - SUBTITLE_SURF.get_width() // 2, 150))
        
        total_members = len(members)
        card_width = 150
        card_height = 240
        spacing = (SCREEN_WIDTH - (total_members * card_width)) // (total_members + 1)
        y_pos = 280
        
        for i, member in enumerate(members):
            x_pos = spacing + i * (card_width + spacing)
            card_rect = pygame.Rect(x_pos, y_pos, card_width, card_height)
            
            if i == selected_index:
                pygame.draw.rect(screen, LIGHT_PURPLE, card_rect)
                pygame.draw.rect(screen, YELLOW, card_rect, 4)  
            else:
                pygame.draw.rect(screen, (35, 18, 40), card_rect)
                pygame.draw.rect(screen, PURPLE, card_rect, 2)
                
            chibi_img = character_images[member]
            img_x = x_pos + (card_width - chibi_img.get_width()) // 2
            img_y = y_pos + 20
            screen.blit(chibi_img, (img_x, img_y))
            
            name_s = member_name_surfs[member]
            screen.blit(name_s, (x_pos + (card_width - name_s.get_width()) // 2, y_pos + 160))
            
            if i == selected_index:
                screen.blit(SELECTED_LABEL, (x_pos + (card_width - SELECTED_LABEL.get_width()) // 2, y_pos + 195))

    elif game_state == "PLAYING":
        active_member = members[selected_index]
        screen.blit(character_images[active_member], (player_x, player_y))
        
        for item in falling_items:
            if item["type"] == "bomb":
                screen.blit(bomb_img, (item["x"], item["y"]))
            else:
                screen.blit(toast_img, (item["x"], item["y"]))
            
        if score_surf:
            screen.blit(score_surf, (30, 30))
        
        if multiplier > 1:
            screen.blit(MULT_3X_SURF, (30, 75))
            
        for l in range(lives):
            screen.blit(heart_img, (SCREEN_WIDTH - 50 - (l * 45), 30))

    elif game_state == "GAMEOVER":
        screen.blit(GAMEOVER_SURF, (SCREEN_WIDTH // 2 - GAMEOVER_SURF.get_width() // 2, 250))
        if final_score_surf:
            screen.blit(final_score_surf, (SCREEN_WIDTH // 2 - final_score_surf.get_width() // 2, 340))
        screen.blit(RESTART_SURF, (SCREEN_WIDTH // 2 - RESTART_SURF.get_width() // 2, 420))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
