import os, sys
import heapq
from random import randint, choice, random
from copy import copy
from math import sin, cos, radians
import numpy as np
import scipy.ndimage as ndi
import cPickle

import pygame
from pygame.sprite import Sprite

from vec2d import vec2d


class Creep(Sprite):
    """ A creep sprite that bounces off walls and changes its
        direction from time to time.
    """
    def __init__(   
            self, screen, img_filename, init_position, 
            init_direction, speed, paths):
        """ Create a new Creep.
        
            screen: 
                The screen on which the creep lives (must be a 
                pygame Surface object, such as pygame.display)
            
            img_filaneme: 
                Image file for the creep.
            
            init_position:
                A vec2d or a pair specifying the initial position
                of the creep on the screen.
            
            init_direction:
                A vec2d or a pair specifying the initial direction
                of the creep. Must have an angle that is a 
                multiple of 45 degres.
            
            speed: 
                Creep speed, in pixels/millisecond (px/ms)
        """
        Sprite.__init__(self)
        
        self.screen = screen
        self.speed = speed
        
        self.image = pygame.image.load(img_filename).convert_alpha()
        self.image_w, self.image_h = self.image.get_size()

        
        # A vector specifying the creep's position on the screen
        #
        self.startpos = self.pos = vec2d(init_position)
        

        # The direction is a normalized vector
        #
        self.direction = vec2d(init_direction).normalized()

        self.paths = copy(paths)
        self.startpaths = copy(paths)

        draw_pos = self.image.get_rect().move(
            self.pos.x - self.image_w / 2, 
            self.pos.y - self.image_h / 2)
        self.rect = draw_pos
         
    def change_image(self, newim):
        self.image = pygame.image.load(newim).convert_alpha()
        self.image_w, self.image_h = self.image.get_size()

   
    def update(self, time_passed):
        """ Update the creep.
        
            time_passed:
                The time passed (in ms) since the previous update.
        """
        # # Make the creep point in the correct direction.
        # # Since our direction vector is in screen coordinates 
        # # (i.e. right bottom is 1, 1), and rotate() rotates 
        # # counter-clockwise, the angle must be inverted to 
        # # work correctly.
        # #
        # self.image = pygame.transform.rotate(
        #     self.base_image, -self.direction.angle)
        # 
        # # Compute and apply the displacement to the position 
        # # vector. The displacement is a vector, having the angle
        # # of self.direction (which is normalized to not affect
        # # the magnitude of the displacement)
        # #
        # displacement = vec2d(    
        #     self.direction.x * self.speed * time_passed,
        #     self.direction.y * self.speed * time_passed)

        while time_passed > 0:
            # are we at the end?
            if len(self.paths) == 0:
                self.pos = self.startpos
                self.paths = copy(self.startpaths)
                return

            # if the creep has multiple paths to choose from, choose one
            while len(self.paths[0]) > 1:
                p = choice(self.paths[0])
                if np.isfinite(p[int(self.pos.y), int(self.pos.x)]):
                    self.paths[0] = [p]
                    break
                

            path = self.paths[0][0]
            old_distance = path[int(self.pos.y), int(self.pos.x)]
            if old_distance == 0.0:
                # move to next piece of path
                self.paths = self.paths[1:]
                return

            new_distance = old_distance
            assert np.isfinite(old_distance)
            while new_distance >= old_distance:
                newpos = self.pos + (choice([-1, 0, 1]), choice([-1, 0, 1]))
                new_distance = path[int(newpos.y), int(newpos.x)]
            time_passed -= (old_distance - new_distance) / self.speed
            # print old_distance, new_distance, old_distance - new_distance, time_passed
            self.pos = newpos

    def blitme(self):
        """ Blit the creep onto the screen that was provided in
            the constructor.
        """
        # The creep image is placed at self.pos.
        # To allow for smooth movement even when the creep rotates
        # and the image size changes, its placement is always
        # centered.
        #
        draw_pos = self.image.get_rect().move(
            self.pos.x - self.image_w / 2, 
            self.pos.y - self.image_h / 2)
        self.rect = draw_pos
        self.screen.blit(self.image, draw_pos)
           
    #------------------ PRIVATE PARTS ------------------#
    
    _counter = 0
    
    def _change_direction(self, time_passed):
        """ Turn by 45 degrees in a random direction once per
            0.4 to 0.5 seconds.
        """
        self._counter += time_passed
        if self._counter > randint(200, 300):
            self.direction.rotate(22.5 * randint(-2, 2))
            while (self.direction.x < 0) and (self.direction.y < 0):
                self.direction.rotate(22.5 * randint(-2, 2))
            self._counter = 0
    

class Button(Creep):
    def __init__(self, *args, **kwargs):
        Creep.__init__(self, *args, **kwargs)
        bg = pygame.Surface(self.image.get_size())
        bg.fill((128, 128, 128))
        bg.blit(self.image, (0, 0))
        self.image = bg
        

