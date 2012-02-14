# -*- coding: utf-8 -*-
from bresenham import bresenham
from copy import deepcopy
from random import shuffle
from itertools import product, chain
from hough import distance
import numpy as np

__all__ = ["WormLost"]

class WormLost:

    def __init__(self, ellipse, image, initial_population=2, max_population=300, threshold=127, step_a=5):

        self.max_population = max_population

        self.next_generation = {}
        self.worm_eggs = []
        self.worms = {}
        self.successful_worms = []

        self.image = image
        self.ellipse = ellipse
        self.threshold = threshold

        self.birth_points = iter(self.create_birth_points(step_a))
        self.populate(initial_population)

        self.callback_preferred = [self.same_radius]
        self.callback_candidates = [self.on_image, self.not_taked, self.border_limit]
        self.callback_point = [self.inside_ellipse]

        self.worm_key = 0

    def same_radius(self, worm, candidates={}):
        candidates = {}
        if not worm.in_points: return
        rd = distance(worm.in_points[-1], self.ellipse[0]) # Reference Distance
        for k, p in candidates.iteritems():
            rp = distance(p, self.ellipse[0])
            worm[k] = -abs(rp - rd)


    def border_limit(self, worm, (y, x)):
        pt = self.image[y, x] < self.threshold
        data = False
        for p in chain(product((y,), (x + 1, x - 1)),
                          product((y + 1, y - 1), (x,))):

            if worm.in_points:
                if p == worm.in_points[-1]: continue
                elif p in worm.in_points: return False
            tt = self.image[p] < self.threshold
            if tt != pt: data = True

        return data

    def not_taked(self, worm, p):
        for test in chain(self.worms.values(), self.successful_worms):
            if p in test.in_points: return False
        return True

    def inside_ellipse(self, worm, p):

        d = distance(self.ellipse[0], p)

        minor = min(self.ellipse[1:3]) * .8
        if d < minor * .8: raise WormException, "limit exceeded: min %d < %d" % (d, minor)

        maximum = max(self.ellipse[1:3]) * 1.2
        if d > maximum: raise WormException, "limit exceeded: min %d < %d" % (d, maximum)

    def on_image(self, worm, (y, x)):
        if x < 0 or y < 0: return False
        height, width = self.image.shape
        if y > height or x > width: return False
        return True

    def mature(self, k, worms):
        if not self.next_generation[k]: return
        worms[k] = self.next_generation[k][0]
        self.next_generation[k].pop(0)


    def next_worm(self):
        worms = {}

        for key, worm in self.worms.iteritems():
            try:
                print "W%d: exec" % key
                worm.next()
                worms[key] = worm
            except StopIteration:
                print "W%d: Debugging" % key
                self.successful_worms.append(worm)
            except WormException, e:
                print "W%d: %s" % (key, e)
                self.next_generation[key] += worm.children
                self.mature(key, worms)

        self.worms = worms

    def worm_debug(self, worm, points=[]):
        image = image_colorize(self.image, self.threshold)
        for p in worm.in_points: image[p] = (0, 255, 0)
        for p in points: image[p] = (127, 127, 0)
        print "Debugging %s" % worm.name
        imshow(image)

    def next_worm_egg(self):
        worm_eggs = []

        for index, worm_egg in enumerate(self.worm_eggs):
            try:
                worm_egg.next()
                worm_eggs.append(worm_egg)
            except StopIteration:
                self.worms[self.worm_key] = worm_egg.get_worm()
                self.next_generation[self.worm_key] = []
                self.worm_key += 1
            except WormException, e:
                print "E%d: %s" % (index, e)

        self.worm_eggs = worm_eggs

    def next(self): #@ReservedAssignment
        if not self.worms and not self.worm_eggs: raise StopIteration
        self.next_worm_egg()
        self.next_worm()

    def populate(self, total):
        total = min(total, self.max_population - (len(self.worm_eggs) + len(self.worms)))
        while total:

            try: self.worm_eggs.append(WormEgg(self, next(self.birth_points)))
            except StopIteration: break

            total -= 1

        return total

    def create_birth_points(self, step_a):

        y, x = self.ellipse[0]
        a, b = self.ellipse[1:3]

        b += 5
        miny = max(int(y - b), 0)
        maxy = min(int(y + b), self.image.shape[0])

        birth_points = list(product((miny, maxy), xrange(int(x - a), int(x + a) + 1, step_a)))

        shuffle(birth_points)

        return birth_points

    def __iter__(self):
        return self

    def solve(self):
        for i in self: pass

