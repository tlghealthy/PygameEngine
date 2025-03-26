import pygame, json, math

# Load settings from JSON file
with open('graphics_settings.json') as f:
    SETTINGS = json.load(f)

# Base Shape class
class Shape:
    def __init__(self, color=SETTINGS["default_color"]):
        self.color = color
    def draw(self, surface):
        raise NotImplementedError

# Basic shapes
class Triangle(Shape):
    def __init__(self, points, color=SETTINGS["default_color"]):
        super().__init__(color)
        self.points = points
    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)

class Quad(Shape):
    def __init__(self, points, color=SETTINGS["default_color"]):
        super().__init__(color)
        self.points = points
    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)

class Circle(Shape):
    def __init__(self, center, radius, color=SETTINGS["default_color"]):
        super().__init__(color)
        self.center, self.radius = center, radius
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.center, self.radius)

# Helper functions to compute vertices

def star_points(center, outer_radius, inner_radius, num_points):
    cx, cy = center
    angle_step = math.pi / num_points  # Half the angle between star tips
    points = []
    for i in range(2 * num_points):
        r = outer_radius if i % 2 == 0 else inner_radius
        angle = i * angle_step
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        points.append((x, y))
    return points

def regular_polygon_points(center, radius, num_sides):
    cx, cy = center
    angle_step = 2 * math.pi / num_sides
    points = []
    for i in range(num_sides):
        angle = i * angle_step
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        points.append((x, y))
    return points

# Extended shapes

class Star(Shape):
    def __init__(self, center, outer_radius, inner_radius, num_points, color=SETTINGS["default_color"]):
        super().__init__(color)
        self.points = star_points(center, outer_radius, inner_radius, num_points)
    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)

class Polygon(Shape):
    def __init__(self, center, radius, num_sides, color=SETTINGS["default_color"]):
        super().__init__(color)
        self.points = regular_polygon_points(center, radius, num_sides)
    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)

# Graphics engine that manages drawing and the game loop
class GraphicsEngine:
    def __init__(self, settings):
        pygame.init()
        self.screen = pygame.display.set_mode((settings["screen_width"], settings["screen_height"]))
        self.clock = pygame.time.Clock()
        self.shapes = []
        self.bg_color = settings["background_color"]
        self.fps = settings["fps"]
    def add_shape(self, shape):
        self.shapes.append(shape)
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
            self.screen.fill(self.bg_color)
            for shape in self.shapes:
                shape.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

# Example usage with various shapes
if __name__ == '__main__':
    engine = GraphicsEngine(SETTINGS)
    
    # Basic shapes
    engine.add_shape(Triangle([(100, 100), (150, 50), (200, 100)], [255, 0, 0]))
    engine.add_shape(Quad([(300, 300), (400, 300), (400, 400), (300, 400)], [0, 255, 0]))
    engine.add_shape(Circle((500, 150), 50, [0, 0, 255]))
    
    # Star with 5 points (alternates between outer and inner radius)
    engine.add_shape(Star((200, 500), 60, 30, 5, [255, 255, 0]))
    
    # Regular polygon examples:
    # Hexagon (6 sides)
    engine.add_shape(Polygon((500, 500), 50, 6, [255, 0, 255]))
    # Octagon (8 sides)
    engine.add_shape(Polygon((700, 300), 40, 8, [0, 255, 255]))
    
    engine.run()