def masked_distance(start, mask):
    dist = np.inf * np.ones(start.shape)
    mask = mask.copy()
    mask[:, 0] = 0
    mask[:, -1] = 0
    mask[0, :] = 0
    mask[-1, :]
    start = start * mask
    dist[start] = 1

    j, i = np.meshgrid(np.arange(mask.shape[1]), np.arange(mask.shape[0]))    

    heap = [(0, pi, pj) for pi, pj in zip(i[start], j[start])]
    print len(heap), "initial"
    while len(heap) > 0:
        d, pi, pj = heapq.heappop(heap)
        if d < dist[pi, pj]:
            dist[pi, pj] = d
            for di in range(-1, 2):
                for dj in range(-1, 2):
                    newd = dist[pi, pj] + np.sqrt(0.0 + di * di + dj * dj)
                    if mask[pi + di, pj + dj] and (newd < dist[pi + di, pj + dj]):
                        heapq.heappush(heap, (newd, pi + di, pj + dj))

    return dist
    

def create_paths(pathimage):
    # shortest path through black then purple then cyan
    arr = np.transpose(pygame.surfarray.array3d(pathimage), [1,0,2])
    maxval = arr.max()
    black = (((arr == 0).sum(axis=2)) == 3)
    print "found %d black pixels"%(black.sum())
    purple = ((arr[:,:,0] == maxval) & (arr[:,:,1] == 0) & (arr[:,:,2] == maxval))
    print "found %d purple pixels"%(purple.sum())
    cyan = ((arr[:,:,0] == 0) & (arr[:,:,1] == maxval) & (arr[:,:,2] == maxval))
    print "found %d cyan pixels"%(cyan.sum())
    white = (((arr == arr.max()).sum(axis=2)) == 3)
    print "found %d white pixels"%(white.sum())


    mask = black | purple | cyan | white

    black_blobs, black_count = ndi.label(black)
    purple_blobs, purple_count = ndi.label(purple)
    cyan_blobs, cyan_count = ndi.label(cyan)

    print black_count, purple_count, cyan_count

    try:
        black_centers, purple_distances, cyan_distances = cPickle.load(open("distances.pickle"))
    except:
        black_centers = ndi.center_of_mass(np.ones(black_blobs.shape), black_blobs, range(1, black_count + 1))
        purple_distances = [masked_distance(purple_blobs == (b + 1), mask) for b in range(purple_count)]
        cyan_distances = [masked_distance(cyan_blobs == (b + 1), mask) for b in range(cyan_count)]
        cPickle.dump((black_centers, purple_distances, cyan_distances), open("distances.pickle", "w"))
    
    return black_centers, [purple_distances, cyan_distances]

def run_game():
    # Game parameters
    SCREEN_WIDTH, SCREEN_HEIGHT = 400, 400
    BG_COLOR = 150, 150, 80
    CREEP_FILENAMES = [
        'bonehunter2.png', 
        'skorpio.png',
        'tuma.png', 
        'skrals.png']
    TOWER_FILENAMES = [
        'matanui.png',
        'malum.png',
        'gresh.png',
        'gelu.png',
        'vastus.png',
        'kiina.png',
        ]
    N_CREEPS = 50
    N_TOWERS = 0

    pygame.init()

    background = pygame.image.load("Background_Level_1.JPG")
    path = pygame.image.load("Path_Level_1.png")
    w, h = background.get_size()
    assert (w, h) == path.get_size()
    sc = min(1024.0/w, 1024.0/h)
    background = pygame.transform.scale(background, (int(w * sc), int(h * sc)))
    path = pygame.transform.scale(path, (int(w * sc), int(h * sc)))
    backgroundRect = background.get_rect()

    starts, paths = create_paths(path)

    screen = pygame.display.set_mode(
        background.get_size(), 0, 32)
    clock = pygame.time.Clock()

    # Create N_CREEPS random creeps.
    creeps = []    
    for i in range(N_CREEPS):
        creeps.append(Creep(screen,
                            choice(CREEP_FILENAMES), 
                            (   choice(starts)[::-1]), # reversed x and y
                            (   choice([-1, 1]), 
                                choice([-1, 1])),
                            0.05,
                            paths))

    towers = [Creep(screen,
                    choice(TOWER_FILENAMES),
                    (randint(0, background.get_size()[0]), randint(0, background.get_size()[1])),
                    (1, 1),
                    0.0,
                    paths) for i in range (N_TOWERS)]

    buttons = [Button(screen,
                      towerfile,
                      (randint(0, background.get_size()[0]), randint(0, background.get_size()[1])),
                      (1, 1),
                      0.0,
                      paths) for towerfile in TOWER_FILENAMES]

    rightedge = screen.get_width() - 5
    for b in buttons:
        b.pos = vec2d(rightedge - b.image.get_width() / 2, 5 + b.image.get_height() / 2)
        rightedge -= (b.image.get_width() + 5)

    next_tower = TOWER_FILENAMES[0]

    # The main game loop
    #
    rect = pygame.Rect((1, 1), (10, 10))
    while True:
        # Limit frame speed to 50 FPS
        #
        time_passed = clock.tick(50)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    rect.center = pygame.mouse.get_pos()
                    collided = False
                    for b in buttons:
                        if b.rect.colliderect(rect):
                            collided = True
                            next_tower = TOWER_FILENAMES[buttons.index(b)]
                    if not collided:
                        towers += [Creep(screen,
                                         next_tower,
                                         pygame.mouse.get_pos(),
                                         (1, 1),
                                         0.0,
                                         paths)]

        # Redraw the background
        screen.blit(background, backgroundRect)
        
        # Update and redraw all creeps
        for creep in creeps:
            creep.update(time_passed)
            creep.blitme()

        for tower in towers + buttons:
            tower.blitme()

        pygame.display.flip()


def exit_game():
    sys.exit()


run_game()

