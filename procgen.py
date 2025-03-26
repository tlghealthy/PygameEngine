import pygame, random, json, sys
from collections import deque
pygame.init()
with open("procgen_settings.json") as f:
    sett = json.load(f)

# Dungeon grid: 0 = wall, 1 = floor.
class Dungeon:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[0]*w for _ in range(h)]
        self.start = None
        self.end = None
        self.shortest_path = []
    def in_bounds(self, pos):
        x, y = pos; return 0 <= x < self.w and 0 <= y < self.h
    def carve(self, pos):
        x, y = pos
        if self.in_bounds(pos): self.grid[y][x] = 1
    def find_shortest_path(self, start, end):
        q = deque([start]); came = {start: None}
        while q:
            cur = q.popleft()
            if cur == end: break
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nxt = (cur[0]+dx, cur[1]+dy)
                if self.in_bounds(nxt) and self.grid[nxt[1]][nxt[0]]==1 and nxt not in came:
                    came[nxt] = cur; q.append(nxt)
        if end not in came: return []
        path = []; cur = end
        while cur is not None:
            path.append(cur); cur = came[cur]
        path.reverse(); return path
    def draw(self, surf, offset, cell):
        ox, oy = offset
        for y in range(self.h):
            for x in range(self.w):
                col = (200,200,200) if self.grid[y][x]==1 else (50,50,50)
                pygame.draw.rect(surf, col, (ox+x*cell, oy+y*cell, cell, cell))
        # Draw shortest path in yellow
        for pos in self.shortest_path:
            pygame.draw.rect(surf, (255,255,0), (ox+pos[0]*cell, oy+pos[1]*cell, cell, cell))
        # Mark start (green) and end (red)
        if self.start:
            pygame.draw.rect(surf, (0,255,0), (ox+self.start[0]*cell, oy+self.start[1]*cell, cell, cell))
        if self.end:
            pygame.draw.rect(surf, (255,0,0), (ox+self.end[0]*cell, oy+self.end[1]*cell, cell, cell))

