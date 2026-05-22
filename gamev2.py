from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24, GLUT_BITMAP_HELVETICA_18
import time
import math
import random

WINDOW_W = 1000
WINDOW_H = 800
GRID_LENGTH = 400
FOOD_SIZE = 10
SEGMENT_SPACING = 25
TILE_SIZE = 50

fovY = 80
camera_pos = [0, -500, 500]

current_screen = "intro"
start_time = time.time()
title_y = 400
intro_phase = 1

SERPENTS = [
    ("Nyx", (0.05, 0.10, 0.40)),
    ("Vex", (0.00, 0.35, 0.65)),
    ("Byte", (0.40, 0.70, 1.00)),
    ("Flux", (0.00, 0.85, 0.90)),
    ("Qbit", (0.20, 0.30, 0.80)),
    ("Cryo", (0.75, 0.90, 1.00)),
]
serpent_index = 0
serpent_rotation = 0.0

snake_pos = [0.0, 0.0]
snake_angle = 0.0
bob_time = 0.0
snake_body = []
pos_history = []

food_shapes = ["sphere", "cube", "cylinder"]
food_list = []
score = 0
lives = 3
shed_count = 0
current_level = 1
level_score = [0, 6, 12, 20]
last_food = None
multiplier = 1
combo_count = 0
combo_flash = 0.0
combo_duration = 1.5

health = 100.0
health_drain = 0.015
stamina = 100.0
knockback_cost = 20
knockback_cooldown = 0.0
knockback_force = 180
knockback_speed = 1.2

speed_potions = []
speed_boost_end = 0.0
boost_speed = 20
normal_speed = 10
potion_spawn_timer = 0

magnet_potions = []
magnet_active = False
magnet_end_time = 0.0
magnet_radius = 200
magnet_pull = 4.0

mystery_orbs = []
orb_spawn_timer = 0

obstacle_cubes = []
cube_spawn_timer = 0
cube_size = 25

enemy_pos = [200.0, 200.0]
enemy_angle = 180.0
enemy_active = False
enemy_knocked = False
enemy_knockback_target = [0.0, 0.0]

enemy2_pos = [-200.0, -200.0]
enemy2_angle = 0.0
enemy2_active = False
enemy2_knocked = False
enemy2_knockback_target = [0.0, 0.0]

rot_zones = []
rot_timer = 0.0
rot_damage = 0.05

mimic_list = []

MUTATIONS = [
    ("Oracle Trace", "See where next 3 food items will spawn"),
    ("Titan Shell", "Survive 1 cube hit; move 10% slower"),
    ("Neural Sense", "Cubes glow 2x longer before rising"),
]
mutation = None
mutation_choice_pending = False
mutation_index = 0
hardened_used = False
forked_previews = []

effective_boundary = float(GRID_LENGTH)
shrink_rate = 0.02
min_boundary = 150.0
game_over = False
game_won = False


def drawText(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def begin2D():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()


def end2D():
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def drawQuad2D(x, y, w, h):
    begin2D()
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    end2D()


def drawTriangle2D(pts):
    begin2D()
    glBegin(GL_TRIANGLES)
    for px, py in pts:
        glVertex2f(px, py)
    glEnd()
    end2D()


def drawCircle2D(cx, cy, radius, segments=24):
    begin2D()
    glBegin(GL_QUADS)
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        p0x = cx + math.cos(a0) * radius
        p0y = cy + math.sin(a0) * radius
        p1x = cx + math.cos(a1) * radius
        p1y = cy + math.sin(a1) * radius
        glVertex2f(cx, cy)
        glVertex2f(p0x, p0y)
        glVertex2f(p1x, p1y)
        glVertex2f(cx, cy)
    glEnd()
    end2D()


def drawBar2D(x, y, w, h, fraction, fg, bg=(0.05, 0.12, 0.18)):
    glColor3f(*bg)
    drawQuad2D(x, y, w, h)
    glColor3f(*fg)
    drawQuad2D(x, y, w * max(0, min(1, fraction)), h)
    t = 1.5
    glColor3f(0.0, 0.8, 1.0)
    drawQuad2D(x, y, w, t)
    drawQuad2D(x, y + h - t, w, t)
    drawQuad2D(x, y, t, h)
    drawQuad2D(x + w - t, y, t, h)


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], 0, 0, 0, 0, 0, 1)


def drawGrid():
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, TILE_SIZE):
        for y in range(-GRID_LENGTH, GRID_LENGTH, TILE_SIZE):
            col = x // TILE_SIZE
            row = y // TILE_SIZE
            if (col + row) % 2 == 0:
                glColor3f(0.04, 0.07, 0.12)
            else:
                glColor3f(0.07, 0.12, 0.18)
            glVertex3f(x, y, 0)
            glVertex3f(x + TILE_SIZE, y, 0)
            glVertex3f(x + TILE_SIZE, y + TILE_SIZE, 0)
            glVertex3f(x, y + TILE_SIZE, 0)
    glEnd()

    lw = 1.0
    glColor3f(0.0, 0.35, 0.45)
    glBegin(GL_QUADS)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, TILE_SIZE):
        glVertex3f(i, -GRID_LENGTH, 1)
        glVertex3f(i + lw, -GRID_LENGTH, 1)
        glVertex3f(i + lw, GRID_LENGTH, 1)
        glVertex3f(i, GRID_LENGTH, 1)
        glVertex3f(-GRID_LENGTH, i, 1)
        glVertex3f(GRID_LENGTH, i, 1)
        glVertex3f(GRID_LENGTH, i + lw, 1)
        glVertex3f(-GRID_LENGTH, i + lw, 1)
    glEnd()

    for cube in obstacle_cubes:
        if cube["glow_countdown"] > 0 and not cube["rising"]:
            alpha = 1.0 - (cube["glow_countdown"] / cube["glow_max"])
            glColor3f(alpha * 0.9, alpha * 0.5, 0.0)
            cx, cy = cube["x"], cube["y"]
            sz = cube_size + 5
            glBegin(GL_QUADS)
            glVertex3f(cx - sz, cy - sz, 1)
            glVertex3f(cx + sz, cy - sz, 1)
            glVertex3f(cx + sz, cy + sz, 1)
            glVertex3f(cx - sz, cy + sz, 1)
            glEnd()


