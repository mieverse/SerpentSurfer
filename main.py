# IMPORTS

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18

import time
import math


# GLOBAL VARIABLES

startTime = time.time() 
center = 400
phase = 1

fovY = 120
camera_pos = (0, 0, 0)

# TEXT FUNCTION

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Screen-space projection
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


# KEYBOARD, MOUSE, SPECIAL KEYS INPUT 

def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    pass
    # if key == b'w':
    # if key == b's':
    # if key == b'a':
    # if key == b'd':
    # if key == b'c':
    # if key == b'v':
    # if key == b'r':


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    pass
    # global camera_pos
    # x, y, z = camera_pos

    # if key == GLUT_KEY_UP:
    # if key == GLUT_KEY_DOWN:
    # if key == GLUT_KEY_LEFT:
    #     x -= 1
    # if key == GLUT_KEY_RIGHT:
    #     x += 1

    # camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs for firing bullets and toggling camera mode.
    """
    pass
    # if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
    # if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:


# CAMERA

def setupCamera():
    """
    Configures the camera projection and view.
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluPerspective(fovY, 1.25, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos

    gluLookAt(
        x, y, z,
        0, 0, 0,
        0, 0, 1
    )


# INTRO SCREEN

def draw_intro():
    global center, phase, startTime

    elapsed = time.time() - startTime

    if elapsed > 2.5 and phase == 1:
        phase = 2

    if phase == 2 and center < 500:
        center += 3

    title = "SERPENT SURFER"
    pos1 = (1000 - (len(title) * 14)) / 2 

    glColor3f(0.91, 0.33, 0.50)
    draw_text(pos1, center, title, font=GLUT_BITMAP_TIMES_ROMAN_24)

    if phase == 2 and center >= 500:
        glColor3f(1.0, 1.0, 1.0)
        
        t1 = "New Game"
        t2 = "Choose Serpent"

        x1 = (1000 - (len(t1) * 13)) / 2
        draw_text(x1, 400, t1, font=GLUT_BITMAP_TIMES_ROMAN_24)

        x2 = (1000 - (len(t2) * 13)) / 2
        draw_text(x2, 340, t2, font=GLUT_BITMAP_TIMES_ROMAN_24)


# RENDER

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glViewport(0, 0, 1000, 800)

    draw_intro()

    glutSwapBuffers()


def idle():
    glutPostRedisplay()



# MAIN

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)

    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)

    glutCreateWindow(b"Serpent Surfer")

    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()