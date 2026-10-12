import os
import sys
import json
import math
import random
import pygame

# Initialize Pygame and audio
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

# Ensure sound assets are generated
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, 'sounds')
try:
    import sound_generator
    sound_generator.generate_all_sounds(SOUND_DIR)
except Exception as e:
    print(f"Sound generation notice: {e}")

# Constants & Settings
WINDOW_WIDTH = 860
WINDOW_HEIGHT = 740
FPS = 60

GRID_COLS = 10
GRID_ROWS = 20
CELL_SIZE = 32

BOARD_WIDTH = GRID_COLS * CELL_SIZE   # 320 px
BOARD_HEIGHT = GRID_ROWS * CELL_SIZE  # 640 px

BOARD_X = (WINDOW_WIDTH - BOARD_WIDTH) // 2  # Centered
BOARD_Y = (WINDOW_HEIGHT - BOARD_HEIGHT) // 2

# Modern Neon & Cyberpunk Color Palette
COLOR_BG_DARK = (13, 17, 24)
COLOR_BG_PANEL = (22, 27, 34)
COLOR_PANEL_BORDER = (48, 54, 61)
COLOR_GRID_BG = (16, 20, 28)
COLOR_GRID_LINE = (28, 35, 48)
COLOR_TEXT_MAIN = (240, 246, 252)
COLOR_TEXT_MUTED = (139, 148, 158)
COLOR_ACCENT = (88, 166, 255)
COLOR_ACCENT_GLOW = (56, 139, 253, 100)

# Tetromino shapes and their distinct neon vibrant colors
# Shapes defined in standard 4x4 or 3x3 grids
TETROMINOES = {
    'I': {
        'shape': [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ],
        'color': (0, 240, 240),      # Cyan
        'light': (120, 255, 255),
        'dark': (0, 160, 160)
    },
    'J': {
        'shape': [
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        'color': (45, 105, 255),     # Deep Blue
        'light': (120, 160, 255),
        'dark': (20, 60, 180)
    },
    'L': {
        'shape': [
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 0]
        ],
        'color': (255, 150, 0),      # Orange
        'light': (255, 195, 90),
        'dark': (180, 100, 0)
    },
    'O': {
        'shape': [
            [1, 1],
            [1, 1]
        ],
        'color': (255, 225, 30),     # Bright Yellow
        'light': (255, 245, 130),
        'dark': (180, 160, 10)
    },
    'S': {
        'shape': [
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0]
        ],
        'color': (40, 225, 90),      # Neon Green
        'light': (120, 255, 150),
        'dark': (20, 160, 50)
    },
    'T': {
        'shape': [
            [0, 1, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        'color': (180, 60, 255),     # Purple / Violet
        'light': (220, 140, 255),
        'dark': (120, 30, 180)
    },
    'Z': {
        'shape': [
            [1, 1, 0],
            [0, 1, 1],
            [0, 0, 0]
        ],
        'color': (255, 60, 80),      # Crimson / Red
        'light': (255, 130, 145),
        'dark': (180, 30, 45)
    }
}

# High Score Storage
HIGHSCORE_FILE = os.path.join(BASE_DIR, 'highscore.json')

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return json.load(f).get('highscore', 0)
        except Exception:
            return 0
    return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({'highscore': score}, f)
    except Exception:
        pass


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        sound_names = ['move', 'rotate', 'drop', 'clear', 'tetris', 'levelup', 'gameover']
        for name in sound_names:
            path = os.path.join(SOUND_DIR, f"{name}.wav")
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(0.35)
                    self.sounds[name] = snd
                except Exception:
                    pass

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 1.5
        self.gravity = 0.18
        self.life = 1.0  # 1.0 to 0.0
        self.decay = random.uniform(0.02, 0.04)
        self.size = random.uniform(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay
        self.size = max(0, self.size - 0.05)

    def draw(self, surface):
        if self.life > 0 and self.size > 0:
            alpha = int(self.life * 255)
            # Create a small surface with alpha
            p_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            col = (*self.color, alpha)
            pygame.draw.circle(p_surf, col, (int(self.size), int(self.size)), int(self.size))
            surface.blit(p_surf, (self.x - self.size, self.y - self.size))


class FloatingText:
    def __init__(self, text, x, y, color=(255, 255, 255), size=24):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.life = 1.0
        self.decay = 0.02
        self.vy = -1.2

    def update(self):
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surface, font_maker):
        if self.life > 0:
            font = font_maker(self.size, bold=True)
            text_surf = font.render(self.text, True, self.color)
            alpha = int(self.life * 255)
            text_surf.set_alpha(alpha)
            rect = text_surf.get_rect(center=(self.x, self.y))
            surface.blit(text_surf, rect)


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in TETROMINOES[kind]['shape']]
        self.color = TETROMINOES[kind]['color']
        self.light = TETROMINOES[kind]['light']
        self.dark = TETROMINOES[kind]['dark']
        self.x = GRID_COLS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate_cw(self):
        # Transpose and reverse rows
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def rotate_ccw(self):
        # Reverse rows and transpose
        self.shape = [list(row) for row in zip(*self.shape)][::-1]