def drawFood():
    name, (r, g, b) = SERPENTS[serpent_index]
    
    if mutation == "oracle":
        glColor3f(0.9, 0.9, 0.1)
        for px, py in forked_previews:
            glPushMatrix()
            glTranslatef(px, py, FOOD_SIZE + 5)
            gluSphere(gluNewQuadric(), 5, 8, 8)
            glPopMatrix()
    
    for food in food_list:
        food[3] += food[4]
        if food[3] > 1.4 or food[3] < 0.6:
            food[4] *= -1
        glPushMatrix()
        glTranslatef(food[0], food[1], FOOD_SIZE + 5)
        glScalef(food[3], food[3], food[3])
        glColor3f(r, g, b)
        
        if food[2] == "sphere":
            gluSphere(gluNewQuadric(), FOOD_SIZE, 16, 16)
        elif food[2] == "cube":
            glutSolidCube(FOOD_SIZE * 2)
        elif food[2] == "cylinder":
            glRotatef(90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), FOOD_SIZE, FOOD_SIZE, FOOD_SIZE * 2, 16, 4)
        glPopMatrix()


def drawSnakeHead():
    name, (r, g, b) = SERPENTS[serpent_index]
    bob_z = 35 + 8 * math.sin(bob_time)
    
    glPushMatrix()
    glTranslatef(snake_pos[0], snake_pos[1], bob_z)
    glRotatef(snake_angle, 0, 0, 1)
    glColor3f(r, g, b)
    gluSphere(gluNewQuadric(), 25, 32, 32)
    glColor3f(r * 0.45, g * 0.45, b * 0.45)
    gluDisk(gluNewQuadric(), 23.5, 25.5, 32, 1)
    
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 11, 22, 10)
        glColor3f(0.0, 0.9, 1.0)
        gluSphere(gluNewQuadric(), 6, 16, 16)
        glTranslatef(0, 3, 0)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(gluNewQuadric(), 3.5, 12, 12)
        glTranslatef(0.8, 1, 0.8)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(gluNewQuadric(), 1.0, 8, 8)
        glPopMatrix()
    glPopMatrix()


def trailPos(target_dist):
    if not pos_history:
        return None
    accumulated = 0.0
    prev = [snake_pos[0], snake_pos[1], 35 + 8 * math.sin(bob_time)]
    for pt in reversed(pos_history):
        dx = pt[0] - prev[0]
        dy = pt[1] - prev[1]
        seg_len = math.sqrt(dx * dx + dy * dy)
        if accumulated + seg_len >= target_dist:
            remaining = target_dist - accumulated
            if seg_len < 1e-6:
                return [prev[0], prev[1], prev[2]]
            t = remaining / seg_len
            return [prev[0] + dx * t, prev[1] + dy * t, prev[2] + (pt[2] - prev[2]) * t]
        accumulated += seg_len
        prev = pt
    return None


def drawSnakeBody():
    name, (r, g, b) = SERPENTS[serpent_index]
    
    for i, seg in enumerate(snake_body):
        pos = trailPos((i + 1) * SEGMENT_SPACING)
        if pos is None:
            break
        hx, hy, hz = pos
        scale = max(0.40, 1.0 - i * 0.04)
        
        if i % 2 == 0:
            cr, cg, cb = r * 0.68, g * 0.68, b * 0.68
        else:
            cr, cg, cb = r * 0.45, g * 0.45, b * 0.45
        
        glPushMatrix()
        glTranslatef(hx, hy, hz)
        glScalef(scale, scale, scale)
        glColor3f(cr, cg, cb)
        
        if seg["shape"] == "sphere":
            gluSphere(gluNewQuadric(), FOOD_SIZE, 16, 16)
        elif seg["shape"] == "cube":
            glutSolidCube(FOOD_SIZE * 2)
        elif seg["shape"] == "cylinder":
            glRotatef(90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), FOOD_SIZE, FOOD_SIZE, FOOD_SIZE * 2, 16, 4)
        
        if seg["shape"] == "sphere" and i % 2 == 0:
            glColor3f(r * 0.30, g * 0.30, b * 0.30)
            gluDisk(gluNewQuadric(), FOOD_SIZE * 0.92, FOOD_SIZE * 1.02, 20, 1)
        glPopMatrix()


def drawEnemy():
    if not enemy_active:
        return
    glPushMatrix()
    glTranslatef(enemy_pos[0], enemy_pos[1], 35)
    glRotatef(enemy_angle, 0, 0, 1)
    glColor3f(0.8, 0.0, 0.0)
    gluSphere(gluNewQuadric(), 20, 24, 24)
    glColor3f(0.0, 0.0, 0.0)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 8, 18, 8)
        gluSphere(gluNewQuadric(), 4, 8, 8)
        glPopMatrix()
    glPopMatrix()


def drawEnemy2():
    if not enemy2_active:
        return
    glPushMatrix()
    glTranslatef(enemy2_pos[0], enemy2_pos[1], 35)
    glRotatef(enemy2_angle, 0, 0, 1)
    glColor3f(1.0, 0.45, 0.0)
    gluSphere(gluNewQuadric(), 20, 24, 24)
    glColor3f(0.0, 0.0, 0.0)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 8, 18, 8)
        gluSphere(gluNewQuadric(), 4, 8, 8)
        glPopMatrix()
    glPopMatrix()


