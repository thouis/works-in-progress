import os, sys
import heapq
from random import randint, choice, random
from copy import copy
from math import sin, cos, radians
import numpy as np
import scipy.ndimage as ndi
import cPickle

import pygame
import pygame.surfarray
from pygame.sprite import Sprite
import pygame.mixer as mixer
import pygame.font
import pygame.draw

from vec2d import vec2d


class Creep(Sprite):
    """ A creep sprite that bounces off walls and changes its
        direction from time to time.
    """
    def __init__(   
            self, screen, img_filename, init_position, 
            init_direction, speed, paths, explosion=None):
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
        self.explosion = explosion
        self.confused = False
        
        self.image = pygame.image.load(img_filename).convert_alpha()
        self.image_w, self.image_h = self.image.get_size()
        self.img_filename = img_filename

        self.health = 100

        
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
                if np.isfinite(new_distance) and (self.confused is not False):
                    break
            time_passed -= np.abs(old_distance - new_distance) / self.speed
            if self.confused is not False:
                self.confused -= time_passed
                if self.confused <= 0:
                    self.confused = False
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
        if self.health > 0:
            health_rectangle = pygame.Rect(self.pos.x - self.image_w / 2, self.pos.y - self.image_h / 2 - 3, self.health / 3, 3)
            pygame.draw.rect(self.screen, pygame.Color(255, 0, 0), health_rectangle, 0)
           
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
    

class Tower(Creep):
    def __init__(self, *args, **kwargs):
        self.radius = kwargs.pop('radius')
        self.firing_sounds = kwargs.pop('firing_sounds')
        self.max_attacks = kwargs.pop('max_attacks')
        Creep.__init__(self, *args, **kwargs)
        self.active_attacks = []
        self.blasting = False
        self.health = 0

    def attack(self, targets):
        for t in set(targets) - set(a.target for a in self.active_attacks) :
            if len(self.active_attacks) >= self.max_attacks:
                return
            if pygame.sprite.collide_circle(self, t):
                vis = self.visible_attack()
                self.active_attacks.append(Attack(self, t, self.special, vis))
                if vis:
                    # choice(self.firing_sounds).play()
                    pass

    def special(self, target):
        if 'gresh' in self.img_filename:
            target.confused = 500.0
            return False
        elif 'vastus' in self.img_filename:
            # teleport back to beginning
            target.paths = []
            return False
        elif 'ackar' in self.img_filename:
            # fire blast
            self.blasting = [100, target]
        else:
            print "default"
            return True

    def visible_attack(self):
        return not 'ackar' in self.img_filename

    def update(self, time_passed):
        winnings = 0
        if self.blasting:
            self.blasting[0] -= time_passed
            if self.blasting[0] <= 0:
                self.blasting[1].health -= 10
                if self.blasting[1].health <= 0:
                    winnings = 5
                    self.blasting[1].paths = []
                    self.blasting[1].health = 100
                self.blasting = False
        for a in self.active_attacks:
            winnings += a.update(time_passed)
        return winnings

    def blitme(self):
        Creep.blitme(self)
        for a in self.active_attacks:
            a.blitme()
        if self.blasting:
            target = self.blasting[1]
            for idx in range(5):
                offsets = [4 * random() - 2.0 for i in range(4)]
                pygame.draw.line(self.screen,
                                 pygame.Color(255, 0, 0),
                                 (self.pos.x + offsets[0], 
                                 self.pos.y + offsets[1]),
                                 (target.pos.x + offsets[2],
                                  target.pos.y + offsets[3]))
                                 
                
