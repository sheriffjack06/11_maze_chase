import random
import pygame
from game.maze import generate_maze, build_wall_rects, CELL
from game.entities import Player, Enemy, ENEMY_START_INTERVAL

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HUD_H = 64
HEIGHT = ROWS * CELL + HUD_H
FPS = 60

# Difficulty ramp
RAMP_MS = 15_000          # every 15 seconds...
RAMP_STEP = 2             # ...enemies move 2 frames faster per cell
MIN_INTERVAL = 5          # ...down to this minimum
MAX_TIER_IDX = -(-(ENEMY_START_INTERVAL - MIN_INTERVAL) // RAMP_STEP)  # ceil division

# Power pellet
FREEZE_FRAMES = 300
PELLET_RADIUS = 9


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.hud_font = pygame.font.SysFont("monospace", 18)
        self.tiny_font = pygame.font.SysFont("monospace", 13, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.wall_rects = build_wall_rects(self.walls, ROWS, COLS)
        self.player = Player(0, 0)

        # One enemy in each of the other three corners
        corners = [(ROWS - 1, COLS - 1), (0, COLS - 1), (ROWS - 1, 0)]
        self.enemies = [Enemy(r, c) for r, c in corners]

        exit_cell = (ROWS // 2, COLS // 2)
        self.exit_rect = pygame.Rect(exit_cell[1] * CELL + 5, exit_cell[0] * CELL + 5, CELL - 10, CELL - 10)

        # Power pellet: random cell that isn't the exit, a corner, or right next to the player
        corner_cells = {(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)}
        candidates = [(r, c) for r in range(ROWS) for c in range(COLS)
                      if (r, c) != exit_cell and (r, c) not in corner_cells and r + c >= 4]
        pr, pc = random.choice(candidates)
        self.pellet_rect = pygame.Rect(0, 0, PELLET_RADIUS * 2, PELLET_RADIUS * 2)
        self.pellet_rect.center = (pc * CELL + CELL // 2, pr * CELL + CELL // 2)
        self.pellet_active = True
        self.freeze_timer = 0

        # Difficulty ramp
        self.start_ticks = pygame.time.get_ticks()
        self.next_ramp_ms = RAMP_MS
        self.tier = 0

        self.score = 0
        self.caught = False
        self.won = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def _apply_difficulty_ramp(self):
        elapsed = pygame.time.get_ticks() - self.start_ticks
        while elapsed >= self.next_ramp_ms:
            self.next_ramp_ms += RAMP_MS
            self.tier += 1
            for enemy in self.enemies:
                enemy.move_interval = max(MIN_INTERVAL, enemy.move_interval - RAMP_STEP)

    def _tier_label(self):
        idx = min(self.tier, MAX_TIER_IDX)
        label = f"Tier {idx + 1}"
        if idx >= MAX_TIER_IDX:
            label += " (MAX)"
        return label

    def update(self):
        if self.caught or self.won: return

        self.score += 1                      # one point per frame alive
        self._apply_difficulty_ramp()

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.wall_rects, ROWS, COLS)

        # Power pellet pickup -> freeze every enemy for 300 frames
        if self.pellet_active and self.player.rect.colliderect(self.pellet_rect):
            self.pellet_active = False
            self.freeze_timer = FREEZE_FRAMES
            for enemy in self.enemies:
                enemy.frozen = True

        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            if self.freeze_timer == 0:
                for enemy in self.enemies:
                    enemy.frozen = False

        # Each enemy runs its own BFS toward the player
        for enemy in self.enemies:
            enemy.update(self.walls, self.player, ROWS, COLS)

        # Frozen enemies are harmless
        for enemy in self.enemies:
            if not enemy.frozen and self.player.rect.colliderect(enemy.rect):
                self.caught = True
                break

        if not self.caught and self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc = (50, 40, 60)
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * CELL, r * CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, wc, (x, y), (x + CELL, y), 3)
                if w[1]: pygame.draw.line(self.screen, wc, (x, y + CELL), (x + CELL, y + CELL), 3)
                if w[2]: pygame.draw.line(self.screen, wc, (x + CELL, y), (x + CELL, y + CELL), 3)
                if w[3]: pygame.draw.line(self.screen, wc, (x, y), (x, y + CELL), 3)

        pygame.draw.rect(self.screen, (80, 200, 80), self.exit_rect, border_radius=4)
        lbl = self.tiny_font.render("EXIT", True, (20, 80, 20))
        self.screen.blit(lbl, lbl.get_rect(center=self.exit_rect.center))

        if self.pellet_active:
            pygame.draw.circle(self.screen, (250, 220, 40), self.pellet_rect.center, PELLET_RADIUS)
            pygame.draw.circle(self.screen, (170, 140, 0), self.pellet_rect.center, PELLET_RADIUS, 2)

        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD
        hud = pygame.Rect(0, ROWS * CELL, WIDTH, HUD_H)
        pygame.draw.rect(self.screen, (30, 30, 50), hud)
        line1 = f"Survived: {self.score // 60}s   Enemy speed: {self._tier_label()}"
        self.screen.blit(self.hud_font.render(line1, True, (220, 220, 220)), (8, ROWS * CELL + 8))
        if self.freeze_timer > 0:
            secs = (self.freeze_timer + 59) // 60
            line2 = self.hud_font.render(f"ENEMIES FROZEN: {secs}s", True, (130, 200, 255))
        else:
            line2 = self.hud_font.render("Reach EXIT! Yellow = freeze  R=Restart", True, (170, 170, 170))
        self.screen.blit(line2, (8, ROWS * CELL + 34))

        if self.caught:
            self._overlay("CAUGHT!", (220, 60, 60))
        if self.won:
            self._overlay("ESCAPED!", (80, 220, 80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 140))
        self.screen.blit(surf, (0, 0))
        mid = ROWS * CELL // 2
        msg = self.big_font.render(text, True, color)
        final = self.font.render(f"Final score: {self.score}  ({self.score // 60}s survived)", True, (255, 255, 255))
        sub = self.font.render("Press R to Restart", True, (200, 200, 200))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, mid - 55))
        self.screen.blit(final, (WIDTH // 2 - final.get_width() // 2, mid))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, mid + 35))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