def drawObstacleCubes():
    for cube in obstacle_cubes:
        if not cube["active"] or cube["height"] <= 0:
            continue
        glPushMatrix()
        glTranslatef(cube["x"], cube["y"], cube["height"] / 2.0)
        glScalef(1.0, 1.0, cube["height"] / (cube_size * 2))
        glColor3f(0.20, 0.55, 0.65)
        glutSolidCube(cube_size * 2)
        glPopMatrix()
        glColor3f(0.0, 1.0, 1.0)
        cx, cy, ch = cube["x"], cube["y"], cube["height"]
        sz = cube_size
        t = 2.0
        z = ch + 0.5
        glBegin(GL_QUADS)
        glVertex3f(cx - sz, cy - sz, z)
        glVertex3f(cx + sz, cy - sz, z)
        glVertex3f(cx + sz, cy - sz + t, z)
        glVertex3f(cx - sz, cy - sz + t, z)
        glVertex3f(cx - sz, cy + sz - t, z)
        glVertex3f(cx + sz, cy + sz - t, z)
        glVertex3f(cx + sz, cy + sz, z)
        glVertex3f(cx - sz, cy + sz, z)
        glVertex3f(cx - sz, cy - sz, z)
        glVertex3f(cx - sz + t, cy - sz, z)
        glVertex3f(cx - sz + t, cy + sz, z)
        glVertex3f(cx - sz, cy + sz, z)
        glVertex3f(cx + sz - t, cy - sz, z)
        glVertex3f(cx + sz, cy - sz, z)
        glVertex3f(cx + sz, cy + sz, z)
        glVertex3f(cx + sz - t, cy + sz, z)
        glEnd()


def drawSpeedPotions():
    for p in speed_potions:
        glPushMatrix()
        glTranslatef(p[0], p[1], 25)
        pulse = 0.8 + 0.2 * math.sin(bob_time * 4)
        glScalef(pulse, pulse, pulse)
        glColor3f(1.0, 1.0, 0.0)
        gluSphere(gluNewQuadric(), 10, 16, 16)
        glPopMatrix()


def drawMagnetPotions():
    for p in magnet_potions:
        glPushMatrix()
        glTranslatef(p[0], p[1], 25)
        pulse = 0.8 + 0.2 * math.sin(bob_time * 5)
        glScalef(pulse, pulse, pulse)
        glColor3f(1.0, 0.3, 0.7)
        gluSphere(gluNewQuadric(), 10, 16, 16)
        glPopMatrix()
    
    if magnet_active:
        glColor3f(0.8, 0.1, 0.5)
        glDisable(GL_DEPTH_TEST)
        glPushMatrix()
        glTranslatef(snake_pos[0], snake_pos[1], 2)
        gluDisk(gluNewQuadric(), magnet_radius - 2, magnet_radius + 2, 48, 1)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)


def drawMysteryOrbs():
    for orb in mystery_orbs:
        glPushMatrix()
        glTranslatef(orb[0], orb[1], 20)
        glColor3f(0.55, 0.55, 0.55)
        gluSphere(gluNewQuadric(), 10, 16, 16)
        glPopMatrix()


def drawMimicFood():
    name, (r, g, b) = SERPENTS[serpent_index]
    for m in mimic_list:
        jitter = math.sin(bob_time * 8 + m[3]) * 3
        glPushMatrix()
        glTranslatef(m[0] + jitter, m[1] + jitter, FOOD_SIZE + 5)
        glColor3f(r * 0.8, g * 0.8, b * 0.8)
        
        if m[2] == "sphere":
            gluSphere(gluNewQuadric(), FOOD_SIZE, 16, 16)
        elif m[2] == "cube":
            glutSolidCube(FOOD_SIZE * 2)
        elif m[2] == "cylinder":
            glRotatef(90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), FOOD_SIZE, FOOD_SIZE, FOOD_SIZE * 2, 16, 4)
        glPopMatrix()