class Attack(Creep):
    def __init__(self, parent, target, special=None, visible=True, img=None, pos=None):
        self.parent = parent
        if not pos:
            self.pos = parent.pos
        else:
            self.pos = pos
        self.target = target
        self.speed = 0.1
        self.special = special
        self.visible = visible
        self.image = img
        if self.image:
            self.image_w, self.image_h = self.image.get_size()

    def update(self, time_passed):
        delta = self.target.pos - self.pos
        winnings = 0
        if delta.get_length() < time_passed * self.speed:
            # force it back to the start
            if (not self.special) or self.special(self.target):
                self.target.health -= 10
                if self.target.health <= 0:
                    winnings = 5
                    self.target.paths = []
                    self.target.health = 100
                # play the explosion
                # print self.target.explosion.play(fade_ms=50), self.target.explosion
            self.parent.active_attacks.remove(self)
        else:
            self.pos = self.pos + (delta * (time_passed * self.speed) / delta.get_length())
        return winnings
            
    def blitme(self):
        if self.visible:
            if self.image:
                draw_pos = self.image.get_rect().move(
                    self.pos.x - self.image_w / 2, 
                    self.pos.y - self.image_h / 2)
                self.parent.screen.blit(self.image, draw_pos)
            else:
                pygame.draw.circle(self.parent.screen, pygame.Color(255, 255, 255), self.pos, 5)

class MobileAttack(Attack):
    def update(self, time_passed):
        delta = self.target[0].pos - self.pos
        if delta.get_length() < time_passed * self.speed:
            self.target[0].confused = 5000.0
            self.target = self.target[1:]
            if len(self.target) == 0:
                self.parent.active_attacks.remove(self)
        else:
            self.pos = self.pos + (delta * (time_passed * self.speed) / delta.get_length())
        return 0
            
    def blitme(self):
        if self.visible:
            if self.image:
                draw_pos = self.image.get_rect().move(
                    self.pos.x - self.image_w / 2, 
                    self.pos.y - self.image_h)
                self.parent.screen.blit(self.image, draw_pos)
            else:
                pygame.draw.circle(self.parent.screen, pygame.Color(255, 255, 255), self.pos, 5)
    

# inherit from tower to manage attacks
class GlobalAttacks(Tower):
    def update(self, time_passed):
        winnings = 0
        for a in self.active_attacks:
            winnings += a.update(time_passed)
        return winnings

    def blitme(self):
        for a in self.active_attacks:
            a.blitme()

    def ready(self):
        return True
        return self.active_attacks == []

    def target(self, target):
        self.pos = vec2d(target.pos.x, 10)
        self.active_attacks.append(Attack(self,
                                          target,
                                          img=self.image))
    def add_attack(self, attack):
        self.active_attacks.append(attack)
        

class Button(Creep):
    def __init__(self, *args, **kwargs):
        Creep.__init__(self, *args, **kwargs)
        self.health = 0
        bg = pygame.Surface(self.image.get_size())
        bg.fill((128, 128, 128))
        bg.blit(self.image, (0, 0))
        self.image = bg
        

