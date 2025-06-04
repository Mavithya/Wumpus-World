import pygame
import sys
import os

from wumpus_world import WumpusWorld
from logic_agent import LogicBasedAgent

# ───────────────────────────────────────────────────────────────────────────────
# 1) INITIALIZE PYGAME (including mixer & font subsystems)
# ───────────────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init()   # Initialize the sound system

# ───────────────────────────────────────────────────────────────────────────────
# 2) WINDOW LAYOUT CONSTANTS
# ───────────────────────────────────────────────────────────────────────────────
GRID_SIZE      = 4
CELL_SIZE      = 135
GRID_WIDTH     = GRID_SIZE * CELL_SIZE       # 4 × 135 = 540 px
GRID_HEIGHT    = GRID_SIZE * CELL_SIZE  + 10     # 4 × 135 = 540 px

CONTROL_WIDTH  = 250                         # width of left-hand control panel
INFO_HEIGHT    = 180                         # height of bottom info panel

PAD            = 10                          # padding around the grid

WINDOW_WIDTH   = CONTROL_WIDTH + PAD + GRID_WIDTH + PAD   # 250 + 10 + 540 + 10 = 810
WINDOW_HEIGHT  = PAD + GRID_HEIGHT + PAD + INFO_HEIGHT    # 10 + 540 + 10 + 200 = 760

# Gap between cells and rounded-corner settings
CELL_GAP       = 10    # total gap between adjacent cells
CORNER_RADIUS  = 10    # corner radius for rounded rectangles

# ───────────────────────────────────────────────────────────────────────────────
# 3) COLORS
# ───────────────────────────────────────────────────────────────────────────────
BG_COLOR              = (30,  30,  40)   # overall background (dark gray)

# Grid cells
CELL_DEFAULT_COLOR    = (50,  75, 120)  # unvisited: dark blue
CELL_VISITED_COLOR    = (80, 120, 180)  # visited: lighter blue
CELL_SAFE_COLOR       = (50,  90,  50)  # known-safe: dark green

# Cell shadow color (semi-transparent black)
CELL_SHADOW_COLOR     = (0, 0, 0, 200)

# Pit / Wumpus / Gold (no longer used for drawing circles, kept for reference)
PIT_OUTER_COLOR       = (0,    0,    0)
PIT_INNER_COLOR       = (255, 255, 255)
WUMPUS_COLOR_ALIVE    = (200,   0,   0)
WUMPUS_COLOR_DEAD     = (100, 100, 100)
GOLD_OUTER_COLOR      = (255, 255,   0)
GOLD_INNER_COLOR      = (255, 165,   0)

# Agent (no longer used for drawing circles, kept for reference)
AGENT_BODY_COLOR      = (0, 0, 200)
AGENT_ARROW_COLOR     = (255, 255, 255)

# Control panel (left)
CTRL_BG_COLOR         = (20,   20,  60)  # dark navy
BUTTON_BG_COLOR       = (50,  100, 180)  # medium blue
BUTTON_HOVER_COLOR    = (80,  130, 210)  # lighter blue on hover
BUTTON_TEXT_COLOR     = (255, 255, 255)  # white

# Info panel (bottom)
INFO_BG_COLOR         = (20,   20,  50)  # near-black
INFO_TEXT_COLOR       = (255, 255, 255)  # white

# ───────────────────────────────────────────────────────────────────────────────
# 4) FONTS
# ───────────────────────────────────────────────────────────────────────────────
INFO_FONT_SIZE    = 22
BUTTON_FONT_SIZE  = 23
HEADER_FONT_SIZE  = 30
SMALL_FONT_SIZE   = 20

info_font    = pygame.font.SysFont(None, INFO_FONT_SIZE)
button_font  = pygame.font.SysFont(None, BUTTON_FONT_SIZE)
header_font  = pygame.font.SysFont(None, HEADER_FONT_SIZE)
small_font   = pygame.font.SysFont(None, SMALL_FONT_SIZE)

# ───────────────────────────────────────────────────────────────────────────────
# 5) LOAD SOUNDS (turn.wav removed)
# ───────────────────────────────────────────────────────────────────────────────
SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds")

def load_sound(filename):
    path = os.path.join(SOUND_PATH, filename)
    if not os.path.isfile(path):
        print(f"Warning: Sound file not found: {path}")
        return None
    return pygame.mixer.Sound(path)

