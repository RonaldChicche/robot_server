import pygame

# Inicialización
pygame.init()
#screen = pygame.display.set_mode((1000, 1000))
screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
pygame.display.set_caption("Simulación de línea de recogida")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
LIGHT_BLUE = (0, 200, 255)
GRAY = (180, 180, 180)

font = pygame.font.SysFont(None, 26)

# Escalado y posiciones
scale = 0.1 # 1 mm = 0.1 px
offset_x, offset_y = 1000, 1000

# Clase Robot
class Robot:
    def __init__(self, x_mm, y_mm, name, color):
        self.x_mm = x_mm
        self.y_mm = y_mm
        self.name = name
        self.color = color
        self.p_x = self.x_mm
        self.p_y = self.y_mm + 1500

    def update(self, p_x, p_y):
        self.p_x = p_x
        self.p_y = p_y
    
    def get_distance(self):
        return ((self.p_x - self.x_mm) ** 2 + (self.p_y - self.y_mm) ** 2) ** 0.5

    def draw(self):
        pygame.draw.circle(screen, self.color, to_px(self.x_mm, self.y_mm), 10)
        pygame.draw.line(screen, BLUE, to_px(self.x_mm, self.y_mm), to_px(self.p_x, self.p_y), 2)
        screen.blit(font.render(self.name, True, BLACK), to_px(self.x_mm, self.y_mm - 650))
        screen.blit(font.render(f"{self.get_distance():.2f} mm", True, BLACK), to_px(self.p_x, self.p_y + 50))

class Lamina:
    def __init__(self, dx_mm, dy_mm, dz_mm):
        self.dx_mm = dx_mm
        self.dy_mm = dy_mm
        self.dz_mm = dz_mm

    def update(self, dx_mm, dy_mm, dz_mm):
        self.dx_mm = dx_mm
        self.dy_mm = dy_mm
        self.dz_mm = dz_mm
    
    def draw(self):
        # draw rectangle
        pygame.draw.rect(screen, GRAY, (to_px(0, 1540 - self.dy_mm/2), scale_to_pix(self.dx_mm, self.dy_mm)))
        #print(f"{scale_to_pix(self.dx_mm, self.dy_mm)} -> {self.dx_mm}, {self.dy_mm}")

def to_px(x_mm, y_mm):
    #print(x_mm, y_mm, "-> ", int(x_mm * scale), int(y_mm * scale), "->", offset_x, offset_y)
    return int((x_mm + offset_x) * scale), int((y_mm + offset_y) * scale)

def scale_to_pix(x, y):
    return int(x * scale), int(y * scale)

def draw_scene():
    screen.fill(WHITE)
    
    # Tope y ejes
    pygame.draw.line(screen, BLACK, to_px(0, 0), to_px(0, 9000), 2)
    pygame.draw.line(screen, BLACK, to_px(0, 0), to_px(9000, 0), 2)
    pygame.draw.circle(screen, BLUE, to_px(0, 0), 6)
    screen.blit(font.render("Origen", True, BLACK), to_px(-150, -450))
    
    # Líneas hacia línea de recogida
    pygame.draw.line(screen, BLACK, to_px(0, 1540), to_px(9000, 1540), 2)
    screen.blit(font.render("Línea de recogida", True, BLACK), to_px(10000, 1540))
    
    # Líneas destino
    pygame.draw.line(screen, BLACK, to_px(0, 2097 + 503), to_px(9000, 2097 + 503), 2)
    screen.blit(font.render("Líneas destino", True, BLACK), to_px(10000, 2097 + 503))
    
    # Lamina
    lamina = Lamina(3658, 220, 6.35)
    lamina.draw()
    
    # Robots
    robot1 = Robot(1268, 0, "Robot 1", LIGHT_BLUE)
    robot1.draw()
    
    robot2 = Robot(1268+3500, 0, "Robot 2", LIGHT_BLUE)
    robot2.draw()   
    
    # Medidas (opcional)
    screen.blit(font.render("850", True, GRAY), to_px(100, 400))
    screen.blit(font.render("1540", True, GRAY), to_px(3600, 800))
    screen.blit(font.render("503", True, GRAY), to_px(3600, 2300))

# Bucle principal
running = True
while running:
    draw_scene()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
