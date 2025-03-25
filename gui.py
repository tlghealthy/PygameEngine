import pygame, json, os

# --- Load GUI settings ---
if os.path.exists("gui_settings.json"):
    with open("gui_settings.json") as f:
        SETTINGS = json.load(f)
else:
    SETTINGS = {
        "padding": 10,
        "colors": {
            "background": [30, 30, 30],
            "button": [70, 130, 180],
            "button_hover": [100, 160, 210],
            "label": [255, 255, 255],
            "panel": [50, 50, 50],
            "border": [200, 200, 200],
            "text_input_bg": [200, 200, 200],
            "checkbox_box": [255, 255, 255],
            "slider_track": [100, 100, 100]
        },
        "font_name": "freesansbold.ttf",
        "font_size": 20
    }

# --- Base Widget Class ---
class Widget:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.children = []
        self.visible = True
    def add(self, widget):
        self.children.append(widget)
    def handle_event(self, event):
        for child in self.children:
            child.handle_event(event)
    def update(self):
        for child in self.children:
            child.update()
    def draw(self, surface):
        for child in self.children:
            child.draw(surface)

# --- Basic Label ---
class Label(Widget):
    def __init__(self, rect, text, font=None, color=None):
        super().__init__(rect)
        self.text = text
        self.font = font or pygame.font.Font(SETTINGS["font_name"], SETTINGS["font_size"])
        self.color = color or SETTINGS["colors"]["label"]
        self.image = self.font.render(self.text, True, self.color)
    def draw(self, surface):
        if self.visible:
            surface.blit(self.image, self.rect)
        super().draw(surface)

# --- Clickable Button ---
class Button(Widget):
    def __init__(self, rect, text, callback, font=None, color=None, hover_color=None):
        super().__init__(rect)
        self.text = text
        self.callback = callback
        self.font = font or pygame.font.Font(SETTINGS["font_name"], SETTINGS["font_size"])
        self.color = color or SETTINGS["colors"]["button"]
        self.hover_color = hover_color or SETTINGS["colors"]["button_hover"]
        self.current_color = self.color
        self.image = self.font.render(self.text, True, SETTINGS["colors"]["label"])
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.current_color = self.hover_color if self.rect.collidepoint(event.pos) else self.color
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.callback()
        super().handle_event(event)
    def draw(self, surface):
        if self.visible:
            pygame.draw.rect(surface, self.current_color, self.rect)
            pygame.draw.rect(surface, SETTINGS["colors"]["border"], self.rect, 2)
            surface.blit(self.image, self.image.get_rect(center=self.rect.center))
        super().draw(surface)

# --- Panel Container ---
class Panel(Widget):
    def __init__(self, rect, bg_color=None, padding=None):
        super().__init__(rect)
        self.bg_color = bg_color or SETTINGS["colors"]["panel"]
        self.padding = padding or SETTINGS["padding"]
    def draw(self, surface):
        if self.visible:
            pygame.draw.rect(surface, self.bg_color, self.rect)
            pygame.draw.rect(surface, SETTINGS["colors"]["border"], self.rect, 2)
        super().draw(surface)