def drawRotZones():
    if current_level < 2:
        return
    glDisable(GL_DEPTH_TEST)
    for zone in rot_zones:
        zx, zy, zr = zone
        glColor3f(0.55, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(zx - zr, zy - zr, 2)
        glVertex3f(zx + zr, zy - zr, 2)
        glVertex3f(zx + zr, zy + zr, 2)
        glVertex3f(zx - zr, zy + zr, 2)
        glEnd()
    glEnable(GL_DEPTH_TEST)


def drawComboBanner():
    if time.time() < combo_flash:
        glColor3f(1.0, 0.8, 0.0)
        banner = f"COMBO x{combo_count}!"
        bx = (WINDOW_W - len(banner) * 16) / 2
        drawText(bx, WINDOW_H // 2 + 50, banner, font=GLUT_BITMAP_TIMES_ROMAN_24)


def drawDisplay():
    drawBar2D(30, WINDOW_H - 50, 200, 20, health / 100.0, (0.0, 0.9, 0.4))
    glColor3f(0.0, 1.0, 0.6)
    drawText(240, WINDOW_H - 50, "HEALTH")

    drawBar2D(30, WINDOW_H - 80, 200, 20, stamina / 100.0, (0.0, 0.5, 1.0))
    glColor3f(0.0, 0.7, 1.0)
    drawText(240, WINDOW_H - 80, "STAMINA [SPACE=knockback]")

    glColor3f(0.0, 1.0, 1.0)
    drawText(30, WINDOW_H - 110, f"SCORE: {score}  LEVEL: {current_level}/3",
              font=GLUT_BITMAP_HELVETICA_18)
    glColor3f(1.0, 0.35, 0.35)
    drawText(30, WINDOW_H - 140, f"LIVES: {lives}  SHEDS LEFT: {2 - shed_count}")

    if multiplier > 1:
        glColor3f(1.0, 0.85, 0.0)
        drawText(30, WINDOW_H - 170, f"x{multiplier} MULTIPLIER!")

    if time.time() < speed_boost_end:
        glColor3f(1.0, 1.0, 0.0)
        drawText(WINDOW_W - 210, WINDOW_H - 30, "SPEED BOOST!")

    if magnet_active:
        glColor3f(1.0, 0.3, 0.7)
        remaining = max(0.0, magnet_end_time - time.time())
        drawText(WINDOW_W - 240, WINDOW_H - 80, f"MAGNET! {remaining:.1f}s")

    if current_level >= 3 and effective_boundary < GRID_LENGTH - 10:
        glColor3f(1.0, 0.2, 0.2)
        drawText(WINDOW_W - 280, WINDOW_H - 105, "WALLS CLOSING IN!")

    if mutation:
        glColor3f(0.7, 0.3, 1.0)
        drawText(WINDOW_W - 270, 30, f"MUTATION: {mutation.upper()}")

    glColor3f(0.3, 0.5, 0.6)
    drawText(10, 10, "A/D = turn  SPACE = knockback  Arrows = camera  ESC = menu")
    next_need = level_score[min(current_level + 1, 3)] if current_level < 3 else 999
    glColor3f(0.3, 0.5, 0.6)
    drawText(10, 30, f"Next level at score {next_need}")

    drawComboBanner()


def drawIntro():
    global title_y, intro_phase
    elapsed = time.time() - start_time
    if elapsed > 2.5 and intro_phase == 1:
        intro_phase = 2
    if intro_phase == 2 and title_y < 500:
        title_y += 3
    
    glColor3f(0.0, 0.04, 0.08)
    drawQuad2D(0, 0, WINDOW_W, WINDOW_H)
    
    title = "SERPENT SURFER"
    tx = (WINDOW_W - len(title) * 14) / 2
    glColor3f(0.0, 1.0, 1.0)
    drawText(tx, title_y, title, font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.3, 0.6, 0.7)
    sub = "[ CYBERNETIC SNAKE EXPERIENCE ]"
    drawText((WINDOW_W - len(sub) * 9) / 2, title_y - 35, sub)
    
    if intro_phase == 2 and title_y >= 500:
        t1 = "New Game"
        x1 = (WINDOW_W - len(t1) * 13) / 2
        glColor3f(0.0, 0.15, 0.22)
        drawQuad2D(x1 - 15, 388, len(t1) * 13 + 30, 42)
        glColor3f(1.0, 1.0, 1.0)
        drawText(x1, 403, t1, font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.3, 0.4, 0.4)
    drawText(20, 20, "ESC = quit")


def drawInstructions():
    glColor3f(0.02, 0.04, 0.08)
    drawQuad2D(0, 0, WINDOW_W, WINDOW_H)
    glColor3f(0.0, 1.0, 1.0)
    drawText(310, 750, "HOW TO PLAY", font=GLUT_BITMAP_TIMES_ROMAN_24)

    lines = [
        ("CONTROLS", 700),
        ("W/S = Forward / Backward", 670),
        ("A/D = Left / Right", 645),
        ("SPACE = Knockback nearby enemy (costs Stamina)", 620),
        ("Arrow UP / DOWN = Raise or lower camera", 595),
        ("", 575),
        ("OBJECTIVE", 555),
        ("Eat glowing food to grow your serpent and raise your score.", 530),
        ("Eat 2 same-shape foods in a row for x2 score; 3 in a row = COMBO x3!", 503),
        ("Reach score 6 for Level 2, score 12 for Level 3. Win at score 20.", 476),
        ("", 456),
        ("POWER-UPS", 436),
        ("Yellow sphere  = Speed boost for 5 s", 410),
        ("Pink sphere    = Magnet: pulls food toward you for 6 s", 385),
        ("Grey orb       = Mystery: +2 lives (50%) or -1 life (50%)", 360),
        ("", 340),
        ("HAZARDS", 320),
        ("Rising teal cubes glow amber before rising - move away!", 295),
        ("Red zone patches drain health while you stand on them.", 270),
        ("Hit a wall: body is halved (up to 2 times), then lose a life.", 245),
        ("Health drains slowly over time - keep eating to stay alive.", 220),
        ("", 200),
        ("ENEMIES", 180),
        ("Level 2: red enemy chases you. Level 3: orange enemy joins.", 155),
        ("Press SPACE near an enemy to knock it back temporarily.", 130),
        ("MUTATIONS (chosen on level-up):", 105),
        ("Oracle Trace=preview 3 food spots  Titan Shell=survive 1 cube hit  Neural Sense=longer glow", 80),
    ]
    for text, y in lines:
        if text.isupper() or text == "":
            glColor3f(0.0, 1.0, 1.0)
        else:
            glColor3f(0.75, 0.85, 0.90)
        drawText(60, y, text)

    glColor3f(1, 1, 1)
    drawText(390, 40, "START SURFING!", font=GLUT_BITMAP_TIMES_ROMAN_24)


def drawChooseSerpent():
    name, (r, g, b) = SERPENTS[serpent_index]
    glColor3f(r * 0.08, g * 0.08, b * 0.08)
    drawQuad2D(0, 0, WINDOW_W, WINDOW_H)
    
    glColor3f(0.0, 1.0, 1.0)
    drawText((WINDOW_W - len("CHOOSE YOUR SERPENT") * 14) / 2, 680,
              "CHOOSE YOUR SERPENT", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(r, g, b)
    drawText((WINDOW_W - len(name) * 14) / 2, 580, name, font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    drawPreviewHead3D(r, g, b)
    drawArrowLeft()
    drawArrowRight()
    drawDotIndicators()
    
    glColor3f(1.0, 1.0, 1.0)
    drawText((WINDOW_W - len("[ Select ]") * 13) / 2, 212,
              "[ Select ]", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.3, 0.3, 0.3)
    drawText(20, 20, "ESC = back")


def drawPreviewHead3D(r, g, b):
    glViewport(350, 320, 300, 300)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluPerspective(45, 1.0, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    gluLookAt(0, 0, 4, 0, 0, 0, 0, 1, 0)
    glEnable(GL_DEPTH_TEST)
    
    glRotatef(serpent_rotation, 0, 1, 0)
    glColor3f(r, g, b)
    gluSphere(gluNewQuadric(), 1.0, 48, 48)
    glColor3f(r * 0.45, g * 0.45, b * 0.45)
    gluDisk(gluNewQuadric(), 0.98, 1.01, 48, 1)
    
    for side in (-1, 1):
        ex = side * 0.45
        ey = 0.40
        ez = math.sqrt(max(0, 1.0 - ex ** 2 - ey ** 2)) * 0.95
        glPushMatrix()
        glTranslatef(ex, ey, ez)
        glColor3f(0.0, 0.9, 1.0)
        gluSphere(gluNewQuadric(), 0.18, 24, 24)
        glTranslatef(0, 0, 0.13)
        glColor3f(0, 0, 0)
        gluSphere(gluNewQuadric(), 0.09, 16, 16)
        glPopMatrix()
    
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def drawArrowLeft():
    cx, cy = 220, 400
    glColor3f(0.0, 0.8, 1.0)
    drawTriangle2D([(cx - 30, cy), (cx + 25, cy + 28), (cx + 25, cy - 28)])


def drawArrowRight():
    cx, cy = 780, 400
    glColor3f(0.0, 0.8, 1.0)
    drawTriangle2D([(cx + 30, cy), (cx - 25, cy + 28), (cx - 25, cy - 28)])


def drawDotIndicators():
    n = len(SERPENTS)
    spacing = 24
    sx = WINDOW_W / 2 - (n - 1) * spacing / 2
    for i in range(n):
        x = sx + i * spacing
        if i == serpent_index:
            glColor3f(0.0, 1.0, 1.0)
            drawCircle2D(x, 285, 7)
        else:
            glColor3f(0.2, 0.3, 0.4)
            drawCircle2D(x, 285, 4)


def drawLevelupMutation():
    glColor3f(0.02, 0.01, 0.06)
    drawQuad2D(0, 0, WINDOW_W, WINDOW_H)
    
    glColor3f(0.0, 1.0, 1.0)
    drawText(250, 700, f"LEVEL {current_level} REACHED!", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.8, 0.8, 0.9)
    drawText(280, 650, "Choose your MUTATION:", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    for i, (name, desc) in enumerate(MUTATIONS):
        y = 560 - i * 90
        if i == mutation_index:
            glColor3f(0.0, 0.2, 0.3)
            drawQuad2D(100, y - 10, 800, 70)
            glColor3f(0.0, 1.0, 1.0)
        else:
            glColor3f(0.3, 0.4, 0.4)
        drawText(120, y + 35, f" {name}", font=GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(0.5, 0.6, 0.6)
        drawText(120, y + 10, f" {desc}")
    
    glColor3f(0.3, 0.4, 0.4)
    drawText(280, 120, "UP/DOWN to choose  ENTER to confirm")


def drawGameOver():
    glColor3f(0.0, 0.0, 0.0)
    drawQuad2D(150, 250, 700, 300)
    
    if game_won:
        glColor3f(0.0, 1.0, 0.5)
        drawText(260, 480, "YOU WON! CONGRATULATIONS!", font=GLUT_BITMAP_TIMES_ROMAN_24)
    else:
        glColor3f(1.0, 0.1, 0.1)
        drawText(330, 480, "GAME OVER", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.8, 0.9, 0.9)
    drawText(320, 420, f"Final Score: {score}", font=GLUT_BITMAP_TIMES_ROMAN_24)
    drawText(310, 370, f"Level Reached: {current_level}", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(0.3, 0.4, 0.5)
    drawText(310, 300, "Press R to restart | ESC for menu")


def drawGame():
    setupCamera()
    drawGrid()
    drawRotZones()
    drawObstacleCubes()
    drawFood()
    drawMimicFood()
    drawSpeedPotions()
    drawMagnetPotions()
    drawMysteryOrbs()
    drawEnemy()
    drawEnemy2()
    drawSnakeHead()
    drawSnakeBody()
    drawDisplay()
    if game_over or game_won:
        drawGameOver()


def spawnFood():
    margin = 50
    for _ in range(200):
        x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        ok = all((x - f[0]) ** 2 + (y - f[1]) ** 2 > 3600 for f in food_list)
        if ok:
            shape = food_shapes[len(food_list) % 3]
            food_list.append([x, y, shape, 1.0, 0.01])
            if mutation == "oracle":
                forked_previews.append([x, y])
                while len(forked_previews) > 3:
                    forked_previews.pop(0)
            break


def initFood():
    food_list.clear()
    for _ in range(3):
        spawnFood()


def spawnSpeedPotion():
    margin = 50
    x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    speed_potions.append([x, y])


def spawnMysteryOrb():
    margin = 50
    x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    kind = "powerup" if random.random() < 0.5 else "trap"
    mystery_orbs.append([x, y, kind])


def spawnMagnetPotion():
    margin = 50
    x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    magnet_potions.append([x, y])


def spawnObstacleCube():
    max_cubes = current_level * 2 + 1
    if len([c for c in obstacle_cubes if c["active"]]) >= max_cubes:
        return
    margin_tiles = 2
    min_col = -GRID_LENGTH // TILE_SIZE + margin_tiles
    max_col = GRID_LENGTH // TILE_SIZE - margin_tiles
    col = random.randint(min_col, max_col)
    row = random.randint(min_col, max_col)
    x = col * TILE_SIZE + TILE_SIZE // 2
    y = row * TILE_SIZE + TILE_SIZE // 2
    dx = x - snake_pos[0]
    dy = y - snake_pos[1]
    if dx * dx + dy * dy < 3600:
        return
    glow_max = 120 if mutation == "neural" else 60
    obstacle_cubes.append({
        "x": x, "y": y,
        "height": 0.0, "max_h": cube_size * 2.5,
        "rising": False,
        "glow_countdown": glow_max, "glow_max": glow_max,
        "active": True,
    })


def spawnMimic():
    margin = 50
    x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
    shape = random.choice(food_shapes)
    mimic_list.append([x, y, shape, random.uniform(0, 100)])


def spawnRotZones():
    rot_zones.clear()
    count = 2 + (current_level - 2)
    margin = 80
    for _ in range(count):
        x = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        y = random.randint(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        rot_zones.append([x, y, random.randint(50, 100)])


def resetGame():
    global score, lives, shed_count, current_level
    global snake_pos, snake_angle, bob_time, snake_body, pos_history
    global food_list, health, stamina, speed_potions
    global mystery_orbs, obstacle_cubes, mimic_list
    global enemy_pos, enemy_active, enemy2_pos, enemy2_active, enemy2_angle
    global rot_zones, rot_timer
    global speed_boost_end
    global last_food, multiplier, game_over, game_won
    global mutation, mutation_choice_pending, hardened_used, forked_previews
    global combo_count, combo_flash
    global magnet_potions, magnet_active, magnet_end_time
    global effective_boundary
    global enemy_knocked, enemy_knockback_target
    global enemy2_knocked, enemy2_knockback_target, knockback_cooldown

    score = 0
    lives = 3
    shed_count = 0
    current_level = 1
    snake_pos[0] = 0.0
    snake_pos[1] = 0.0
    snake_angle = 0.0
    bob_time = 0.0
    snake_body.clear()
    pos_history.clear()
    food_list.clear()
    speed_potions.clear()
    mystery_orbs.clear()
    obstacle_cubes.clear()
    mimic_list.clear()
    rot_zones.clear()
    rot_timer = 0.0
    health = 100.0
    stamina = 100.0
    speed_boost_end = 0.0
    last_food = None
    multiplier = 1
    game_over = False
    game_won = False
    enemy_active = False
    enemy_pos[0] = 200.0
    enemy_pos[1] = 200.0
    enemy2_active = False
    enemy2_pos[0] = -200.0
    enemy2_pos[1] = -200.0
    enemy2_angle = 0.0
    mutation = None
    mutation_choice_pending = False
    hardened_used = False
    forked_previews.clear()
    combo_count = 0
    combo_flash = 0.0
    magnet_potions.clear()
    magnet_active = False
    magnet_end_time = 0.0
    effective_boundary = float(GRID_LENGTH)
    enemy_knocked = False
    enemy_knockback_target = [0.0, 0.0]
    enemy2_knocked = False
    enemy2_knockback_target = [0.0, 0.0]
    knockback_cooldown = 0.0
    initFood()


def advanceLevel():
    global current_level, mutation_choice_pending, game_won
    global enemy_active, enemy2_active, mutation_index
    
    if current_level >= 3:
        game_won = True
        return
    
    current_level += 1
    mutation_choice_pending = True
    mutation_index = 0
    
    if current_level >= 2:
        enemy_active = True
        spawnRotZones()
    
    if current_level >= 3:
        enemy2_active = True
        enemy2_pos[0] = -200.0
        enemy2_pos[1] = -200.0
    
    obstacle_cubes.clear()


def shedBody():
    global shed_count, lives, snake_body
    
    if shed_count < 2:
        shed_count += 1
        half = len(snake_body) // 2
        snake_body = snake_body[:half]
        snake_pos[0] = 0.0
        snake_pos[1] = 0.0
    else:
        lives -= 1
        snake_body.clear()
        snake_pos[0] = 0.0
        snake_pos[1] = 0.0
        shed_count = 0


def hitsCube(nx, ny):
    for cube in obstacle_cubes:
        if cube["active"] and cube["height"] > 20:
            if abs(nx - cube["x"]) < cube_size + 22 and abs(ny - cube["y"]) < cube_size + 22:
                return True
    return False


def recordPos():
    pos_history.append([snake_pos[0], snake_pos[1], 35 + 8 * math.sin(bob_time)])
    if len(pos_history) > 4000:
        pos_history.pop(0)


def angleToTarget(pos, tx, ty):
    dx = tx - pos[0]
    dy = ty - pos[1]
    hyp = math.sqrt(dx * dx + dy * dy)
    if hyp < 1e-6:
        return 0.0
    sin_a = -dx / hyp
    cos_a = dy / hyp
    sin_a = max(-1.0, min(1.0, sin_a))
    base = math.degrees(math.asin(sin_a))
    if cos_a < 0:
        base = 180.0 - base
    return base % 360.0


def tryKnockback():
    global stamina, knockback_cooldown
    global enemy_knocked, enemy_knockback_target
    global enemy2_knocked, enemy2_knockback_target

    if stamina < knockback_cost:
        return
    if time.time() < knockback_cooldown:
        return

    did_knock = False

    if enemy_active:
        dx = enemy_pos[0] - snake_pos[0]
        dy = enemy_pos[1] - snake_pos[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < 120 * 120 and dist_sq > 0:
            dist = math.sqrt(dist_sq)
            enemy_knockback_target[0] = snake_pos[0] + (dx / dist) * knockback_force
            enemy_knockback_target[1] = snake_pos[1] + (dy / dist) * knockback_force
            enemy_knockback_target[0] = max(-GRID_LENGTH + 40, min(GRID_LENGTH - 40, enemy_knockback_target[0]))
            enemy_knockback_target[1] = max(-GRID_LENGTH + 40, min(GRID_LENGTH - 40, enemy_knockback_target[1]))
            enemy_knocked = True
            did_knock = True

    if enemy2_active:
        dx = enemy2_pos[0] - snake_pos[0]
        dy = enemy2_pos[1] - snake_pos[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < 120 * 120 and dist_sq > 0:
            dist = math.sqrt(dist_sq)
            enemy2_knockback_target[0] = snake_pos[0] + (dx / dist) * knockback_force
            enemy2_knockback_target[1] = snake_pos[1] + (dy / dist) * knockback_force
            enemy2_knockback_target[0] = max(-GRID_LENGTH + 40, min(GRID_LENGTH - 40, enemy2_knockback_target[0]))
            enemy2_knockback_target[1] = max(-GRID_LENGTH + 40, min(GRID_LENGTH - 40, enemy2_knockback_target[1]))
            enemy2_knocked = True
            did_knock = True

    if did_knock:
        stamina -= knockback_cost
        knockback_cooldown = time.time() + 1.5


def keyboardListener(key, x, y):
    global current_screen, game_over, game_won
    global snake_angle, mutation, mutation_index, mutation_choice_pending, hardened_used

    if key == b'\x1b':
        current_screen = "intro"
        return

    if current_screen == "levelup":
        if key == b'\r' or key == b'\n':
            if mutation_index == 0:
                mutation = "oracle"
            elif mutation_index == 1:
                mutation = "titan"
                hardened_used = False
            else:
                mutation = "neural"
            mutation_choice_pending = False
            current_screen = "game"
        glutPostRedisplay()
        return

    if current_screen == "game" and not game_over and not game_won:
        if key == b'a':
            snake_angle += 5
        if key == b'd':
            snake_angle -= 5

        if key == b' ':
            tryKnockback()

    if current_screen == "game" and (game_over or game_won):
        if key == b'r':
            resetGame()
            current_screen = "game"
        glutPostRedisplay()


def specialKeyListener(key, x, y):
    global camera_pos, mutation_index
    
    if current_screen == "levelup":
        if key == GLUT_KEY_UP:
            mutation_index = (mutation_index - 1) % 3
        if key == GLUT_KEY_DOWN:
            mutation_index = (mutation_index + 1) % 3
        glutPostRedisplay()
        return
    
    if key == GLUT_KEY_UP:
        camera_pos[2] += 10
    if key == GLUT_KEY_DOWN:
        camera_pos[2] = max(50, camera_pos[2] - 10)
    if key == GLUT_KEY_LEFT:
        camera_pos[0] -= 20
    if key == GLUT_KEY_RIGHT:
        camera_pos[0] += 20
    glutPostRedisplay()


def mouseListener(button, state, mx, my):
    if state != GLUT_DOWN:
        return
    wy = glutGet(GLUT_WINDOW_HEIGHT) - my
    if current_screen == "intro":
        introClick(mx, wy)
    elif current_screen == "instructions":
        instructClick(mx, wy)
    elif current_screen == "choose_serpent":
        chooseClick(mx, wy)


def hitTest(mx, wy, bx, by, bw, bh):
    return bx <= mx <= bx + bw and by <= wy <= by + bh


def introClick(mx, wy):
    global current_screen
    if intro_phase < 2:
        return
    t1 = "New Game"
    x1 = (WINDOW_W - len(t1) * 13) / 2
    if hitTest(mx, wy, x1 - 15, 388, len(t1) * 13 + 30, 42):
        current_screen = "instructions"


def instructClick(mx, wy):
    global current_screen
    if hitTest(mx, wy, 350, 22, 300, 50):
        current_screen = "choose_serpent"


def chooseClick(mx, wy):
    global serpent_index, current_screen
    if hitTest(mx, wy, 180, 370, 80, 60):
        serpent_index = (serpent_index - 1) % len(SERPENTS)
    elif hitTest(mx, wy, 740, 370, 80, 60):
        serpent_index = (serpent_index + 1) % len(SERPENTS)
    elif hitTest(mx, wy, 380, 200, 240, 44):
        current_screen = "game"
        resetGame()
    glutPostRedisplay()


def moveEnemy(pos, angle_ref, turn_cap, extra_speed, knocked, kb_target):
    if knocked:
        dx = kb_target[0] - pos[0]
        dy = kb_target[1] - pos[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < knockback_speed * knockback_speed * 4:
            return angle_ref, False
        dist = math.sqrt(dist_sq)
        step = min(knockback_speed * 6, dist)
        pos[0] += (dx / dist) * step
        pos[1] += (dy / dist) * step
        return angle_ref, True

    target_angle = angleToTarget(pos, snake_pos[0], snake_pos[1])
    angle_diff = (target_angle - angle_ref + 180) % 360 - 180
    new_angle = angle_ref + max(-turn_cap, min(turn_cap, angle_diff))
    speed = 0.01 + current_level * 0.1 + extra_speed
    nx = pos[0] - speed * math.sin(math.radians(new_angle))
    ny = pos[1] + speed * math.cos(math.radians(new_angle))
    
    if hitsCube(nx, ny):
        for turn in (45, -45, 90, -90, 135, -135, 180):
            alt = new_angle + turn
            ax = pos[0] - speed * math.sin(math.radians(alt))
            ay = pos[1] + speed * math.cos(math.radians(alt))
            if not hitsCube(ax, ay):
                new_angle = alt
                nx, ny = ax, ay
                break
        else:
            nx, ny = pos[0], pos[1]
    
    pos[0] = max(-GRID_LENGTH + 30, min(GRID_LENGTH - 30, nx))
    pos[1] = max(-GRID_LENGTH + 30, min(GRID_LENGTH - 30, ny))
    return new_angle, False


def idle():
    global serpent_rotation, bob_time, current_screen, mutation_choice_pending
    global score, health, stamina, game_over, game_won
    global speed_boost_end
    global last_food, multiplier, lives
    global enemy_pos, enemy_angle, enemy2_pos, enemy2_angle, enemy2_active
    global cube_spawn_timer, potion_spawn_timer, orb_spawn_timer
    global rot_timer, current_level, mutation
    global combo_count, combo_flash
    global magnet_active, magnet_end_time
    global effective_boundary
    global enemy_knocked, enemy_knockback_target
    global enemy2_knocked, enemy2_knockback_target
    global hardened_used

    if current_screen == "choose_serpent":
        serpent_rotation = (serpent_rotation + 1) % 360
    
    if current_screen in ("levelup", "intro", "instructions", "choose_serpent"):
        glutPostRedisplay()
        return
    
    if game_over or game_won:
        glutPostRedisplay()
        return

    bob_time += 0.04

    # ========
    if not game_over and not game_won and current_screen == "game":
        slowdown = 0.9 if mutation == "titan" else 1.0
        cur_speed = (boost_speed if time.time() < speed_boost_end else normal_speed) * slowdown

        nx = snake_pos[0] - cur_speed * math.sin(math.radians(snake_angle))
        ny = snake_pos[1] + cur_speed * math.cos(math.radians(snake_angle))

        if abs(nx) >= effective_boundary - 20 or abs(ny) >= effective_boundary - 20:
            shedBody()
        elif hitsCube(nx, ny):
            # cube blocked: don't move this frame (player must steer around it)
            pass
        else:
            recordPos()
            snake_pos[0] = nx
            snake_pos[1] = ny

    # ========

    health = max(0, health - health_drain)
    if health <= 0:
        lives -= 1
        health = 100.0
        snake_body.clear()

    stamina = min(100.0, stamina + 0.2)

    if magnet_active:
        for food in food_list:
            dx = snake_pos[0] - food[0]
            dy = snake_pos[1] - food[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < magnet_radius:
                food[0] += (dx / dist) * magnet_pull
                food[1] += (dy / dist) * magnet_pull
        if time.time() > magnet_end_time:
            magnet_active = False

    for food in food_list[:]:
        dx = snake_pos[0] - food[0]
        dy = snake_pos[1] - food[1]
        if dx * dx + dy * dy < 38 * 38:
            if food[2] == last_food:
                combo_count += 1
            else:
                combo_count = 1
            last_food = food[2]
            if combo_count >= 3:
                multiplier = 3
                combo_flash = time.time() + combo_duration
            elif combo_count == 2:
                multiplier = 2
            else:
                multiplier = 1
            score += 1 * multiplier
            health = min(100.0, health + 20)
            snake_body.insert(0, {"shape": food[2]})
            food_list.remove(food)
            spawnFood()

    for m in mimic_list[:]:
        dx = snake_pos[0] - m[0]
        dy = snake_pos[1] - m[1]
        if dx * dx + dy * dy < 38 * 38:
            mimic_list.remove(m)
            health = max(0, health - 30)

    for p in speed_potions[:]:
        dx = snake_pos[0] - p[0]
        dy = snake_pos[1] - p[1]
        if dx * dx + dy * dy < 30 * 30:
            speed_potions.remove(p)
            speed_boost_end = time.time() + 5.0

    for p in magnet_potions[:]:
        dx = snake_pos[0] - p[0]
        dy = snake_pos[1] - p[1]
        if dx * dx + dy * dy < 30 * 30:
            magnet_potions.remove(p)
            magnet_active = True
            magnet_end_time = time.time() + 6.0

    for orb in mystery_orbs[:]:
        dx = snake_pos[0] - orb[0]
        dy = snake_pos[1] - orb[1]
        if dx * dx + dy * dy < 30 * 30:
            mystery_orbs.remove(orb)
            if orb[2] == "powerup":
                lives = min(lives + 2, 9)
            else:
                lives -= 1

    for cube in obstacle_cubes:
        if not cube["active"]:
            continue
        if cube["glow_countdown"] > 0 and not cube["rising"]:
            cube["glow_countdown"] -= 1
            if cube["glow_countdown"] <= 0:
                cube["rising"] = True
        if cube["rising"]:
            cube["height"] = min(cube["max_h"], cube["height"] + 3)
            if cube["height"] > 20:
                if (abs(snake_pos[0] - cube["x"]) < cube_size + 20 and
                        abs(snake_pos[1] - cube["y"]) < cube_size + 20):
                    if mutation == "titan" and not hardened_used:
                        hardened_used = True
                    else:
                        shedBody()

    cube_spawn_timer += 1
    spawn_rate = max(60, 180 - current_level * 30)
    if cube_spawn_timer >= spawn_rate:
        cube_spawn_timer = 0
        spawnObstacleCube()

    potion_spawn_timer += 1
    if potion_spawn_timer >= 300 and len(speed_potions) < 2:
        potion_spawn_timer = 0
        spawnSpeedPotion()

    if random.random() < 0.0008 and len(magnet_potions) < 1:
        spawnMagnetPotion()

    orb_spawn_timer += 1
    if orb_spawn_timer >= 400 and len(mystery_orbs) < 3:
        orb_spawn_timer = 0
        spawnMysteryOrb()

    if current_level >= 2 and random.random() < 0.002 and len(mimic_list) < 1:
        spawnMimic()

    if enemy_active:
        enemy_angle, enemy_knocked = moveEnemy(
            enemy_pos, enemy_angle, 3, 0.0, enemy_knocked, enemy_knockback_target)
        dx = snake_pos[0] - enemy_pos[0]
        dy = snake_pos[1] - enemy_pos[1]
        if dx * dx + dy * dy < 40 * 40:
            shedBody()

    if enemy2_active:
        enemy2_angle, enemy2_knocked = moveEnemy(
            enemy2_pos, enemy2_angle, 5, 0.1, enemy2_knocked, enemy2_knockback_target)
        dx = snake_pos[0] - enemy2_pos[0]
        dy = snake_pos[1] - enemy2_pos[1]
        if dx * dx + dy * dy < 40 * 40:
            shedBody()

    for zone in rot_zones:
        dx = snake_pos[0] - zone[0]
        dy = snake_pos[1] - zone[1]
        if dx * dx + dy * dy < zone[2] * zone[2]:
            health = max(0, health - rot_damage * 10)
            break

    if current_level >= 3:
        effective_boundary = max(min_boundary, effective_boundary - shrink_rate)

    level_thresholds = {1: 6, 2: 12, 3: 20}
    if current_level < 3 and score >= level_thresholds[current_level]:
        advanceLevel()
        current_screen = "levelup"
    
    if current_level == 3 and score >= 20:
        game_won = True

    if lives <= 0:
        game_over = True

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    
    if current_screen == "intro":
        drawIntro()
    elif current_screen == "instructions":
        drawInstructions()
    elif current_screen == "choose_serpent":
        drawChooseSerpent()
    elif current_screen == "levelup":
        drawLevelupMutation()
    elif current_screen == "game":
        drawGame()
    
    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Serpent Surfer")
    glClearColor(0.02, 0.03, 0.06, 1.0)
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()