# Generator with four strategies.
class DungeonGenerator:
    def __init__(self, sett):
        self.w, self.h = sett["grid_width"], sett["grid_height"]
        self.min_path = sett["min_path_length"]
        self.noise_thresh = sett["noise_threshold"]
        self.bsp_min = sett["bsp_min_size"]
    
    def carve_random_corridor(self, d, start, end):
        current = start
        while current != end:
            x, y = current
            candidates = []
            # Moves that reduce Manhattan distance
            if x < end[0]:
                candidates.append((x+1, y))
            if x > end[0]:
                candidates.append((x-1, y))
            if y < end[1]:
                candidates.append((x, y+1))
            if y > end[1]:
                candidates.append((x, y-1))
            # Introduce some lateral variation
            if random.random() < 0.3:
                lateral = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
                candidates.extend(lateral)
            # Filter out moves that are off-grid
            candidates = [pos for pos in candidates if d.in_bounds(pos)]
            current = random.choice(candidates)
            d.carve(current)

    # Strategy 1: POI Corridor
    def generate_poi(self):
        d = Dungeon(self.w, self.h)
        start, end = (0, 0), (self.w - 1, self.h - 1)
        cur = start; d.carve(cur)
        for _ in range(self.min_path):
            dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nxt = (cur[0] + dx, cur[1] + dy)
            if d.in_bounds(nxt):
                cur = nxt; d.carve(cur)
        # Replace the straight-line connection with our randomized corridor
        self.carve_random_corridor(d, cur, end)
        d.start, d.end = start, end
        d.shortest_path = d.find_shortest_path(d.start, d.end)
        return d

    # Strategy 2: Maze via DFS/random walk
    def generate_maze(self):
        d = Dungeon(self.w, self.h)
        start = (random.randrange(0, self.w, 2), random.randrange(0, self.h, 2))
        d.start = start; d.carve(start)
        stack = [start]
        while stack:
            x, y = stack[-1]
            nbrs = []
            for dx, dy in [(2,0), (-2,0), (0,2), (0,-2)]:
                nxt = (x+dx, y+dy)
                if d.in_bounds(nxt) and d.grid[nxt[1]][nxt[0]]==0:
                    nbrs.append(nxt)
            if nbrs:
                nxt = random.choice(nbrs)
                mx, my = (x+nxt[0])//2, (y+nxt[1])//2
                d.carve((mx,my)); d.carve(nxt); stack.append(nxt)
            else:
                stack.pop()
        # Use BFS to choose farthest cell from start as end.
        q = deque([start]); dist = {start: 0}
        while q:
            cur = q.popleft()
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nxt = (cur[0]+dx, cur[1]+dy)
                if d.in_bounds(nxt) and d.grid[nxt[1]][nxt[0]]==1 and nxt not in dist:
                    dist[nxt] = dist[cur] + 1; q.append(nxt)
        farthest = start; maxd = 0
        for pos, dval in dist.items():
            if dval > maxd: maxd = dval; farthest = pos
        d.end = farthest
        d.shortest_path = d.find_shortest_path(d.start, d.end)
        return d
    # Strategy 3: Noise-based terrain with smoothing.
    def generate_noise(self):
        d = Dungeon(self.w, self.h)
        # Create a noise-based floorplan
        for y in range(self.h):
            for x in range(self.w):
                d.grid[y][x] = 1 if random.random() > self.noise_thresh else 0
        # Smooth the noise to form coherent areas
        for _ in range(2):
            new = [[d.grid[y][x] for x in range(self.w)] for y in range(self.h)]
            for y in range(1, self.h-1):
                for x in range(1, self.w-1):
                    cnt = sum(d.grid[ny][nx] for nx in range(x-1, x+2) for ny in range(y-1, y+2))
                    new[y][x] = 1 if cnt >= 5 else 0
            d.grid = new
        start, end = (0, 0), (self.w - 1, self.h - 1)
        # Use the randomized corridor function to carve a winding connection
        d.carve(start)
        self.carve_random_corridor(d, start, end)
        d.start, d.end = start, end
        d.shortest_path = d.find_shortest_path(d.start, d.end)
        return d
    # Strategy 4: BSP dungeon – partition, carve rooms, and connect centers.
    def generate_bsp(self):
        d = Dungeon(self.w, self.h)
        rooms = []
        def split(x, y, w, h):
            if w < self.bsp_min*2 or h < self.bsp_min*2:
                rx, ry = x+1, y+1; rw, rh = max(2, w-2), max(2, h-2)
                rooms.append((rx, ry, rw, rh))
                for i in range(rx, rx+rw):
                    for j in range(ry, ry+rh):
                        d.carve((i,j))
                return
            if w > h:
                sx = random.randint(x+self.bsp_min, x+w-self.bsp_min)
                split(x, y, sx-x, h); split(sx, y, x+w-sx, h)
            else:
                sy = random.randint(y+self.bsp_min, y+h-self.bsp_min)
                split(x, y, w, sy-y); split(x, sy, w, y+h-sy)
        split(0, 0, self.w, self.h)
        if rooms:
            first = rooms[0]
            last = rooms[-1]
            d.start = (first[0] + first[2]//2, first[1] + first[3]//2)
            d.end = (last[0] + last[2]//2, last[1] + last[3]//2)
            for i in range(1, len(rooms)):
                x1 = rooms[i-1][0] + rooms[i-1][2]//2
                y1 = rooms[i-1][1] + rooms[i-1][3]//2
                x2 = rooms[i][0] + rooms[i][2]//2
                y2 = rooms[i][1] + rooms[i][3]//2
                cx, cy = x1, y1
                while cx != x2:
                    cx += 1 if cx < x2 else -1; d.carve((cx,cy))
                while cy != y2:
                    cy += 1 if cy < y2 else -1; d.carve((cx,cy))
        else:
            d.start, d.end = (0,0), (self.w-1, self.h-1)
        d.shortest_path = d.find_shortest_path(d.start, d.end)
        return d

# Prepare dungeons using different strategies.
gen = DungeonGenerator(sett)
d_poi = gen.generate_poi()
d_maze = gen.generate_maze()
d_noise = gen.generate_noise()
d_bsp = gen.generate_bsp()

sw, sh = sett["screen_width"], sett["screen_height"]
cell = sett["cell_size"]
screen = pygame.display.set_mode((sw, sh))
pygame.display.set_caption("Procedural Dungeon Generation Demo")
clock = pygame.time.Clock()
offsets = [(10,10), (sw//2+10,10), (10,sh//2+10), (sw//2+10,sh//2+10)]
dungeons = [d_poi, d_maze, d_noise, d_bsp]
labels = ["POI Corridor", "Maze DFS", "Noise-Based", "BSP Rooms"]
font = pygame.font.SysFont(None, 24)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            d_poi = gen.generate_poi()
            d_maze = gen.generate_maze()
            d_noise = gen.generate_noise()
            d_bsp = gen.generate_bsp()
            dungeons = [d_poi, d_maze, d_noise, d_bsp]
    screen.fill((30,30,30))
    for off, d, lab in zip(offsets, dungeons, labels):
        d.draw(screen, off, cell)
        txt = font.render(lab, True, (240,240,240))
        screen.blit(txt, (off[0], off[1]-24))
    pygame.display.flip()
    clock.tick(30)
pygame.quit(); sys.exit()
