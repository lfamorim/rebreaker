from bresenham import bresenham
from copy import copy
from random import shuffle
from itertools import product, chain
import numpy
__all__ = ["WormLost"]

class WormLost(object):

    def __init__(self, ellipse, image, initial_population=4, max_population=10, threshold=127, step_a=5):
        
        self.max_population = max_population
        
        self.worms = []
        self.worms_out = []
        self.worms_in = []
        self.worms_stuck = []

        self._image = image
        self._ellipse = ellipse
        self._next_direction = 1
        self._threshold = threshold
        
        self._create_birth_points(step_a)
        
        self.populate(initial_population)

    def solve(self):
        while self.worms_in or self.worms_out:
            self.iterate()
        
        for worm in self.worms:
            imshow(worm.image_colorize())

    def populate(self, total):
        for i in xrange(total): self.inicialize_worm()
                
    def _create_birth_points(self, step_a):
        
        y, x = self._ellipse[0]
        a, b = self._ellipse[1:3]
        
        b += 5
        
        lowy = int(y - b)
        if lowy < 0: lowy = 0

        highy = int(y + b)
        if highy > self._image.shape[0]: highy = self._image.shape[0]
        
        
        range_a = range(int(x - a), int(x + a) + 1, step_a)
        range_a = product((lowy, highy), range_a)
        birth_points = [v for v in range_a]
        shuffle(birth_points)
        
        
        self._birth_points = iter(birth_points)

    def _inicialize_worm(self):
        # Check population size
        if len(self.worms) == self.max_population:
            raise WormException, "Maximum population reached"

        # Get birth point
        try: point_birth = next(self._birth_points)
        except StopIteration:
            raise WormException("No more birthday points") 
        
        #Create Worm
        worm = Worm(self, self._next_direction, point_birth, self._ellipse, self._image, self._threshold)
        return worm

    def inicialize_worm(self):
        # Check population size
        if len(self.worms) == self.max_population:
            raise WormException, "Maximum population reached"

        while True:
            try:
                worm = self._inicialize_worm()
                self.worms.append(worm)
                self.worms_out.append(worm)
                self._next_direction *= -1
                break
            except PointException: pass
        

    def validate_in(self, worm, index, candidates):
        for candidate in copy(candidates):
            for worm in self.worms:
                if candidate in worm.in_points:
                    candidates.remove(candidate)

    def _iterate_in(self):
        for worm in copy(self.worms_in):
            try:
                worm.iterate_in(self.validate_in)
            except StopIteration:
                self.worms_in.remove(worm)
                self.worms_stuck.append(worm)
            except WormException:
                self.worms_in.remove(worm)
                self.worms.remove(worm)


    def iterate_out(self):
        for worm in copy(self.worms_out):
            try:
                worm.iterate_out()
            except StopIteration:
                self.worms_out.remove(worm)
                self.worms_in.append(worm)
            except WormException:
                self.worms_out.remove(worm)
                self.worms.remove(worm)
 
    def iterate(self):
        self._iterate_in()
        self.iterate_out()
            
class Worm:    
                
    def __init__(self, worm_lost, direction, birth_point, ellipse, image, threshold=127):
        
        self._worm_lost = worm_lost
        self._image = image
        self._threshold = threshold
        
        if self.threshold_test(birth_point): raise PointException

        self.in_points = []
        self.out_points = [birth_point]
        self.key_points = [birth_point]

        self._direction = direction
        self._ellipse = ellipse
        self._stuck = {-1 : False, 1:  False}
        self._center_line = bresenham(birth_point, ellipse[0])
        
        
    def stuck(self):
        self._stuck[self._direction] = True

    def image_colorize(self, imc=None):
        
        if imc == None: imc = image_colorize(self._image)
        
        for y, x in self.in_points: imc[y][x] = (255, 0, 0)
        for y, x in self.out_points: imc[y][x] = (0, 255, 0) 
        for y, x in self.key_points: imc[y][x] = (0, 0, 255)
        
        return imc
        

    def stuck_action(self, interact=None):
        self.stuck()
        self.change_direction()
        return self.iterate_in(interact)

    def threshold_test(self, (y, x)):
        return self._image[y][x] < self._threshold

    def _is_out_of_limit(self, (y, x)):
        
        if y < 0 or x < 0: return True

        my, mx = self._image.shape
        
        if y >= my or x >= mx: return True

        return False
    
    def is_border_limit(self, p, plast):
        y, x = p
        pthreshold = self.threshold_test(p)
                
        for ptest in chain(product((y,), (x + 1, x - 1)),
                           product((y + 1, y - 1), (x,))):

            if self._is_out_of_limit(ptest): continue
            elif ptest == plast: continue
            elif self.threshold_test(ptest) != pthreshold: return True
        return False
    
    def iterate_out(self, interact=None):
        
        p = self._center_line.next()
            
        if p == None: raise Exception, "Just the way"

        if not self.threshold_test(p):
            self.out_points.append(p)
            return

        if interact is not None: interact(self, p)

        self.key_points.append(p)
        self.in_points.append(p)
        
        raise StopIteration

    def iterate_in(self, interact=None):
                
        if self._stuck[self._direction] == True: raise StopIteration
        
        y, x = p = self.in_points[-1]
        
        candidates = [v for v in product((y + 1, y, y - 1), (x + 1, x, x - 1))]
        candidates.remove(p)

        for candidate in copy(candidates):
            if self._is_out_of_limit(candidate):
                candidates.remove(candidate)
            elif not self.is_border_limit(candidate, p):
                candidates.remove(candidate)
            elif candidate in self.in_points:
                candidates.remove(candidate)
        
        index_direction = int((self._direction * 0.5) - 0.5)
        if interact != None: interact(self, index_direction, candidates)
        
        if not candidates: return self.stuck_action(interact)
        self.in_points.append(candidates[index_direction])
        

    def change_direction(self):
        self.in_points.append(self.key_points[-1])
        self.key_points.append(self.in_points[-2])
        self._direction *= -1
            
def image_colorize(image):
    colorized = numpy.zeros((image.shape[0], image.shape[1], 3))
    for y in range(image.shape[0]): 
        for x in range(image.shape[1]):
            colorized[y][x] = [image[y][x]] * 3
    return colorized

class WormException(Exception): pass
class PointException(WormException): pass

if __name__ == "__main__":
    import json
    from sys import argv
    from scipy.misc import imshow
    from scipy.ndimage import imread
    

    if len(argv) < 3:
        raise Exception("Usage: ./worm_lost recaptcha.jpeg ellipse_json")
    
    print WormLost(json.loads(argv[2]), imread(argv[1], True)).solve()