sound_move      = load_sound("move.wav")
sound_shoot     = load_sound("shoot.wav")
sound_grab      = load_sound("grab.wav")
sound_scream    = load_sound("scream.wav")
sound_game_over = load_sound("game_over.wav")
sound_win       = load_sound("win.wav")

# ───────────────────────────────────────────────────────────────────────────────
# 6) MAIN GAME CLASS
# ───────────────────────────────────────────────────────────────────────────────
class WumpusGameVisualization:
    def __init__(self):
        # ――― Set up the Pygame window ―――
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Wumpus World - Logic-Based Agent")

        # ――― Now that a display exists, load & convert images ―――
        ASSET_PATH = os.path.join(os.path.dirname(__file__), "assets")
        ICON_SIZE  =  80

        self.img_pit    = pygame.image.load(os.path.join(ASSET_PATH, "pit.png")).convert_alpha()
        self.img_wumpus = pygame.image.load(os.path.join(ASSET_PATH, "wumpus.png")).convert_alpha()
        self.img_agent  = pygame.image.load(os.path.join(ASSET_PATH, "agent.png")).convert_alpha()
        self.img_gold   = pygame.image.load(os.path.join(ASSET_PATH, "gold.png")).convert_alpha()

        self.img_pit    = pygame.transform.smoothscale(self.img_pit,    (ICON_SIZE, ICON_SIZE))
        self.img_wumpus = pygame.transform.smoothscale(self.img_wumpus, (ICON_SIZE, ICON_SIZE))
        self.img_agent  = pygame.transform.smoothscale(self.img_agent,  (ICON_SIZE, ICON_SIZE))
        self.img_gold   = pygame.transform.smoothscale(self.img_gold,   (ICON_SIZE, ICON_SIZE))

        # ――― Initialize other game state ―――
        self.clock = pygame.time.Clock()
        self.world      = WumpusWorld()
        self.agent      = LogicBasedAgent(self.world)
        self.game_over  = False
        self.auto_play  = False
        self.move_delay = 600   # milliseconds between auto-steps
        self.last_move_time = 0

        # Track whether sound is enabled
        self.sound_on = True

        # Store button rectangles for click detection
        self.button_rects = {}

        # Track if we’ve already played the scream sound (only once when Wumpus dies)
        self.scream_played = False

    # ────────────────────────────────────────────────────────────────────────────
    # DRAWING METHODS
    # ────────────────────────────────────────────────────────────────────────────
    def draw_control_panel(self):
        """Draw the left-hand Control Panel with functional buttons."""
        # Panel background
        pygame.draw.rect(self.screen, CTRL_BG_COLOR,
                         (0, 0, CONTROL_WIDTH, WINDOW_HEIGHT))

        # Header text
        hdr = header_font.render("Control Panel", True, BUTTON_TEXT_COLOR)
        self.screen.blit(hdr, (20, 20))

        # Determine Pause/Resume label
        pause_label = "Pause" if self.auto_play else "Resume"

        # Determine Sound toggle label
        sound_label = "Sound: On" if self.sound_on else "Sound: Off"

        # Button labels & vertical positions
        labels = [
            (pause_label,            75),
            ("Reset",               130),
            ("New Game",            185),
            (f"Auto: {'ON' if self.auto_play else 'OFF'}", 240),
            (sound_label,           295),
            ("Quit",                350)
        ]

        btn_w = CONTROL_WIDTH - 50
        btn_h = 45
        x0    = 25
        mouse_pos = pygame.mouse.get_pos()

        # Draw each button with hover effect
        self.button_rects.clear()
        for (text, y) in labels:
            rect = pygame.Rect(x0, y, btn_w, btn_h)
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, BUTTON_HOVER_COLOR, rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, BUTTON_BG_COLOR, rect, border_radius=5)

            txt_surf = button_font.render(text, True, BUTTON_TEXT_COLOR)
            self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
            self.button_rects[text] = rect

    def draw_grid(self):
        """
        Draw the right-hand 4×4 Wumpus grid (shifted right by CONTROL_WIDTH).
        Each cell is drawn with a small gap, rounded corners, and a drop shadow.
        """
        offset_x = CONTROL_WIDTH
        offset_y = 10

        # Fill the grid background (behind all cells)
        pygame.draw.rect(self.screen, BG_COLOR, (offset_x, offset_y, GRID_WIDTH, GRID_HEIGHT))

        # For each cell, draw a drop shadow then a rounded rectangle
        inner_size = CELL_SIZE - CELL_GAP
        shadow_offset = 4  # offset for drop shadow

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell_x = offset_x + c * CELL_SIZE
                cell_y = offset_y + r * CELL_SIZE

                # Compute inner rectangle coordinates (centered within each CELL_SIZE block)
                inner_x = cell_x + (CELL_GAP // 2)
                inner_y = cell_y + (CELL_GAP // 2)

                # Determine cell fill color
                if (r, c) in self.agent.visited:
                    fill_color = CELL_VISITED_COLOR
                elif (r, c) in self.agent.safe_cells:
                    fill_color = CELL_SAFE_COLOR
                else:
                    fill_color = CELL_DEFAULT_COLOR

                # 1) Draw drop shadow: a rounded rect on a temporary surface with alpha
                shadow_surf = pygame.Surface((inner_size, inner_size), pygame.SRCALPHA)
                pygame.draw.rect(
                    shadow_surf,
                    CELL_SHADOW_COLOR,
                    (0, 0, inner_size, inner_size),
                    border_radius=CORNER_RADIUS
                )
                # Blit the shadow slightly offset
                self.screen.blit(shadow_surf, (inner_x + shadow_offset, inner_y + shadow_offset))

                # 2) Draw the actual cell rect with rounded corners
                pygame.draw.rect(
                    self.screen,
                    fill_color,
                    (inner_x, inner_y, inner_size, inner_size),
                    border_radius=CORNER_RADIUS
                )

    def draw_cell_contents(self, row, col):
        """
        Draw Pit, Wumpus, and Gold in each cell immediately.
        The icons are centered in the full CELL_SIZE block, not the inner only.
        """
        offset_x = CONTROL_WIDTH
        offset_y = 0
        cell = self.world.world[row][col]

        x = offset_x + col * CELL_SIZE
        y = offset_y + row * CELL_SIZE
        center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)

        # ── Pit (use pit.png)
        if cell["pit"]:
            icon_rect = self.img_pit.get_rect(center=center)
            self.screen.blit(self.img_pit, icon_rect)

        # ── Wumpus (use wumpus.png; gray-out if dead)
        if cell["wumpus"]:
            size = self.img_wumpus.get_width()  # should be ICON_SIZE
            if not self.world.wumpus_alive:
                gray_wumpus = pygame.Surface((size, size), pygame.SRCALPHA)
                gray_wumpus.blit(self.img_wumpus, (0, 0))
                gray_wumpus.fill(
                    (100, 100, 100, 180), special_flags=pygame.BLEND_RGBA_MULT
                )
                icon_rect = gray_wumpus.get_rect(center=center)
                self.screen.blit(gray_wumpus, icon_rect)
            else:
                icon_rect = self.img_wumpus.get_rect(center=center)
                self.screen.blit(self.img_wumpus, icon_rect)

        # ── Gold (use gold.png)
        if cell["gold"]:
            icon_rect = self.img_gold.get_rect(center=center)
            self.screen.blit(self.img_gold, icon_rect)

    def draw_agent(self):
        """
        Draw the agent’s head sprite (agent.png) at the center of its cell,
        then draw a small arrow on top to indicate direction.
        """
        offset_x = CONTROL_WIDTH
        offset_y = 0
        (r, c) = self.world.agent_pos

        center_x = offset_x + c * CELL_SIZE + CELL_SIZE // 2
        center_y = offset_y + r * CELL_SIZE + CELL_SIZE // 2

        # ── 1) Draw the head sprite, rotated for direction:
        rot_agent = self.img_agent
        if self.world.agent_dir == "up":
            rot_agent = pygame.transform.rotate(self.img_agent, 0)
        elif self.world.agent_dir == "right":
            rot_agent = pygame.transform.rotate(self.img_agent, -90)
        elif self.world.agent_dir == "down":
            rot_agent = pygame.transform.rotate(self.img_agent, 180)
        elif self.world.agent_dir == "left":
            rot_agent = pygame.transform.rotate(self.img_agent, 90)

        agent_rect = rot_agent.get_rect(center=(center_x, center_y))
        self.screen.blit(rot_agent, agent_rect)

        # ── 2) Draw a small white arrow on top to show facing direction:
        arrow_size = 12
        half = arrow_size // 2

        if self.world.agent_dir == "up":
            pts = [
                (center_x, center_y - half - 10),
                (center_x - half, center_y - 10 + half),
                (center_x + half, center_y - 10 + half),
            ]
        elif self.world.agent_dir == "down":
            pts = [
                (center_x, center_y + half + 10),
                (center_x - half, center_y + 10 - half),
                (center_x + half, center_y + 10 - half),
            ]
        elif self.world.agent_dir == "left":
            pts = [
                (center_x - half - 10, center_y),
                (center_x - 10 + half, center_y - half),
                (center_x - 10 + half, center_y + half),
            ]
        else:  # "right"
            pts = [
                (center_x + half + 10, center_y),
                (center_x + 10 - half, center_y - half),
                (center_x + 10 - half, center_y + half),
            ]

        pygame.draw.polygon(self.screen, (255, 255, 255), pts)

        # ── Tiny gold icon at corner if carrying gold:
        if self.world.has_gold:
            tiny_gold = pygame.transform.smoothscale(self.img_gold, (20, 20))
            tg_rect = tiny_gold.get_rect(bottomright=(center_x + 20, center_y - 20))
            self.screen.blit(tiny_gold, tg_rect)

    def draw_info_panel(self):
        """
        Draw the bottom Info panel beneath the grid (x=250..790, y=540..740),
        showing Score, Steps, Gold, Arrow, Wumpus, Percepts, and Agent Reasoning.
        """
        panel_x = CONTROL_WIDTH
        panel_y = GRID_HEIGHT
        panel_w = GRID_WIDTH
        panel_h = INFO_HEIGHT

        # Background
        pygame.draw.rect(self.screen, INFO_BG_COLOR,
                         (panel_x, panel_y, panel_w + 15 , panel_h + 12))

        # Separator line
        pygame.draw.line(self.screen, (255, 255, 255),
                         (panel_x, panel_y + 10),
                         (panel_x + panel_w, panel_y + 10), 2)

        text_y = panel_y + 50

        # 1) Score | Steps | Gold | Arrow | Wumpus Alive
        line1 = (
            f"Score: {self.world.score}   |   "
            f"Steps: {len(self.agent.visited)}   |   "
            f"Gold: {'Yes' if self.world.has_gold else 'No'}   |   "
            f"Arrow: {'Yes' if self.world.has_arrow else 'No'}   |   "
            f"Wumpus Alive: {'Yes' if self.world.wumpus_alive else 'No'}"
        )
        surf1 = info_font.render(line1, True, INFO_TEXT_COLOR)
        self.screen.blit(surf1, (panel_x + 10, text_y))
        text_y += 30

        # 2) Percepts
        percepts = [k.upper() for k, v in self.world.percepts.items() if v]
        ptext = "Percepts: " + (", ".join(percepts) if percepts else "None")
        surf2 = info_font.render(ptext, True, INFO_TEXT_COLOR)
        self.screen.blit(surf2, (panel_x + 10, text_y))
        text_y += 30

        # 3) Agent Reasoning
        # reasoning = "Agent Reasoning: "
        # try:
        #     reasoning += self.agent.current_reasoning
        # except AttributeError:
        #     reasoning += "—"
        # surf3 = info_font.render(reasoning, True, INFO_TEXT_COLOR)
        # self.screen.blit(surf3, (panel_x + 10, text_y))
        # text_y += 30

        # 4) Mode (AUTO vs MANUAL)
        mode_text = f"Mode: {'AUTO' if self.auto_play else 'MANUAL'}"
        mode_color = (0, 255, 0) if self.auto_play else (255, 0, 0)
        surf4 = header_font.render(mode_text, True, mode_color)
        self.screen.blit(surf4, (panel_x + 10, text_y))

    def draw_game_over_popup(self):
        """
        Draw a semi-transparent overlay over the grid area (x=250..790, y=0..540)
        and a centered popup with "New Game" and "Quit" buttons.
        """
        offset_x = CONTROL_WIDTH
        offset_y = 0

        # Overlay
        overlay = pygame.Surface((GRID_WIDTH, GRID_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (offset_x, offset_y))

        # Popup rectangle
        popup_w = 400
        popup_h = 250
        popup_x = offset_x + (GRID_WIDTH - popup_w)//2
        popup_y = offset_y + (GRID_HEIGHT - popup_h)//2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)

        pygame.draw.rect(self.screen, (240, 240, 240), popup_rect, border_radius=14)
        pygame.draw.rect(self.screen, (0, 0, 0), popup_rect, 3, border_radius=14)

        # Title "GAME OVER"
        status = self.world.is_game_over()
        go_color = (255, 0, 0) if status == "lose" else (0, 200, 0)
        title = header_font.render("GAME OVER", True, go_color)
        self.screen.blit(
            title,
            title.get_rect(center=(offset_x + GRID_WIDTH//2, popup_y + 50))
        )

        # Subtitle "You died/won with score: X"
        if status == "lose":
            sub = f"You died with score: {self.world.score}"
        else:
            sub = f"You won with score: {self.world.score}"
        sub_surf = small_font.render(sub, True, (0, 0, 0))
        self.screen.blit(
            sub_surf,
            sub_surf.get_rect(center=(offset_x + GRID_WIDTH//2, popup_y + 90))
        )

        # Buttons "New Game" and "Quit"
        btn_w, btn_h = 140, 40
        gap = 30
        total_w = btn_w * 2 + gap
        start_x = offset_x + (GRID_WIDTH - total_w)//2
        y = popup_y + 140

        # New Game
        self.btn_new_rect = pygame.Rect(start_x, y, btn_w, btn_h)
        pygame.draw.rect(self.screen, BUTTON_BG_COLOR, self.btn_new_rect, border_radius=5)
        txt1 = button_font.render("New Game", True, BUTTON_TEXT_COLOR)
        self.screen.blit(txt1, txt1.get_rect(center=self.btn_new_rect.center))

        # Quit
        self.btn_quit_rect = pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h)
        pygame.draw.rect(self.screen, BUTTON_BG_COLOR, self.btn_quit_rect, border_radius=5)
        txt2 = button_font.render("Quit", True, BUTTON_TEXT_COLOR)
        self.screen.blit(txt2, txt2.get_rect(center=self.btn_quit_rect.center))

    # ────────────────────────────────────────────────────────────────────────────
    # GAME ACTION METHODS (UNCHANGED, except TURN SOUND REMOVED)
    # ────────────────────────────────────────────────────────────────────────────
    def execute_action(self, action):
        """
        Perform one of: "move", "turn_left", "turn_right", "shoot", "grab", "climb".
        Returns "win", "lose", or "continue".

        We also play the appropriate sound effect just after each action,
        except for turning (no turn.wav). Each sound plays only if self.sound_on == True.
        """
        # ── MOVE FORWARD ──
        if action == "move":
            moved = self.world.move_forward()
            if self.sound_on and sound_move:
                sound_move.play()

        # ── TURN LEFT ── (no sound)
        elif action == "turn_left":
            self.world.turn_left()

        # ── TURN RIGHT ── (no sound)
        elif action == "turn_right":
            self.world.turn_right()

        # ── SHOOT ARROW ──
        elif action == "shoot":
            shot = self.world.shoot_arrow()
            if self.sound_on and sound_shoot:
                sound_shoot.play()

        # ── GRAB GOLD ──
        elif action == "grab":
            grabbed = self.world.grab_gold()
            if grabbed and self.sound_on and sound_grab:
                sound_grab.play()

        # ── CLIMB ──
        elif action == "climb":
            if self.world.agent_pos == (0, 0) and self.world.has_gold:
                if self.sound_on and sound_win:
                    sound_win.play()
                return "win"

        # After the action, check if Wumpus just died (play scream once):
        if not self.world.wumpus_alive and not self.scream_played:
            if self.sound_on and sound_scream:
                sound_scream.play()
            self.scream_played = True

        # Check if that action caused a losing condition:
        result = self.world.is_game_over()
        if result == "lose":
            if self.sound_on and sound_game_over:
                sound_game_over.play()
            return result

        return "continue"

    def reset_game(self):
        """
        Reset world/agent to start a brand-new game (same as pressing R).
        Also reset the “scream_played” flag so we can hear the scream next time.
        """
        self.world      = WumpusWorld()
        self.agent      = LogicBasedAgent(self.world)
        self.game_over  = False
        self.auto_play  = False
        self.last_move_time = 0
        self.scream_played = False

    # ────────────────────────────────────────────────────────────────────────────
    # MAIN LOOP
    # ────────────────────────────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                # ― QUIT ―
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # ― KEYDOWN & MANUAL CONTROLS ―
                if event.type == pygame.KEYDOWN and not self.game_over:
                    # Quit (Q)
                    if event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

                    # Reset (R)
                    elif event.key == pygame.K_r:
                        self.reset_game()

                    # Toggle Auto/Manual (SPACE)
                    elif event.key == pygame.K_SPACE:
                        self.auto_play = not self.auto_play

                    # Logic-agent single step (ENTER) in Manual mode
                    elif event.key == pygame.K_RETURN:
                        if not self.auto_play and not self.game_over:
                            action = self.agent.choose_action()
                            result = self.execute_action(action)
                            if result != "continue":
                                self.game_over = True

                    # Manual move/turn with arrow keys or WASD
                    elif not self.auto_play:
                        # ↑ or W
                        if event.key in (pygame.K_UP, pygame.K_w):
                            desired = "up"
                            if self.world.agent_dir == desired:
                                result = self.execute_action("move")
                            else:
                                result = self.execute_action(self.agent.get_turn_action(desired))
                            if result != "continue":
                                self.game_over = True

                        # ↓ or S
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            desired = "down"
                            if self.world.agent_dir == desired:
                                result = self.execute_action("move")
                            else:
                                result = self.execute_action(self.agent.get_turn_action(desired))
                            if result != "continue":
                                self.game_over = True

                        # ← or A
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            desired = "left"
                            if self.world.agent_dir == desired:
                                result = self.execute_action("move")
                            else:
                                result = self.execute_action(self.agent.get_turn_action(desired))
                            if result != "continue":
                                self.game_over = True

                        # → or D
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            desired = "right"
                            if self.world.agent_dir == desired:
                                result = self.execute_action("move")
                            else:
                                result = self.execute_action(self.agent.get_turn_action(desired))
                            if result != "continue":
                                self.game_over = True

                        # Shoot (F)
                        elif event.key == pygame.K_f:
                            result = self.execute_action("shoot")
                            if result != "continue":
                                self.game_over = True

                        # Grab (G)
                        elif event.key == pygame.K_g:
                            result = self.execute_action("grab")
                            if result != "continue":
                                self.game_over = True

                        # Climb (C)
                        elif event.key == pygame.K_c:
                            result = self.execute_action("climb")
                            if result != "continue":
                                self.game_over = True

                # ― MOUSE CLICK FOR GAME OVER POPUP ―
                if event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                    mx, my = event.pos
                    # New Game
                    if hasattr(self, "btn_new_rect") and self.btn_new_rect.collidepoint(mx, my):
                        self.reset_game()
                    # Quit
                    elif hasattr(self, "btn_quit_rect") and self.btn_quit_rect.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()

                # ― MOUSE CLICK FOR CONTROL PANEL BUTTONS ―
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    mx, my = event.pos

                    # 1) Pause/Resume button (text is either "Pause" or "Resume")
                    pause_label = "Pause" if self.auto_play else "Resume"
                    if pause_label in self.button_rects and self.button_rects[pause_label].collidepoint(mx, my):
                        self.auto_play = not self.auto_play

                    # 2) Reset button
                    if "Reset" in self.button_rects and self.button_rects["Reset"].collidepoint(mx, my):
                        self.reset_game()

                    # 3) New Game button
                    if "New Game" in self.button_rects and self.button_rects["New Game"].collidepoint(mx, my):
                        self.reset_game()

                    # 4) Auto: ON/OFF button
                    auto_label = f"Auto: {'ON' if self.auto_play else 'OFF'}"
                    if auto_label in self.button_rects and self.button_rects[auto_label].collidepoint(mx, my):
                        self.auto_play = not self.auto_play

                    # 5) Sound On/Off button
                    sound_label = "Sound: On" if self.sound_on else "Sound: Off"
                    if sound_label in self.button_rects and self.button_rects[sound_label].collidepoint(mx, my):
                        self.sound_on = not self.sound_on

                    # 6) Quit button
                    if "Quit" in self.button_rects and self.button_rects["Quit"].collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()

            # ― AUTO PLAY ―
            if self.auto_play and not self.game_over and current_time - self.last_move_time > self.move_delay:
                action = self.agent.choose_action()
                result = self.execute_action(action)
                if result != "continue":
                    self.game_over = True
                self.last_move_time = current_time

            # ― DRAW EVERYTHING ―
            self.screen.fill(BG_COLOR)

            # 1) Left control panel
            self.draw_control_panel()

            # 2) Right grid + contents + agent
            self.draw_grid()
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    self.draw_cell_contents(r, c)
            self.draw_agent()

            # 3) Bottom info panel
            self.draw_info_panel()

            # 4) Game Over popup (over grid only)
            if self.game_over:
                self.draw_game_over_popup()

            pygame.display.flip()
            self.clock.tick(60)


# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = WumpusGameVisualization()
    game.run()
