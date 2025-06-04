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
GRID_WIDTH     = GRID_SIZE * CELL_SIZE       # 135*4 px
GRID_HEIGHT    = GRID_SIZE * CELL_SIZE       # 480 px

CONTROL_WIDTH  = 250                         # width of left‐hand control panel
INFO_HEIGHT    = 200                         # height of bottom info panel

WINDOW_WIDTH   = CONTROL_WIDTH + GRID_WIDTH  # 250 + 480 = 680 px
WINDOW_HEIGHT  = GRID_HEIGHT + INFO_HEIGHT   # 480 + 200 = 680 px

# ───────────────────────────────────────────────────────────────────────────────
# 3) COLORS
# ───────────────────────────────────────────────────────────────────────────────
BG_COLOR              = (30,  30,  40)   # overall background (dark gray)

# Grid cells
CELL_DEFAULT_COLOR    = (50,  75, 120)  # unvisited: dark blue
CELL_VISITED_COLOR    = (80, 120, 180)  # visited: lighter blue
CELL_SAFE_COLOR       = (50,  90,  50)  # known‐safe: dark green

# Grid lines
GRID_LINE_COLOR       = (20,  20,  20)  # near‐black

# Pit / Wumpus / Gold
PIT_OUTER_COLOR       = (0,    0,    0)  # black outline
PIT_INNER_COLOR       = (255, 255, 255)  # white fill
WUMPUS_COLOR_ALIVE    = (200,   0,   0)  # red
WUMPUS_COLOR_DEAD     = (100, 100, 100)  # gray
GOLD_OUTER_COLOR      = (255, 255,   0)  # yellow
GOLD_INNER_COLOR      = (255, 165,   0)  # orange

# Agent
AGENT_BODY_COLOR      = (  0,   0, 200)  # blue
AGENT_ARROW_COLOR     = (255, 255, 255)  # white

# Control panel (left)
CTRL_BG_COLOR         = (20,   20,  60)  # dark navy
BUTTON_BG_COLOR       = (50,  100, 180)  # medium blue
BUTTON_HOVER_COLOR    = (80,  130, 210)  # lighter blue on hover
BUTTON_TEXT_COLOR     = (255, 255, 255)  # white

# Info panel (bottom)
INFO_BG_COLOR         = (20,   20,  50)  # near‐black
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
# 5) LOAD SOUNDS (no turn.wav)
# ───────────────────────────────────────────────────────────────────────────────
SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds")

def load_sound(filename):
    path = os.path.join(SOUND_PATH, filename)
    if not os.path.isfile(path):
        print(f"Warning: Sound file not found: {path}")
        return None
    return pygame.mixer.Sound(path)