class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TETRIS KLASSIK - Desktop O'yini")
        self.clock = pygame.time.Clock()

        # Load fonts
        self.font_cache = {}
        self.sound_mgr = SoundManager()

        self.highscore = load_highscore()
        self.reset_game()

    def get_font(self, size, bold=False):
        key = (size, bold)
        if key not in self.font_cache:
            try:
                # Try Segoe UI or Arial or fallback to default
                self.font_cache[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
            except Exception:
                self.font_cache[key] = pygame.font.Font(None, size)
        return self.font_cache[key]

    def reset_game(self):
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.bag = []
        self.next_pieces = [self.get_bag_piece() for _ in range(3)]
        self.current_piece = self.get_bag_piece()
        self.hold_piece = None
        self.can_hold = True

        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = -1

        self.game_over = False
        self.paused = False

        self.drop_time = 0
        self.lock_delay = 500  # ms
        self.lock_timer = 0
        self.is_locking = False

        # Input handling with DAS (Delayed Auto Shift)
        self.key_left_pressed = False
        self.key_right_pressed = False
        self.key_down_pressed = False
        self.das_timer = 0
        self.das_initial_delay = 170  # ms
        self.das_repeat_rate = 45     # ms
        self.das_direction = 0

        # VFX
        self.particles = []
        self.floating_texts = []
        self.screen_shake_time = 0
        self.screen_shake_magnitude = 0
        self.clearing_rows = []
        self.clear_anim_timer = 0

    def get_bag_piece(self):
        if not self.bag:
            self.bag = list(TETROMINOES.keys())
            random.shuffle(self.bag)
        return Piece(self.bag.pop())

    def get_drop_interval(self):
        # Speed scales up with level: level 1: 800ms, level 15: 80ms
        return max(70, int(850 * (0.84 ** (self.level - 1))))

    def is_valid_position(self, piece, offset_x=0, offset_y=0, shape=None):
        shape = shape or piece.shape
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if val:
                    new_x = piece.x + c + offset_x
                    new_y = piece.y + r + offset_y
                    if new_x < 0 or new_x >= GRID_COLS or new_y >= GRID_ROWS:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x] is not None:
                        return False
        return True

    def rotate_current_piece(self, clockwise=True):
        if not self.current_piece or self.game_over or self.paused:
            return

        old_shape = [row[:] for row in self.current_piece.shape]
        if clockwise:
            self.current_piece.rotate_cw()
        else:
            self.current_piece.rotate_ccw()

        # Wall kick tests (offsets to try: 0, -1, +1, -2, +2, then vertical up -1)
        wall_kicks = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
        rotated = False
        for ox, oy in wall_kicks:
            if self.is_valid_position(self.current_piece, offset_x=ox, offset_y=oy):
                self.current_piece.x += ox
                self.current_piece.y += oy
                rotated = True
                self.sound_mgr.play('rotate')
                break

        if not rotated:
            # Revert shape
            self.current_piece.shape = old_shape

    def hard_drop(self):
        if not self.current_piece or self.game_over or self.paused:
            return

        drop_dist = 0
        while self.is_valid_position(self.current_piece, offset_y=1):
            self.current_piece.y += 1
            drop_dist += 1

        self.score += drop_dist * 2
        self.sound_mgr.play('drop')
        self.trigger_screen_shake(4, 120)

        # Particle impact at landing bottom
        for r, row in enumerate(self.current_piece.shape):
            for c, val in enumerate(row):
                if val:
                    px = BOARD_X + (self.current_piece.x + c) * CELL_SIZE + CELL_SIZE // 2
                    py = BOARD_Y + (self.current_piece.y + r + 1) * CELL_SIZE
                    for _ in range(3):
                        self.particles.append(Particle(px, py, self.current_piece.color))

        self.lock_piece()

    def hold_current_piece(self):
        if not self.can_hold or self.game_over or self.paused:
            return

        self.sound_mgr.play('rotate')
        if self.hold_piece is None:
            self.hold_piece = Piece(self.current_piece.kind)
            self.current_piece = self.next_pieces.pop(0)
            self.next_pieces.append(self.get_bag_piece())
        else:
            # Swap
            temp = Piece(self.hold_piece.kind)
            self.hold_piece = Piece(self.current_piece.kind)
            self.current_piece = temp

        self.can_hold = False
        self.is_locking = False
        self.lock_timer = 0

    def get_ghost_y(self):
        if not self.current_piece:
            return 0
        ghost_y = self.current_piece.y
        while self.is_valid_position(self.current_piece, offset_y=(ghost_y - self.current_piece.y + 1)):
            ghost_y += 1
        return ghost_y

    def lock_piece(self):
        # Freeze piece onto grid
        for r, row in enumerate(self.current_piece.shape):
            for c, val in enumerate(row):
                if val:
                    gx = self.current_piece.x + c
                    gy = self.current_piece.y + r
                    if 0 <= gy < GRID_ROWS and 0 <= gx < GRID_COLS:
                        self.grid[gy][gx] = {
                            'color': self.current_piece.color,
                            'light': self.current_piece.light,
                            'dark': self.current_piece.dark
                        }

        self.check_line_clears()

        # Spawn next piece
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self.get_bag_piece())
        self.can_hold = True
        self.is_locking = False
        self.lock_timer = 0

        # Check Game Over
        if not self.is_valid_position(self.current_piece):
            self.game_over = True
            self.sound_mgr.play('gameover')
            if self.score > self.highscore:
                self.highscore = self.score
                save_highscore(self.highscore)

    def check_line_clears(self):
        cleared_indices = []
        for r in range(GRID_ROWS):
            if all(self.grid[r][c] is not None for c in range(GRID_COLS)):
                cleared_indices.append(r)

        if not cleared_indices:
            self.combo = -1
            return

        self.combo += 1
        num_lines = len(cleared_indices)
        self.lines += num_lines

        # Scoring points based on standard Guideline
        scores_table = {1: 100, 2: 300, 3: 500, 4: 800}
        base_points = scores_table.get(num_lines, 100 * num_lines) * self.level
        combo_bonus = max(0, self.combo * 50 * self.level)
        total_gained = base_points + combo_bonus
        self.score += total_gained

        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)

        # Check Level Progression (every 10 lines)
        new_level = (self.lines // 10) + 1
        if new_level > self.level:
            self.level = new_level
            self.sound_mgr.play('levelup')
            self.floating_texts.append(FloatingText(f"BOSQICH {self.level}!", BOARD_X + BOARD_WIDTH // 2, BOARD_Y + 180, (255, 230, 80), 28))
        else:
            if num_lines == 4:
                self.sound_mgr.play('tetris')
            else:
                self.sound_mgr.play('clear')

        # VFX Particles along cleared lines
        for r in cleared_indices:
            for c in range(GRID_COLS):
                cell = self.grid[r][c]
                col = cell['color'] if cell else (255, 255, 255)
                px = BOARD_X + c * CELL_SIZE + CELL_SIZE // 2
                py = BOARD_Y + r * CELL_SIZE + CELL_SIZE // 2
                for _ in range(6):
                    self.particles.append(Particle(px, py, col))

        # Floating labels
        names = {1: "YAGONA +", 2: "IKKILIK! +", 3: "UCHLIK! +", 4: "★ TETRIS! ★ +"}
        label = f"{names.get(num_lines, '')}{total_gained}"
        color = (255, 80, 100) if num_lines == 4 else (80, 240, 255)
        self.floating_texts.append(FloatingText(label, BOARD_X + BOARD_WIDTH // 2, BOARD_Y + cleared_indices[0] * CELL_SIZE, color, 24))

        if self.combo > 0:
            self.floating_texts.append(FloatingText(f"COMBO x{self.combo+1}!", BOARD_X + BOARD_WIDTH // 2, BOARD_Y + cleared_indices[0] * CELL_SIZE - 25, (255, 200, 50), 18))

        if num_lines == 4:
            self.trigger_screen_shake(7, 200)

        # Clear rows and shift down
        for r in cleared_indices:
            del self.grid[r]
            self.grid.insert(0, [None for _ in range(GRID_COLS)])

    def trigger_screen_shake(self, magnitude, duration_ms):
        self.screen_shake_magnitude = magnitude
        self.screen_shake_time = duration_ms

    def handle_das(self, dt):
        if self.das_direction != 0:
            self.das_timer += dt
            if self.das_timer >= self.das_initial_delay:
                # Repeat moves
                while self.das_timer >= self.das_initial_delay + self.das_repeat_rate:
                    self.das_timer -= self.das_repeat_rate
                    if self.is_valid_position(self.current_piece, offset_x=self.das_direction):
                        self.current_piece.x += self.das_direction
                        self.sound_mgr.play('move')
                        if self.is_locking:
                            self.lock_timer = 0  # Lock delay reset on move

    def update(self, dt):
        # Update floating texts & particles
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        for ft in self.floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.floating_texts.remove(ft)

        # Screen shake timer
        if self.screen_shake_time > 0:
            self.screen_shake_time = max(0, self.screen_shake_time - dt)

        if self.game_over or self.paused:
            return

        # DAS handling
        self.handle_das(dt)

        # Soft drop or normal gravity
        current_speed = self.get_drop_interval()
        if self.key_down_pressed:
            current_speed = max(35, current_speed // 9)

        self.drop_time += dt
        if self.drop_time >= current_speed:
            self.drop_time = 0
            if self.is_valid_position(self.current_piece, offset_y=1):
                self.current_piece.y += 1
                if self.key_down_pressed:
                    self.score += 1
                self.is_locking = False
                self.lock_timer = 0
            else:
                self.is_locking = True

        # Lock delay when touching ground
        if self.is_locking:
            self.lock_timer += dt
            if self.lock_timer >= self.lock_delay:
                self.lock_piece()

    def draw_beveled_block(self, surface, x, y, size, color_tuple, light_tuple, dark_tuple, alpha=255):
        if alpha < 255:
            block_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            col = (*color_tuple, alpha)
            l_col = (*light_tuple, alpha)
            d_col = (*dark_tuple, alpha)
            pygame.draw.rect(block_surf, col, (0, 0, size, size))
            # Bevel highlights
            pygame.draw.polygon(block_surf, l_col, [(0, 0), (size, 0), (size - 3, 3), (3, 3), (3, size - 3), (0, size)])
            pygame.draw.polygon(block_surf, d_col, [(size, size), (0, size), (3, size - 3), (size - 3, size - 3), (size - 3, 3), (size, 0)])
            # Inner glossy square
            inner_col = (*[min(255, c + 20) for c in color_tuple], alpha)
            pygame.draw.rect(block_surf, inner_col, (4, 4, size - 8, size - 8))
            surface.blit(block_surf, (x, y))
        else:
            pygame.draw.rect(surface, color_tuple, (x, y, size, size))
            # Bevel edges
            pygame.draw.polygon(surface, light_tuple, [(x, y), (x + size, y), (x + size - 3, y + 3), (x + 3, y + 3), (x + 3, y + size - 3), (x, y + size)])
            pygame.draw.polygon(surface, dark_tuple, [(x + size, y + size), (x, y + size), (x + 3, y + size - 3), (x + size - 3, y + size - 3), (x + size - 3, y + 3), (x + size, y)])
            inner_col = [min(255, c + 25) for c in color_tuple]
            pygame.draw.rect(surface, inner_col, (x + 4, y + 4, size - 8, size - 8))

    def draw_ghost_piece(self, surface):
        if not self.current_piece:
            return
        ghost_y = self.get_ghost_y()
        if ghost_y == self.current_piece.y:
            return  # No need if already at the bottom

        for r, row in enumerate(self.current_piece.shape):
            for c, val in enumerate(row):
                if val:
                    gx = BOARD_X + (self.current_piece.x + c) * CELL_SIZE
                    gy = BOARD_Y + (ghost_y + r) * CELL_SIZE
                    # Draw subtle translucent outline
                    ghost_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    outline_col = (*self.current_piece.color, 90)
                    fill_col = (*self.current_piece.color, 35)
                    pygame.draw.rect(ghost_surf, fill_col, (1, 1, CELL_SIZE - 2, CELL_SIZE - 2))
                    pygame.draw.rect(ghost_surf, outline_col, (1, 1, CELL_SIZE - 2, CELL_SIZE - 2), 2)
                    surface.blit(ghost_surf, (gx, gy))

    def draw_panel(self, surface, x, y, width, height, title=""):
        # Glassmorphic rounded panel
        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (22, 27, 34, 220), (0, 0, width, height), border_radius=12)
        pygame.draw.rect(panel_surf, (56, 139, 253, 90), (0, 0, width, height), width=2, border_radius=12)
        surface.blit(panel_surf, (x, y))

        if title:
            t_font = self.get_font(13, bold=True)
            t_surf = t_font.render(title.upper(), True, COLOR_TEXT_MUTED)
            surface.blit(t_surf, (x + 16, y + 12))

    def draw_mini_piece(self, surface, piece, center_x, center_y, box_size=24):
        if not piece:
            return
        shape = piece.shape
        w = len(shape[0]) * box_size
        h = len(shape) * box_size
        start_x = center_x - w // 2
        start_y = center_y - h // 2
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if val:
                    bx = start_x + c * box_size
                    by = start_y + r * box_size
                    self.draw_beveled_block(surface, bx, by, box_size - 2, piece.color, piece.light, piece.dark)

    def draw(self):
        # Calculate screen shake offset
        shake_x = 0
        shake_y = 0
        if self.screen_shake_time > 0:
            shake_x = random.randint(-self.screen_shake_magnitude, self.screen_shake_magnitude)
            shake_y = random.randint(-self.screen_shake_magnitude, self.screen_shake_magnitude)

        render_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        render_surf.fill(COLOR_BG_DARK)

        # Subtle background grid dots
        for gx in range(0, WINDOW_WIDTH, 40):
            for gy in range(0, WINDOW_HEIGHT, 40):
                pygame.draw.circle(render_surf, (20, 26, 36), (gx, gy), 1)

        # 1. BOARD FRAME
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
        pygame.draw.rect(render_surf, COLOR_GRID_BG, board_rect, border_radius=6)

        # Draw grid lines inside board
        for c in range(GRID_COLS + 1):
            x = BOARD_X + c * CELL_SIZE
            pygame.draw.line(render_surf, COLOR_GRID_LINE, (x, BOARD_Y), (x, BOARD_Y + BOARD_HEIGHT), 1)
        for r in range(GRID_ROWS + 1):
            y = BOARD_Y + r * CELL_SIZE
            pygame.draw.line(render_surf, COLOR_GRID_LINE, (BOARD_X, y), (BOARD_X + BOARD_WIDTH, y), 1)

        # Draw locked blocks
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cell = self.grid[r][c]
                if cell:
                    bx = BOARD_X + c * CELL_SIZE
                    by = BOARD_Y + r * CELL_SIZE
                    self.draw_beveled_block(render_surf, bx + 1, by + 1, CELL_SIZE - 2, cell['color'], cell['light'], cell['dark'])

        # Draw Ghost piece
        if not self.game_over and self.current_piece:
            self.draw_ghost_piece(render_surf)

        # Draw Current falling piece
        if not self.game_over and self.current_piece:
            for r, row in enumerate(self.current_piece.shape):
                for c, val in enumerate(row):
                    if val:
                        bx = BOARD_X + (self.current_piece.x + c) * CELL_SIZE
                        by = BOARD_Y + (self.current_piece.y + r) * CELL_SIZE
                        if by >= BOARD_Y:  # Don't draw above top edge
                            self.draw_beveled_block(render_surf, bx + 1, by + 1, CELL_SIZE - 2,
                                                   self.current_piece.color, self.current_piece.light, self.current_piece.dark)

        # Glowing Board Border
        pygame.draw.rect(render_surf, (56, 139, 253), board_rect, width=3, border_radius=6)

        # 2. LEFT SIDEBAR (HOLD + CONTROLS)
        left_w = 200
        left_x = BOARD_X - left_w - 30

        # HOLD PANEL
        self.draw_panel(render_surf, left_x, BOARD_Y, left_w, 140, "SAQLASH [C]")
        if self.hold_piece:
            alpha = 255 if self.can_hold else 110
            self.draw_mini_piece(render_surf, self.hold_piece, left_x + left_w // 2, BOARD_Y + 80)
        else:
            hint = self.get_font(13).render("Bo'sh", True, (80, 90, 105))
            render_surf.blit(hint, hint.get_rect(center=(left_x + left_w // 2, BOARD_Y + 80)))

        # CONTROLS PANEL
        ctrl_y = BOARD_Y + 160
        ctrl_h = 320
        self.draw_panel(render_surf, left_x, ctrl_y, left_w, ctrl_h, "BOSHQARUV")
        controls_info = [
            ("← / →", "Chap / O'ng"),
            ("↑ / W", "Aylantirish"),
            ("↓ / S", "Sekin tushirish"),
            ("Bo'shliq", "Tez tashlash"),
            ("C / Shift", "Saqlash (Hold)"),
            ("P / Esc", "Pauza"),
            ("R", "Qayta o'ynash"),
            ("M", "Ovoz yoq/o'chir"),
        ]
        curr_cy = ctrl_y + 40
        for key_text, desc in controls_info:
            kf = self.get_font(12, bold=True)
            df = self.get_font(12)
            k_surf = kf.render(key_text, True, COLOR_ACCENT)
            d_surf = df.render(desc, True, COLOR_TEXT_MUTED)
            render_surf.blit(k_surf, (left_x + 14, curr_cy))
            render_surf.blit(d_surf, (left_x + 14, curr_cy + 16))
            curr_cy += 34

        # SOUND STATUS PANEL
        snd_y = ctrl_y + ctrl_h + 20
        self.draw_panel(render_surf, left_x, snd_y, left_w, 60)
        snd_text = "Ovoz: YOQILGAN 🔊" if self.sound_mgr.enabled else "Ovoz: O'CHIRILGAN 🔇"
        col = (70, 230, 120) if self.sound_mgr.enabled else (230, 90, 90)
        st_surf = self.get_font(13, bold=True).render(snd_text, True, col)
        render_surf.blit(st_surf, st_surf.get_rect(center=(left_x + left_w // 2, snd_y + 30)))

        # 3. RIGHT SIDEBAR (SCORE, NEXT, STATS)
        right_w = 200
        right_x = BOARD_X + BOARD_WIDTH + 30

        # SCORE PANEL
        self.draw_panel(render_surf, right_x, BOARD_Y, right_w, 140, "HISOB (SCORE)")
        s_val = self.get_font(28, bold=True).render(f"{self.score:,}", True, (255, 255, 255))
        render_surf.blit(s_val, (right_x + 16, BOARD_Y + 40))

        # HIGH SCORE
        hs_title = self.get_font(11, bold=True).render("REKORD", True, (240, 180, 50))
        hs_val = self.get_font(16, bold=True).render(f"{self.highscore:,}", True, (240, 180, 50))
        render_surf.blit(hs_title, (right_x + 16, BOARD_Y + 85))
        render_surf.blit(hs_val, (right_x + 16, BOARD_Y + 104))

        # NEXT PIECES PANEL
        next_y = BOARD_Y + 160
        next_h = 310
        self.draw_panel(render_surf, right_x, next_y, right_w, next_h, "KEYINGI (NEXT)")
        for idx, np in enumerate(self.next_pieces):
            py = next_y + 60 + idx * 85
            self.draw_mini_piece(render_surf, np, right_x + right_w // 2, py, box_size=20)

        # STATS PANEL (LEVEL & LINES)
        stats_y = next_y + next_h + 20
        self.draw_panel(render_surf, right_x, stats_y, right_w, 150, "STATISTIKA")
        # Level
        lvl_lbl = self.get_font(12, bold=True).render("BOSQICH (LEVEL):", True, COLOR_TEXT_MUTED)
        lvl_val = self.get_font(22, bold=True).render(str(self.level), True, (88, 166, 255))
        render_surf.blit(lvl_lbl, (right_x + 16, stats_y + 38))
        render_surf.blit(lvl_val, (right_x + 150, stats_y + 32))

        # Lines
        line_lbl = self.get_font(12, bold=True).render("QATORLAR:", True, COLOR_TEXT_MUTED)
        line_val = self.get_font(22, bold=True).render(str(self.lines), True, (63, 185, 80))
        render_surf.blit(line_lbl, (right_x + 16, stats_y + 82))
        render_surf.blit(line_val, (right_x + 150, stats_y + 76))

        # Particles & Floating Texts
        for p in self.particles:
            p.draw(render_surf)
        for ft in self.floating_texts:
            ft.draw(render_surf, self.get_font)

        # 4. OVERLAYS (PAUSE & GAME OVER)
        if self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 14, 20, 210))
            render_surf.blit(overlay, (0, 0))

            p_box = pygame.Rect(WINDOW_WIDTH // 2 - 180, WINDOW_HEIGHT // 2 - 100, 360, 200)
            pygame.draw.rect(render_surf, (22, 27, 34), p_box, border_radius=16)
            pygame.draw.rect(render_surf, (88, 166, 255), p_box, width=3, border_radius=16)

            p_title = self.get_font(32, bold=True).render("PAUZA", True, (255, 255, 255))
            p_sub = self.get_font(16).render("Davom etish uchun [P] yoki [ESC] bosing", True, COLOR_TEXT_MUTED)
            render_surf.blit(p_title, p_title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 35)))
            render_surf.blit(p_sub, p_sub.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30)))

        elif self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 14, 20, 220))
            render_surf.blit(overlay, (0, 0))

            go_box = pygame.Rect(WINDOW_WIDTH // 2 - 210, WINDOW_HEIGHT // 2 - 140, 420, 280)
            pygame.draw.rect(render_surf, (22, 27, 34), go_box, border_radius=16)
            pygame.draw.rect(render_surf, (255, 60, 80), go_box, width=3, border_radius=16)

            go_title = self.get_font(34, bold=True).render("O'YIN TUGADI!", True, (255, 80, 90))
            render_surf.blit(go_title, go_title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80)))

            score_str = f"Yakuniy ball: {self.score:,}"
            sc_surf = self.get_font(20, bold=True).render(score_str, True, (255, 255, 255))
            render_surf.blit(sc_surf, sc_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 25)))

            if self.score >= self.highscore and self.score > 0:
                rec_surf = self.get_font(16, bold=True).render("★ YANGI REKORD! ★", True, (255, 215, 0))
                render_surf.blit(rec_surf, rec_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))

            restart_str = "Qayta o'ynash uchun [R] yoki [BO'SHLIQ] bosing"
            r_surf = self.get_font(15, bold=True).render(restart_str, True, (88, 166, 255))
            render_surf.blit(r_surf, r_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 65)))

        # Blit to real screen with screen shake offset
        self.screen.fill(COLOR_BG_DARK)
        self.screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        if not self.game_over:
                            self.paused = not self.paused

                    elif event.key == pygame.K_m:
                        self.sound_mgr.toggle()

                    elif event.key == pygame.K_r:
                        self.reset_game()

                    elif not self.paused and not self.game_over:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.key_left_pressed = True
                            self.das_direction = -1
                            self.das_timer = 0
                            if self.is_valid_position(self.current_piece, offset_x=-1):
                                self.current_piece.x -= 1
                                self.sound_mgr.play('move')
                                if self.is_locking:
                                    self.lock_timer = 0

                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.key_right_pressed = True
                            self.das_direction = 1
                            self.das_timer = 0
                            if self.is_valid_position(self.current_piece, offset_x=1):
                                self.current_piece.x += 1
                                self.sound_mgr.play('move')
                                if self.is_locking:
                                    self.lock_timer = 0

                        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_x):
                            self.rotate_current_piece(clockwise=True)

                        elif event.key == pygame.K_z:
                            self.rotate_current_piece(clockwise=False)

                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.key_down_pressed = True

                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()

                        elif event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                            self.hold_current_piece()

                    elif self.game_over:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                            self.reset_game()

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.key_left_pressed = False
                        if self.key_right_pressed:
                            self.das_direction = 1
                            self.das_timer = 0
                        else:
                            self.das_direction = 0

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.key_right_pressed = False
                        if self.key_left_pressed:
                            self.das_direction = -1
                            self.das_timer = 0
                        else:
                            self.das_direction = 0

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.key_down_pressed = False

            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = TetrisGame()
    game.run()
