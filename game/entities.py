import pygame
from game.maze import CELL, bfs

SPEED = 2
ENEMY_START_INTERVAL = 30   # frames between cell moves at the start (slower than the player)
ENEMY_GRACE_FRAMES = 120    # enemies hold still this long at the start of a round


class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2
        self.rect = pygame.Rect(cx - 10, cy - 10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, wall_rects, rows, cols):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = SPEED
        # Axes are tested separately so the player slides along walls
        nr = self.rect.move(dx, 0)
        if self._valid(nr, wall_rects, rows, cols): self.rect = nr
        nr = self.rect.move(0, dy)
        if self._valid(nr, wall_rects, rows, cols): self.rect = nr

    def _valid(self, rect, wall_rects, rows, cols):
        # Stay inside the maze area
        if rect.left < 0 or rect.top < 0 or rect.right > cols * CELL or rect.bottom > rows * CELL:
            return False
        # Blocked by any wall
        return rect.collidelist(wall_rects) == -1

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)


class Enemy:
    def __init__(self, r, c, move_interval=ENEMY_START_INTERVAL, grace=ENEMY_GRACE_FRAMES):
        self.r, self.c = r, c
        cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2
        self.rect = pygame.Rect(cx - 12, cy - 12, 24, 24)
        self.color = (220, 60, 60)
        self.frozen_color = (130, 200, 255)
        self.timer = -grace              # negative = start-of-round grace period
        self.move_interval = move_interval  # frames between cell moves
        self.frozen = False

    def update(self, walls, player, rows, cols):
        if self.frozen:
            return
        self.timer += 1
        if self.timer >= self.move_interval:
            self.timer = 0
            pr, pc = player.rect.centery // CELL, player.rect.centerx // CELL
            step = bfs(walls, (self.r, self.c), (pr, pc), rows, cols)
            if step:
                dr, dc = step
                self.r += dr
                self.c += dc
                cx, cy = self.c * CELL + CELL // 2, self.r * CELL + CELL // 2
                self.rect.center = (cx, cy)

    def draw(self, screen):
        color = self.frozen_color if self.frozen else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        if self.frozen:
            # ice outline
            pygame.draw.rect(screen, (255, 255, 255), self.rect, width=2, border_radius=5)
            # closed eyes
            for ex in [self.rect.x + 4, self.rect.x + 14]:
                pygame.draw.line(screen, (40, 60, 100), (ex, self.rect.y + 9), (ex + 6, self.rect.y + 9), 2)
            # snowflake above the enemy
            cx, cy = self.rect.centerx, self.rect.top - 8
            for dx, dy in [(0, 6), (5, 3), (5, -3)]:
                pygame.draw.line(screen, (120, 200, 255), (cx - dx, cy - dy), (cx + dx, cy + dy), 2)
        else:
            # eyes
            for ex in [self.rect.x + 4, self.rect.x + 14]:
                pygame.draw.circle(screen, (255, 255, 255), (ex, self.rect.y + 8), 4)
                pygame.draw.circle(screen, (0, 0, 0), (ex + 1, self.rect.y + 8), 2)