class Cursor(Creep):
    def __init__(self, *args, **kwargs):
        Creep.__init__(self, *args, **kwargs)
        self.health = 0
        self.fix_im()

    def change_image(self, *args, **kwargs):
        Creep.change_image(self, *args, **kwargs)
        self.fix_im()

    def fix_im(self):
        arr = pygame.surfarray.pixels_alpha(self.image)
        arr[:,:] = (2.0 * arr) / 3

    def update(self):
        self.pos = vec2d(pygame.mouse.get_pos())

    def blitme(self):
        Creep.blitme(self)
        pygame.draw.circle(self.screen, pygame.Color(128, 10, 10, 128), self.pos, 100, 1)



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
        'skrals.png',
        'stronius1.png',
        'stronius2.png',
        'metus_with_guards.png']
    TOWER_FILENAMES = [
        'matanui.png',
        'malum.png',
        'gresh.png',
        'gelu.png',
        'vastus.png',
        'kiina.png',
        'ackar.png',
        'straak.png'
        ]
    SELL_FILENAME = 'Sell.png'
    RAIN_OF_FIRE = 'rain_of_fire.png'
    TORNADO = 'tornado.png'
    TORNADO_BIG = 'tornado_big.png'
    BUTTON_FILENAMES = TOWER_FILENAMES + [RAIN_OF_FIRE, TORNADO, SELL_FILENAME]

    money = 643823726935627492742129573207

    mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
    mixer.init()
    mixer.set_num_channels(30)
    print "mix", mixer.get_num_channels()
    EXPLOSIONS = [mixer.Sound('expl%d.wav'%(i)) for i in range(1, 7)]
    FIRING = [mixer.Sound('fire%d.wav'%(i)) for i in range(1, 4)]
    N_CREEPS = 10
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
                            paths,
                            choice(EXPLOSIONS)))

    towers = [Tower(screen,
                    choice(TOWER_FILENAMES),
                    (randint(0, background.get_size()[0]), randint(0, background.get_size()[1])),
                    (1, 1),
                    0.0,
                    paths, radius=100, max_attacks=3, firing_sounds=FIRING) for i in range (N_TOWERS)]

    buttons = [Button(screen,
                      buttonfile,
                      (randint(0, background.get_size()[0]), randint(0, background.get_size()[1])),
                      (1, 1),
                      0.0,
                      paths) for buttonfile in BUTTON_FILENAMES]



    rightedge = screen.get_width() - 5
    for b in buttons[:len(buttons)//2]:
        b.pos = vec2d(rightedge - b.image.get_width() / 2, 5 + b.image.get_height() / 2)
        rightedge -= (b.image.get_width() + 5)
    rightedge = screen.get_width() - 5
    for b in buttons[len(buttons)//2:]:
        b.pos = vec2d(rightedge - b.image.get_width() / 2, 5 + b.image.get_height() / 2 + 80)
        rightedge -= (b.image.get_width() + 5)

    next_tower = TOWER_FILENAMES[0]

    cursor = Cursor(screen, TOWER_FILENAMES[0],
                    (0, 0),
                    (1,1),
                    0.0, paths)

    font = pygame.font.SysFont(pygame.font.get_default_font(), 20, bold=True)

    tornado_img = pygame.image.load(TORNADO_BIG).convert_alpha()

    global_attacks = GlobalAttacks(screen, RAIN_OF_FIRE,
                                   (randint(0, background.get_size()[0]), randint(0, background.get_size()[1])),
                                   (1, 1),
                                   0.0,
                                   paths, radius=100, max_attacks=3, firing_sounds=FIRING)

    # The main game loop
    #
    rect = pygame.Rect((1, 1), (10, 10))
    selling = False    
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
                            selling = (b.img_filename == SELL_FILENAME)
                            rain_of_fire = (b.img_filename == RAIN_OF_FIRE)
                            tornado = (b.img_filename == TORNADO)
                            buying = (not selling) and (not rain_of_fire)
                            if buying:
                                next_tower = BUTTON_FILENAMES[buttons.index(b)]
                                cursor.change_image(next_tower)
                            # only one rain of fire available at a time
                            if global_attacks.ready():
                                if rain_of_fire:
                                    for i in range(20):
                                        target = choice(creeps)
                                        global_attacks.target(target)
                            if tornado:
                                targets = [choice(creeps) for i in range(20)]
                                tornado_attack = MobileAttack(global_attacks, 
                                                              targets, 
                                                              img=tornado_img, 
                                                              pos=vec2d((randint(0, background.get_size()[0]), 
                                                                         randint(0, background.get_size()[1]))))
                                tornado_attack.speed = 0.2
                                global_attacks.add_attack(tornado_attack)
                            collided = True
                    for t in towers:
                        if cursor.rect.colliderect(t.rect):
                            collided = t
                    if not collided and not selling and money >= 100:
                        towers += [Tower(screen,
                                         next_tower,
                                         pygame.mouse.get_pos(),
                                         (1, 1),
                                         0.0,
                                         paths,
                                         radius=100,
                                         max_attacks=3,
                                         firing_sounds=FIRING)]
                        money -= 100
                    if selling and collided:
                        if collided in towers:
                            towers.remove(collided)
                            money += 50

        # Redraw the background
        screen.blit(background, backgroundRect)
        
        # Update and redraw all creeps
        for creep in creeps:
            creep.update(time_passed)

        for tower in towers:
            tower.attack(creeps)
            money += tower.update(time_passed)

        money += global_attacks.update(time_passed)
        
        cursor.update()

        for obj in creeps + towers + buttons + [global_attacks, cursor]:
            obj.blitme()
            
        money_text = font.render("%d"%(money), True, pygame.Color(0, 0, 0))
        screen.blit(money_text, (rightedge - 5 - money_text.get_width(), 5 + money_text.get_height()))

        pygame.display.flip()


def exit_game():
    sys.exit()


run_game()