# --- New Widget: Draggable Collapsible Panel ---
class CollapsiblePanel(Panel):
    def __init__(self, rect, title, collapse_direction="down", bg_color=None, padding=None, draggable=False):
        super().__init__(rect, bg_color, padding)
        self.title = title
        self.collapse_direction = collapse_direction.lower()  # "up" or "down"
        self.collapsed = False
        self.full_rect = self.rect.copy()
        self.font = pygame.font.Font(SETTINGS["font_name"], SETTINGS["font_size"])
        self.header_height = SETTINGS["padding"] * 2 + self.font.get_height()
        self.draggable = draggable
        self.dragging = False
        self.drag_offset = (0, 0)
    
    def update_rect(self):
        # Recalculate self.rect based on full_rect and collapse state.
        if self.collapsed:
            if self.collapse_direction == "down":
                self.rect = pygame.Rect(self.full_rect.x, self.full_rect.y, self.full_rect.width, self.header_height)
            else:  # "up"
                self.rect = pygame.Rect(self.full_rect.x, self.full_rect.bottom - self.header_height, self.full_rect.width, self.header_height)
        else:
            self.rect = self.full_rect.copy()
    
    def toggle(self):
        self.collapsed = not self.collapsed
        self.update_rect()
    
    def handle_event(self, event):
        header_margin = 5
        # Compute header rect based on full_rect.
        if self.collapse_direction == "down":
            header_rect = pygame.Rect(
                self.full_rect.x + header_margin,
                self.full_rect.y + header_margin,
                self.full_rect.width - 2 * header_margin,
                self.header_height - 2 * header_margin
            )
        else:
            header_rect = pygame.Rect(
                self.full_rect.x + header_margin,
                self.full_rect.bottom - self.header_height + header_margin,
                self.full_rect.width - 2 * header_margin,
                self.header_height - 2 * header_margin
            )
        # Compute triangle icon bounding box.
        triangle_margin = 10
        icon_width, icon_height = 12, 12
        icon_center = (header_rect.right - triangle_margin - icon_width // 2, header_rect.centery)
        triangle_rect = pygame.Rect(icon_center[0] - icon_width//2, icon_center[1] - icon_height//2, icon_width, icon_height)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if header_rect.collidepoint(event.pos):
                if triangle_rect.collidepoint(event.pos):
                    # Click on triangle toggles collapse.
                    self.toggle()
                else:
                    # Otherwise, if draggable, start dragging.
                    if self.draggable:
                        self.dragging = True
                        self.drag_offset = (event.pos[0] - self.full_rect.x, event.pos[1] - self.full_rect.y)
                    else:
                        # If not draggable, treat header click as toggle.
                        self.toggle()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Compute delta movement.
            old_x, old_y = self.full_rect.topleft
            self.full_rect.x = event.pos[0] - self.drag_offset[0]
            self.full_rect.y = event.pos[1] - self.drag_offset[1]
            dx = self.full_rect.x - old_x
            dy = self.full_rect.y - old_y
            # Update child positions so they move with the panel.
            for child in self.children:
                child.rect.x += dx
                child.rect.y += dy
            self.update_rect()
        # Only pass events to children if expanded.
        if not self.collapsed:
            super().handle_event(event)
    
    def draw(self, surface):
        # Draw panel background.
        if not self.collapsed:
            pygame.draw.rect(surface, self.bg_color, self.full_rect)
            pygame.draw.rect(surface, SETTINGS["colors"]["border"], self.full_rect, 2)
            super().draw(surface)
        else:
            pygame.draw.rect(surface, self.bg_color, self.rect)
            pygame.draw.rect(surface, SETTINGS["colors"]["border"], self.rect, 2)
        # Always draw the header button on top.
        header_margin = 5
        if self.collapse_direction == "down":
            header_rect = pygame.Rect(
                self.full_rect.x + header_margin,
                self.full_rect.y + header_margin,
                self.full_rect.width - 2 * header_margin,
                self.header_height - 2 * header_margin
            )
        else:
            header_rect = pygame.Rect(
                self.full_rect.x + header_margin,
                self.full_rect.bottom - self.header_height + header_margin,
                self.full_rect.width - 2 * header_margin,
                self.header_height - 2 * header_margin
            )
        header_button_color = SETTINGS["colors"]["button"]
        pygame.draw.rect(surface, header_button_color, header_rect)
        pygame.draw.rect(surface, SETTINGS["colors"]["border"], header_rect, 2)
        # Draw title text on the left.
        title_surf = self.font.render(self.title, True, SETTINGS["colors"]["label"])
        title_rect = title_surf.get_rect(midleft=(header_rect.x + header_margin, header_rect.centery))
        surface.blit(title_surf, title_rect)
        # Draw triangle icon on the right.
        triangle_margin = 10
        icon_width, icon_height = 12, 12
        icon_center = (header_rect.right - triangle_margin - icon_width // 2, header_rect.centery)
        if self.collapsed:
            arrow_direction = "up" if self.collapse_direction == "down" else "down"
        else:
            arrow_direction = self.collapse_direction
        if arrow_direction == "down":
            points = [
                (icon_center[0] - icon_width // 2, icon_center[1] - icon_height // 2),
                (icon_center[0] + icon_width // 2, icon_center[1] - icon_height // 2),
                (icon_center[0], icon_center[1] + icon_height // 2)
            ]
        else:  # "up"
            points = [
                (icon_center[0] - icon_width // 2, icon_center[1] + icon_height // 2),
                (icon_center[0] + icon_width // 2, icon_center[1] + icon_height // 2),
                (icon_center[0], icon_center[1] - icon_height // 2)
            ]
        pygame.draw.polygon(surface, SETTINGS["colors"]["label"], points)

# --- Additional Widgets (TextInput, Checkbox, Slider) remain unchanged ---
class TextInput(Widget):
    def __init__(self, rect, text="", callback=None, font=None, text_color=None, bg_color=None, border_color=None):
        super().__init__(rect)
        self.text = text
        self.callback = callback
        self.font = font or pygame.font.Font(SETTINGS["font_name"], SETTINGS["font_size"])
        self.text_color = text_color or SETTINGS["colors"]["label"]
        self.bg_color = bg_color or SETTINGS["colors"].get("text_input_bg", [200,200,200])
        self.border_color = border_color or SETTINGS["colors"]["border"]
        self.active = False
        self.cursor_visible = True
        self.cursor_counter = 0
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                if self.callback:
                    self.callback(self.text)
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        super().handle_event(event)
    def update(self):
        if self.active:
            self.cursor_counter = (self.cursor_counter + 1) % 60
            self.cursor_visible = self.cursor_counter < 30
        super().update()
    def draw(self, surface):
        if self.visible:
            pygame.draw.rect(surface, self.bg_color, self.rect)
            pygame.draw.rect(surface, self.border_color, self.rect, 2)
            txt_surf = self.font.render(self.text, True, self.text_color)
            surface.blit(txt_surf, (self.rect.x+5, self.rect.y+5))
            if self.active and self.cursor_visible:
                cursor_x = self.rect.x+5+txt_surf.get_width()+2
                cursor_y = self.rect.y+5
                pygame.draw.line(surface, self.text_color, (cursor_x, cursor_y), (cursor_x, cursor_y+txt_surf.get_height()), 2)
        super().draw(surface)

class Checkbox(Widget):
    def __init__(self, rect, text, initial=False, callback=None, font=None, box_size=20, text_color=None, box_color=None, check_color=None):
        super().__init__(rect)
        self.text = text
        self.value = initial
        self.callback = callback
        self.font = font or pygame.font.Font(SETTINGS["font_name"], SETTINGS["font_size"])
        self.box_size = box_size
        self.text_color = text_color or SETTINGS["colors"]["label"]
        self.box_color = box_color or SETTINGS["colors"].get("checkbox_box", [255,255,255])
        self.check_color = check_color or SETTINGS["colors"]["button"]
        self.image = self.font.render(self.text, True, self.text_color)
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                if self.callback:
                    self.callback(self.value)
        super().handle_event(event)
    def draw(self, surface):
        if self.visible:
            box_rect = pygame.Rect(self.rect.x, self.rect.y, self.box_size, self.box_size)
            pygame.draw.rect(surface, self.box_color, box_rect)
            pygame.draw.rect(surface, SETTINGS["colors"]["border"], box_rect, 2)
            if self.value:
                inner = box_rect.inflate(-4, -4)
                pygame.draw.rect(surface, self.check_color, inner)
            surface.blit(self.image, (self.rect.x+self.box_size+5, self.rect.y))
        super().draw(surface)

class Slider(Widget):
    def __init__(self, rect, min_value, max_value, initial, callback=None, track_color=None, handle_color=None):
        super().__init__(rect)
        self.min = min_value
        self.max = max_value
        self.value = initial
        self.callback = callback
        self.track_color = track_color or SETTINGS["colors"].get("slider_track", [100,100,100])
        self.handle_color = handle_color or SETTINGS["colors"]["button"]
        self.dragging = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos)
        super().handle_event(event)
    def update_value(self, pos):
        rel_x = pos[0] - self.rect.x
        rel_x = max(0, min(rel_x, self.rect.width))
        ratio = rel_x / self.rect.width
        self.value = self.min + ratio * (self.max - self.min)
        if self.callback:
            self.callback(self.value)
    def draw(self, surface):
        if self.visible:
            track_rect = pygame.Rect(self.rect.x, self.rect.centery - 5, self.rect.width, 10)
            pygame.draw.rect(surface, self.track_color, track_rect)
            ratio = (self.value - self.min) / (self.max - self.min)
            handle_x = self.rect.x + ratio * self.rect.width
            handle_center = (int(handle_x), self.rect.centery)
            pygame.draw.circle(surface, self.handle_color, handle_center, 10)
            pygame.draw.circle(surface, SETTINGS["colors"]["border"], handle_center, 10, 2)
        super().draw(surface)

# --- Example: Draggable Collapsible Panel with Child GUI Elements ---
def example_draggable_collapsible_panel():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # Create a collapsible panel with draggable enabled.
    panel = CollapsiblePanel((50, 50, 700, 400), "Draggable Panel", collapse_direction="down", draggable=True)
    panel.add(Label((70, 100, 200, 30), "Panel Content"))
    panel.add(Button((70, 150, 150, 40), "A Button", lambda: print("Button clicked inside panel!")))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            panel.handle_event(event)
        panel.update()
        screen.fill(SETTINGS["colors"]["background"])
        panel.draw(screen)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()

if __name__ == "__main__":
    example_draggable_collapsible_panel()
