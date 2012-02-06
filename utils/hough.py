#!/usr/bin/env python

__all__ = ["Hough"]

from scipy.ndimage.filters import sobel, generic_gradient_magnitude
from math import pi, sqrt, atan2, sin, cos
from collections import defaultdict

class Hough:

	def __init__(self, image, threshold = 127):
		self._threshold = threshold
		self._image = image
		
		self.min_major_axis = 7
		self.max_major_axis = 35
		
		self.max_b = 10
		self.min_b = 7
		
		self.min_frequency = 10
		self.path_points = 100
		self.verification_distance = 2.
		self.coverage_ratio = 0.94
	
	def find_ellipses(self, resize = None):

		ellipses = []

		wp, edge_image = self._store_edges(resize)
	
		for y1, x1 in wp:
			for y2, x2 in wp:

				bbins = defaultdict(int)

				major_axis = distance((y1, x1), (y2, x2))

				if major_axis < self.min_major_axis or major_axis > self.max_major_axis:
					continue

				c = ((y1+y2)/2., (x1+x2)/2.)
				a = major_axis/2.
				alfa = atan2((y2 - y1), (x2 - x1))

				for y3, x3 in wp:

					d = distance((y3, x3), c)

					if d < self.min_b or d > a:
						continue

					f = distance((y3,x3),(y2,x2))
	
					cost = a ** 2. + d ** 2. - f ** 2.
					cost /= 2. * a * d

					b = a ** 2. - d ** 2. * cost ** 2.
					if b == 0: continue
					b = (a ** 2. * d ** 2. * (1. - cost ** 2.)) / b
					if b <= 0: continue
					b = int(sqrt(b))
					if b == 0: continue
					bbins[b] += 1

				max_freq, b = self._max_frequency(bbins)
	
				if max_freq < self.min_frequency: continue
				if alfa < 0.0: continue
				if b < self.min_b: continue
				if b > self.max_b: continue

				supported = self._supported_ellipse(wp, c, a, b, alfa)
				
				if supported == None: continue

				for p in supported:	wp.remove(p)
				
				image_b = cross_mul(b, self._image.shape[0], edge_image.shape[0])
				image_a = cross_mul(a, self._image.shape[1], edge_image.shape[1])

				image_c = cross_mul(c[0], self._image.shape[0], edge_image.shape[0])
				image_c = (image_c, cross_mul(c[1], self._image.shape[1], edge_image.shape[1]))
				
				image_y1 = cross_mul(y1, self._image.shape[0], edge_image.shape[0])
				image_y2 = cross_mul(y2, self._image.shape[0], edge_image.shape[0])
				image_x1 = cross_mul(x1, self._image.shape[1], edge_image.shape[1])
				image_x2 = cross_mul(x2, self._image.shape[1], edge_image.shape[1])
				
				image_alfa = atan2((image_y2-image_y1), (image_x2-image_x1))
				
				ellipses.append((image_c, image_a, image_b, image_alfa))
				

		return ellipses
	
	def _edge_detection(self):
		return generic_gradient_magnitude(self._image, sobel)

	def _store_edges(self, resize = None):

		img = self._edge_detection()

		if resize is not None: img = resize(img)

		wp = []

		for y in range(img.shape[0]):
			for x in range(img.shape[1]):
				if img[y][x] > self._threshold: wp.append((y,x))

		return wp, img

	def _supported_ellipse(self, wp, center, a, b, alfa):
				
		data = parametric_ellipse(center, a, b, alfa, self.path_points)

		supported = []
		support_ratio = 0.0
	
		for i in range(self.path_points):
			
			ely, elx = data[i]
	
			for y, x in wp:

				verification_distance = distance((ely, elx), (y, x))
	
				if verification_distance > self.verification_distance:
					continue

				supported.append((y, x))
				support_ratio += 1. / float(self.path_points)
				break
	
		if support_ratio < self.coverage_ratio: return None

		supported = uniqify(supported)

		return supported

	def _max_frequency(self, bbins):
		max_freq = 0
		half_minor_axis = 0
		for key, value in bbins.items():
			if value > max_freq:
				max_freq = value
				half_minor_axis = key
		return max_freq, half_minor_axis
	
	
def parametric_ellipse(center, a, b, angle, path_points):
	yc, xc = center

	ely = lambda t: yc + a * cos(t) * sin(angle) + b * sin(t) * cos(angle)
	elx = lambda t: xc + a * cos(t) * cos(angle) - b * sin(t) * sin(angle)

	return [(
		ely(2. * pi * x / float(path_points)),
		elx(2. * pi * x / float(path_points-1))
		) for x in range(path_points)]
		
def distance((y, x), (dy, dx)):
	return sqrt((x - dx) ** 2 + (y - dy) ** 2)
	
def cross_mul(a, c, b):
	d = a * c / b
	return d

def uniqify(seq):  
	keys = {} 
	for e in seq: 
		keys[e] = 1 
	return keys.keys()

if __name__ == "__main__":
	from sys import argv
	from scipy.ndimage import imread

	if len(argv) < 2:
		raise Exception("Usage: ./hough atom.jpg")
	
	Hough(imread(argv[1], True)).find_ellipses()