class WormEgg:

    def __init__(self, worm_lost, birth_point, name=None):
        self.worm_lost = worm_lost
        self.birth_point = birth_point
        self.center_line = iter(bresenham(birth_point, worm_lost.ellipse[0])) # Create line
        self.name = name

    def threshold_test(self, (y, x)):
        return threshold_test(self.worm_lost.image, (y, x), self.worm_lost.threshold)

    def __iter__(self):
        self.next()

    def get_worm(self):
        return Worm(self.worm_lost, [self.start_point], name=self.name)

    def next(self): #@ReservedAssignment
        try: p = self.center_line.next()
        except StopIteration: raise WormException

        if not self.threshold_test(p): return

        self.start_point = p
        raise StopIteration

class Worm:

    def __init__(self, worm_lost, candidates, in_points=[], name=None):

        self.worm_lost = worm_lost
        self.name = name

        self.children = []
        self.in_points = in_points

        self.callback_candidates = []
        self.callback_preferred = []
        self.callback_point = []
        self.candidates = candidates

    def child(self):
        #self.worm_lost.worm_debug(self)
        return Worm(self.worm_lost, deepcopy(self.candidates), deepcopy(self.in_points), name=self.name)


    def valid_image_point(self, (y, x)):

        if y < 0 or x < 0:
            return False

        height, width = self.worm_lost.image.shape[0:2]

        if y > height or x > width:
            return False

        return True

    def store_child(self):
        if not self.candidates: return
        self.children.append(self.child())

    def validate_candidate(self, vp):
        for validate in chain(self.callback_candidates, self.worm_lost.callback_candidates):
            if not validate(self, vp): return False
        return True

    def validate_candidates(self):
        passed = []
        for candidate in self.candidates:
            if self.validate_candidate(candidate):
                passed.append(candidate)
        self.candidates = passed

    def generate_candidates(self):
        y, x = self.in_points[-1]
        # make a cube
        return chain(product((y + 1, y - 1), (x + 1, x, x - 1)),
              product((y,), (x + 1, x - 1)))

    def preferred_direction(self):

        candidates = {}
        for k in self.candidates: candidates[k] = 0

        for fnc_importance in chain(self.callback_preferred,
                                    self.worm_lost.callback_preferred):
            fnc_importance(self, candidates)

        sorted(candidates, key=lambda (k, v):(v, k), reverse=True)
        self.candidates = candidates.keys()

    def run(self):
        self.validate_candidates()
        len_candidates = len(self.candidates)

        if not len_candidates: raise StopIteration
        if len_candidates > 1: self.preferred_direction()

        p = self.candidates[0]
        self.candidates.pop(0)

        self.store_child()
        self.run_at(p)

    def run_at(self, p):
        for validate in chain(self.callback_point, self.worm_lost.callback_point):
            validate(self, p)
        self.in_points.append(p)

    def __iter__(self):
        self.next()

    def next(self): #@ReservedAssignment
        self.run()
        self.candidates = self.generate_candidates()


def image_colorize(image, treshold=127):
    colorized = np.zeros(list(image.shape[0:2]) + [3])
    for y, x in product(*[xrange(x) for x in image.shape[0:2]]):
        colorized[y, x] = [(image[y, x] > treshold) * 255] * 3
    return colorized

def threshold_test(image, (y, x), threshold):
    return image[y, x] < threshold

class WormException(Exception): pass

if __name__ == "__main__":
    import json
    from sys import argv
    from scipy.misc import imshow
    from scipy.ndimage import imread

    if len(argv) < 3:
        raise Exception("Usage: ./worm_lost recaptcha.jpeg ellipse_json")
    reimage = imread(argv[1], True)
    a = WormLost(json.loads(argv[2]), reimage)
    imshow(image_colorize(reimage))
    a.solve()
    for worm in a.successful_worms:
        a.worm_debug(worm)