# We no longer load turn.wav
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

        self.clock = pygame.time.Clock()

        # ――― Game state ―――
        self.world      = WumpusWorld()
        self.agent      = LogicBasedAgent(self.world)
        self.game_over  = False
        self.auto_play  = False
        self.move_delay = 600   # milliseconds between auto‐steps
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
        """Draw the left‐hand Control Panel with functional buttons."""
        # Panel background
        pygame.draw.rect(self.screen, CTRL_BG_COLOR,
                         (0, 0, CONTROL_WIDTH, WINDOW_HEIGHT))

        # Header text
        hdr = header_font.render("Control Panel", True, BUTTON_TEXT_COLOR)
        self.screen.blit(hdr, (20, 20))

        # Determine Pause/Resume label from auto_play
        pause_label = "Pause" if self.auto_play else "Resume"

        # Determine Sound toggle label based on current state
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

        # Draw each button
        self.button_rects.clear()
        for (text, y) in labels:
            rect = pygame.Rect(x0, y, btn_w, btn_h)
            # Hover effect
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, BUTTON_HOVER_COLOR, rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, BUTTON_BG_COLOR, rect, border_radius=5)

            # Center‐aligned text
            txt_surf = button_font.render(text, True, BUTTON_TEXT_COLOR)
            self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))

            # Store rectangle keyed by label
            self.button_rects[text] = rect

    def draw_grid(self):
        """Draw the right‐hand 4×4 Wumpus grid (shifted right by CONTROL_WIDTH)."""
        offset_x = CONTROL_WIDTH
        offset_y = 0

        # Grid background
        pygame.draw.rect(self.screen, BG_COLOR,
                         (offset_x, offset_y, GRID_WIDTH, GRID_HEIGHT))

        # Draw each cell background (unvisited/visited/safe)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell_x = offset_x + c * CELL_SIZE
                cell_y = offset_y + r * CELL_SIZE

                if (r, c) in self.agent.visited:
                    color = CELL_VISITED_COLOR
                elif (r, c) in self.agent.safe_cells:
                    color = CELL_SAFE_COLOR
                else:
                    color = CELL_DEFAULT_COLOR

                pygame.draw.rect(self.screen, color,
                                 (cell_x + 1, cell_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))

        # Draw grid lines
        for i in range(GRID_SIZE + 1):
            vx = offset_x + i * CELL_SIZE
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (vx, offset_y),
                             (vx, offset_y + GRID_HEIGHT), 2)
            hy = offset_y + i * CELL_SIZE
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (offset_x, hy),
                             (offset_x + GRID_WIDTH, hy), 2)

    def draw_cell_contents(self, row, col):
        """
        Draw Pit, Wumpus, and Gold in each cell immediately
        (no waiting for visited or game over).
        """
        offset_x = CONTROL_WIDTH
        offset_y = 0
        cell = self.world.world[row][col]

        x = offset_x + col * CELL_SIZE
        y = offset_y + row * CELL_SIZE
        center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)

        # ── Pit
        if cell["pit"]:
            pygame.draw.circle(self.screen, PIT_OUTER_COLOR, center, 30)
            pygame.draw.circle(self.screen, PIT_INNER_COLOR, center, 25)
            txt = small_font.render("PIT", True, (0, 0, 0))
            self.screen.blit(txt, txt.get_rect(center=center))

        # ── Wumpus
        if cell["wumpus"]:
            w_color = WUMPUS_COLOR_ALIVE if self.world.wumpus_alive else WUMPUS_COLOR_DEAD
            pygame.draw.circle(self.screen, w_color, (center[0], center[1] + 10), 25)
            pygame.draw.circle(self.screen, w_color, (center[0], center[1] - 15), 15)
            pygame.draw.circle(self.screen, (0, 0, 0), (center[0] - 8, center[1] - 18), 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (center[0] + 8, center[1] - 18), 3)
            if not self.world.wumpus_alive:
                # Draw an X if dead
                pygame.draw.line(self.screen, (0, 0, 0),
                                 (x + 20, y + 20),
                                 (x + CELL_SIZE - 20, y + CELL_SIZE - 20), 3)
                pygame.draw.line(self.screen, (0, 0, 0),
                                 (x + CELL_SIZE - 20, y + 20),
                                 (x + 20, y + CELL_SIZE - 20), 3)

        # ── Gold
        if cell["gold"]:
            pygame.draw.circle(self.screen, GOLD_OUTER_COLOR, center, 20)
            pygame.draw.circle(self.screen, GOLD_INNER_COLOR, center, 15)
            txt = small_font.render("GOLD", True, (0, 0, 0))
            self.screen.blit(txt, txt.get_rect(center=center))

    def draw_agent(self):
        """
        Draw the agent as a blue circle + white arrow (shifted into grid area).
        If carrying gold, draw a small gold dot above its head.
        """
        offset_x = CONTROL_WIDTH
        offset_y = 0
        (r, c) = self.world.agent_pos

        center_x = offset_x + c * CELL_SIZE + CELL_SIZE // 2
        center_y = offset_y + r * CELL_SIZE + CELL_SIZE // 2

        # Draw the body
        pygame.draw.circle(self.screen, AGENT_BODY_COLOR, (center_x, center_y), 15)

        # Draw the direction arrow
        if self.world.agent_dir == "up":
            pygame.draw.polygon(self.screen, AGENT_ARROW_COLOR,
                                [(center_x, center_y - 10),
                                 (center_x - 5, center_y),
                                 (center_x + 5, center_y)])
        elif self.world.agent_dir == "down":
            pygame.draw.polygon(self.screen, AGENT_ARROW_COLOR,
                                [(center_x, center_y + 10),
                                 (center_x - 5, center_y),
                                 (center_x + 5, center_y)])
        elif self.world.agent_dir == "left":
            pygame.draw.polygon(self.screen, AGENT_ARROW_COLOR,
                                [(center_x - 10, center_y),
                                 (center_x, center_y - 5),
                                 (center_x, center_y + 5)])
        elif self.world.agent_dir == "right":
            pygame.draw.polygon(self.screen, AGENT_ARROW_COLOR,
                                [(center_x + 10, center_y),
                                 (center_x, center_y - 5),
                                 (center_x, center_y + 5)])

        # Tiny gold above head if carrying
        if self.world.has_gold:
            pygame.draw.circle(self.screen, GOLD_OUTER_COLOR,
                               (center_x, center_y - 25), 8)

    def draw_info_panel(self):
        """
        Draw the bottom Info panel beneath the grid (x=200..680, y=480..680),
        showing Score, Steps, Gold, Arrow, Wumpus, Percepts, and Agent Reasoning.
        """
        panel_x = CONTROL_WIDTH
        panel_y = GRID_HEIGHT
        panel_w = GRID_WIDTH
        panel_h = INFO_HEIGHT

        # Background
        pygame.draw.rect(self.screen, INFO_BG_COLOR,
                         (panel_x, panel_y, panel_w, panel_h))

        # Separator line
        pygame.draw.line(self.screen, (255, 255, 255),
                         (panel_x, panel_y),
                         (panel_x + panel_w, panel_y), 2)

        text_y = panel_y + 10

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
        reasoning = "Agent Reasoning: "
        try:
            reasoning += self.agent.current_reasoning
        except AttributeError:
            reasoning += "—"
        surf3 = info_font.render(reasoning, True, INFO_TEXT_COLOR)
        self.screen.blit(surf3, (panel_x + 10, text_y))
        text_y += 30

        # 4) Mode (AUTO vs MANUAL)
        mode_text = f"Mode: {'AUTO' if self.auto_play else 'MANUAL'}"
        mode_color = (0, 255, 0) if self.auto_play else (255, 0, 0)
        surf4 = header_font.render(mode_text, True, mode_color)
        self.screen.blit(surf4, (panel_x + 10, text_y))

    def draw_game_over_popup(self):
        """
        Draw a semi‐transparent overlay over the grid area (x=200..680, y=0..480)
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

        pygame.draw.rect(self.screen, (240, 240, 240), popup_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), popup_rect, 3, border_radius=8)

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
        except for turning (we have removed that sound). Each sound plays only
        if self.sound_on == True.
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
                # We are winning right now—play win sound
                if self.sound_on and sound_win:
                    sound_win.play()
                return "win"

        # After performing the action, check if Wumpus just died to play “scream” ONCE:
        if not self.world.wumpus_alive and not self.scream_played:
            if self.sound_on and sound_scream:
                sound_scream.play()
            self.scream_played = True

        # Check if that action caused a losing condition:
        result = self.world.is_game_over()
        if result == "lose":
            # Play “game over” sound
            if self.sound_on and sound_game_over:
                sound_game_over.play()
            return result

        return "continue"

    def reset_game(self):
        """
        Reset world/agent to start a brand‐new game (same as pressing R).
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

                    # Logic‐agent single step (ENTER) in Manual mode
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
