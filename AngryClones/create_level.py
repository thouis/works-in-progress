#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An attempt at some simple, self-contained pygame-based examples.
Example 02

In short:
One static body:
    + One fixture: big polygon to represent the ground
Two dynamic bodies:
    + One fixture: a polygon
    + One fixture: a circle
And some drawing code that extends the shape classes.

kne
"""
import pygame
from pygame.locals import *
import random as pyrand

import Box2D # The main library
from Box2D.b2 import world, polygonShape, staticBody, dynamicBody, circleShape # This maps Box2D.b2Vec2 to vec2 (and so on)

# --- constants ---
# Box2D deals with meters, but we want to display pixels, 
# so define a conversion factor:
PPM=20.0 # pixels per meter
TARGET_FPS=30
TIME_STEP=1.0/TARGET_FPS


# --- pybox2d world setup ---
# Create the world
world=world(gravity=(0,-10),doSleep=True)

# And a static body to hold the ground shape
ground_body=world.CreateStaticBody(
    position=(0,0),
    shapes=polygonShape(box=(50,1)),
    )

# Create a couple dynamic bodies
for i in range(200):
    body=world.CreateDynamicBody(position=(20 + pyrand.randrange(0,40)/10.0, pyrand.randrange(60,160)))
    circle=body.CreateCircleFixture(radius=0.5, density=1, friction=0.3)

body=world.CreateDynamicBody(position=(30,45), angle=15)
box=body.CreatePolygonFixture(box=(2,1), density=0.2, friction=0.5)

body=world.CreateDynamicBody(position=(10,45), angle=15)
box=body.CreatePolygonFixture(box=(2,1), density=0.2, friction=0.5)

colors = {
    staticBody  : (255,255,255,255),
    dynamicBody : (127,127,127,255),
}

# Let's play with extending the shape classes to draw for us.
def my_draw_polygon(polygon, body, fixture):
    vertices=[(body.transform*v)*PPM for v in polygon.vertices]
    vertices=[(v[0], SCREEN_HEIGHT-v[1]) for v in vertices]
    pygame.draw.polygon(screen, colors[body.type], vertices)
polygonShape.draw=my_draw_polygon

def my_draw_circle(circle, body, fixture):
    position=body.transform*circle.pos*PPM
    position=(position[0], SCREEN_HEIGHT-position[1])
    pygame.draw.circle(screen, colors[body.type], [int(x) for x in position], int(circle.radius*PPM))
    # Note: Python 3.x will enforce that pygame get the integers it requests,
    #       and it will not convert from float.
circleShape.draw=my_draw_circle

# --- main game loop ---

background = pygame.image.load("Level1-TNT-House.png")
w, h = background.get_size()
sc = min(1024.0/w, 1024.0/h)
background = pygame.transform.scale(background, (int(w * sc), int(h * sc)))
backgroundRect = background.get_rect()

SCREEN_WIDTH, SCREEN_HEIGHT = background.get_size()

# --- pygame setup ---
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.DOUBLEBUF, 32)
pygame.display.set_caption('Simple pygame example')
clock=pygame.time.Clock()

background = background.convert()

polys = []
polypts = []

running=True
while running:
    # Check the event queue
    for event in pygame.event.get():
        if event.type==QUIT:
            running=False
        elif (event.type==KEYDOWN and event.key==K_ESCAPE):
            if polypts:
                polypts.pop()
        elif (event.type==KEYDOWN and event.key==K_RETURN):
            if len(polypts) > 2:
                polys.append(polypts)
            polypts = []
        elif (event.type==KEYDOWN and event.key==K_b):
            if polys:
                polys.pop()
        elif (event.type == pygame.MOUSEBUTTONDOWN and
              pygame.mouse.get_pressed()[0]):
            polypts.append(pygame.mouse.get_pos())

    screen.blit(background, backgroundRect)
    
    for p in polys:
        pygame.draw.polygon(screen, pygame.Color(0, 255, 0), p)

    if len(polypts) > 1:
        pygame.draw.lines(screen, pygame.Color(0, 0, 255), 0, polypts)

    # Draw the world
    for body in world.bodies:
        for fixture in body.fixtures:
            fixture.shape.draw(body, fixture)

    # Make Box2D simulate the physics of our world for one step.
#     world.Step(TIME_STEP, 10, 10)

    # Flip the screen and try to keep at the target FPS
    pygame.display.flip()
    clock.tick(TARGET_FPS)
    
pygame.quit()
print('Done!')
print polys


polys= [[(439, 5), (439, 31), (470, 34), (471, 5)], [(441, 34), (367, 258), (389, 260), (461, 35)], [(461, 36), (477, 259), (516, 258), (488, 31)], [(456, 53), (448, 95), (440, 256), (457, 256), (465, 138)], [(316, 260), (318, 286), (559, 283), (559, 261)], [(320, 287), (317, 338), (335, 332), (334, 320), (350, 323), (364, 316), (335, 309), (335, 285)], [(422, 290), (274, 369), (288, 388), (426, 310)], [(273, 371), (272, 390), (287, 392)], [(309, 378), (290, 388), (310, 392)], [(430, 284), (428, 316), (442, 317), (443, 285)], [(421, 315), (410, 383), (443, 386), (448, 319)], [(355, 350), (355, 367), (379, 372), (380, 354)], [(343, 368), (343, 375), (393, 383), (394, 374)], [(329, 374), (324, 396), (348, 402), (356, 379)], [(267, 390), (266, 415), (349, 422), (350, 401)], [(266, 415), (227, 624), (247, 626), (287, 417)], [(295, 461), (284, 601), (307, 601), (317, 460)], [(313, 423), (295, 435), (400, 542), (415, 528)], [(520, 464), (528, 476), (510, 492), (444, 534), (420, 539), (417, 524)], [(416, 527), (424, 544), (396, 546)], [(403, 546), (390, 616), (413, 619), (419, 547)], [(388, 383), (370, 482), (469, 490), (484, 399)], [(284, 602), (270, 633), (340, 639), (310, 600)], [(390, 616), (360, 638), (430, 645), (415, 618)], [(470, 300), (445, 309), (528, 457), (547, 441)], [(545, 287), (535, 357), (498, 352), (506, 369), (533, 375), (530, 409), (548, 436), (552, 415), (562, 283)], [(546, 441), (524, 464), (635, 604), (662, 585)], [(532, 478), (526, 624), (512, 624), (508, 493)], [(513, 625), (499, 643), (538, 644), (528, 627)], [(616, 583), (529, 624), (542, 645), (627, 597)], [(588, 590), (530, 567), (527, 587), (577, 598)], [(661, 635), (572, 626), (562, 641), (653, 649), (663, 643)], [(212, 622), (119, 715), (239, 713), (242, 659), (323, 669), (315, 713), (450, 713), (455, 668), (559, 667), (552, 717), (619, 715), (571, 645)], [(95, 692), (97, 716), (118, 716), (119, 691)], [(248, 697), (248, 715), (269, 718), (271, 697)], [(272, 703), (271, 717), (287, 716), (286, 703)], [(290, 698), (287, 716), (302, 715), (303, 698)], [(467, 685), (462, 715), (491, 717), (496, 684)], [(496, 694), (494, 717), (518, 716), (518, 695)], [(518, 690), (518, 714), (542, 714), (544, 687)], [(669, 641), (595, 675), (608, 689), (674, 652)], [(638, 674), (605, 693), (622, 717), (637, 714)], [(660, 591), (636, 606), (720, 716), (741, 701)], [(742, 701), (721, 718), (743, 718)], [(544, 227), (539, 257), (649, 266), (654, 237)], [(660, 211), (651, 264), (632, 265), (642, 288), (628, 370), (660, 367), (687, 211)], [(627, 371), (609, 471), (606, 512), (632, 516), (654, 370)], [(608, 513), (632, 517), (631, 545)], [(657, 372), (896, 406), (1018, 413), (1019, 438), (900, 447), (897, 434), (652, 401)], [(893, 434), (878, 431), (839, 642), (835, 713), (866, 715), (888, 542), (1018, 530), (1019, 511), (886, 493), (894, 440)], [(698, 216), (713, 236), (684, 364), (671, 371), (723, 379), (713, 366), (742, 240), (770, 226)], [(803, 215), (829, 230), (807, 375), (793, 388), (839, 396), (831, 380), (861, 237), (889, 220)], [(607, 470), (564, 462), (576, 478), (606, 486)], [(667, 186), (662, 206), (690, 208), (802, 214), (929, 215), (929, 190), (733, 179)], [(805, 47), (731, 176), (863, 182)], [(905, 218), (876, 403), (899, 403), (915, 310), (1021, 319), (1019, 289), (919, 276), (923, 219)], [(652, 403), (640, 480), (716, 492), (735, 413)], [(736, 413), (718, 490), (796, 497), (804, 425)], [(804, 424), (798, 497), (862, 505), (875, 432)], [(640, 481), (635, 542), (698, 553), (716, 492)], [(631, 544), (677, 605), (694, 551)], [(718, 490), (698, 553), (779, 564), (796, 497)], [(795, 498), (778, 563), (850, 571), (863, 504)], [(695, 551), (677, 607), (760, 625), (774, 564)], [(774, 564), (763, 627), (839, 635), (849, 571)], [(682, 614), (706, 648), (712, 621)], [(708, 652), (738, 656), (741, 620), (713, 614)], [(739, 655), (765, 660), (772, 628), (742, 622)], [(738, 657), (732, 684), (756, 690), (766, 660)], [(773, 629), (755, 717), (833, 716), (837, 635)], [(708, 654), (730, 682), (736, 657)], [(732, 686), (746, 700), (747, 689)], [(747, 689), (745, 716), (756, 716), (758, 691)], [(888, 668), (883, 713), (934, 716), (937, 673)], [(920, 622), (888, 665), (938, 669)], [(882, 693), (868, 717), (883, 717)], [(935, 701), (934, 718), (951, 717)], [(733, 341), (724, 380), (790, 389), (790, 353)], [(732, 286), (772, 271), (739, 258)], [(792, 280), (811, 317), (821, 284)]]
