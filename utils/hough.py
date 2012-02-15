__all__ = ["Hough"]

from scipy.ndimage.filters import sobel, generic_gradient_magnitude
from math import pi, sqrt, atan2, sin, cos
from collections import defaultdict
from itertools import izip
from numpy import nonzero

class Hough:

    def __init__(self, image, threshold=127):
        self.threshold = threshold
        self.image = image

        self.min_major_axis = 7
        self.max_major_axis = 35
        self.max_b = 10
        self.min_b = 7
        self.min_frequency = 10
        self.path_points = 100
        self.verification_distance = 2.
        self.coverage_ratio = 0.94


    def convert_ellipse(self, from_image, a, b, c, y1, y2, x1, x2):
        image_b = cross_mul(b, self.image.shape[0], from_image.shape[0])
        image_a = cross_mul(a, self.image.shape[1], from_image.shape[1])
        image_c = cross_mul(c[0], self.image.shape[0], from_image.shape[0])
        image_c = (image_c, cross_mul(c[1], self.image.shape[1], from_image.shape[1]))
        image_y1 = cross_mul(y1, self.image.shape[0], from_image.shape[0])
        image_y2 = cross_mul(y2, self.image.shape[0], from_image.shape[0])
        image_x1 = cross_mul(x1, self.image.shape[1], from_image.shape[1])
        image_x2 = cross_mul(x2, self.image.shape[1], from_image.shape[1])
        image_alfa = atan2((image_y2 - image_y1), (image_x2 - image_x1))
        return (image_c, image_a, image_b, image_alfa)

    def edge_detection(self):
        return generic_gradient_magnitude(self.image, sobel)

    def store_edges(self, resize=None):

        img = self.edge_detection()

        if resize is not None: img = resize(img)

        return list(izip(*nonzero(img > self.threshold))), img

    def supported_ellipse(self, wp, center, a, b, alfa, ignore = []):

        data = parametric_ellipse(center, a, b, alfa, self.path_points)

        supported = []
        support_ratio = 0.0

        for i in range(self.path_points):

            ely, elx = data[i]

            for y, x in wp:

                if (y, x) in ignore: continue

                verification_distance = distance((ely, elx), (y, x))

                if verification_distance > self.verification_distance:
                    continue

                supported.append((y, x))
                support_ratio += 1. / float(self.path_points)
                break

        if support_ratio < self.coverage_ratio: return False

        ignore += supported

        return True

    def max_frequency(self, bbins):
        max_freq = 0
        half_minor_axis = 0
        for key, value in bbins.items():
            if value > max_freq:
                max_freq = value
                half_minor_axis = key
        return max_freq, half_minor_axis

    def find_ellipses(self, resize=None):

        wp, edge_image = self.store_edges(resize)
        ignore = []

        for (y1, x1) in wp:

            if (y1, x1) in ignore: continue

            for (y2, x2) in wp:

                if (y2, x2) in ignore: continue

                bbins = defaultdict(int)

                major_axis = distance((y1, x1), (y2, x2))

                if major_axis < self.min_major_axis: continue
                if major_axis > self.max_major_axis: continue

                c = ((y1 + y2) / 2., (x1 + x2) / 2.)
                a = major_axis / 2.
                alfa = atan2((y2 - y1), (x2 - x1))

                for y3, x3 in wp:

                    if (y3, x3) in ignore: continue

                    d = distance((y3, x3), c)

                    if d < self.min_b or d > a:
                        continue

                    f = distance((y3, x3), (y2, x2))

                    cost = a ** 2. + d ** 2. - f ** 2.
                    cost /= 2. * a * d

                    b = a ** 2. - d ** 2. * cost ** 2.
                    if b == 0: continue
                    b = (a ** 2. * d ** 2. * (1. - cost ** 2.)) / b
                    if b <= 0: continue
                    b = int(sqrt(b))
                    if b == 0: continue
                    bbins[b] += 1

                max_freq, b = self.max_frequency(bbins)

                if max_freq < self.min_frequency: continue
                if alfa < 0.0: continue
                if b < self.min_b: continue
                if b > self.max_b: continue
                if not self.supported_ellipse(wp, c, a, b, alfa, ignore): continue

                yield (self.convert_ellipse(edge_image, a, b, c, y1, y2, x1, x2))


def parametric_ellipse(center, a, b, angle, path_points):
    yc, xc = center

    ely = lambda t: yc + a * cos(t) * sin(angle) + b * sin(t) * cos(angle)
    elx = lambda t: xc + a * cos(t) * cos(angle) - b * sin(t) * sin(angle)

    return [(
        ely(2. * pi * x / float(path_points)),
        elx(2. * pi * x / float(path_points - 1))
        ) for x in range(path_points)]

def distance((y, x), (dy, dx)):
    return sqrt((x - dx) ** 2 + (y - dy) ** 2)

def cross_mul(a, c, b):
    d = a * c / b
    return d