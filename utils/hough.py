#!/usr/bin/env python
import numpy, operator
from scipy.misc import imresize, imshow
from scipy.ndimage.filters import sobel
from math import *
from collections import defaultdict

class Hough:

	_image = None
	_threshold = 127

	half_major = 8
	half_minor = 6
	minor_frequency = 30
	path_points = 51
	verification_distance = 1.
	coverage_ratio = 0.9
	
	def __init__(self, image, threshold = 127):
		self._threshold = threshold
		self._image = image

	def _sobel(self):
		sdy = sobel(self._image, 0)
		sdx = sobel(self._image, 1)
		mag = numpy.hypot(sdx, sdy)
		mag *= 255.0 / numpy.max(mag)
		return mag

	def _parametric_ellipse(self, center, a, b, angle):
		yc, xc = center

		ely = lambda t: yc + a * cos(t) * sin(angle) + b * sin(t) * cos(angle)
		elx = lambda t: xc + a * cos(t) * cos(angle) - b * sin(t) * sin(angle)

		return [(
			int(ely(2. * pi * x / float(self.path_points-1))),
			int(elx(2. * pi * x / float(self.path_points-1)))
		) for x in range(self.path_points)]


	@staticmethod	
	def _distance(p1, p2):
		return sqrt((p1[1] - p2[1]) ** 2 + (p1[0] - p2[0]) ** 2)

	def scan(self):

		ellipses = []

		img = self._sobel()
#		img = imresize(img, 0.25, 'bilinear')

#		imshow(img)

		wp = []

		for y in range(0, img.shape[0]):
			for x in range(0, img.shape[1]):
				if img[y][x] > self._threshold: wp.append((y,x))

		for y1, x1 in wp:
			for y2, x2 in wp:

				bbins = defaultdict(int)

				iteraction_distance = self._distance((y1, x1), (y2, x2))
				if iteraction_distance < 2 * self.half_major:
					continue

				center = ((y1+y2)/2., (x1+x2)/2.)
				half_distance = iteraction_distance/2.
				alfa = atan2((y2 - y1), (x2 - x1))

				for y3, x3 in wp:

					center_distance = self._distance((y3, x3), center)

					if center_distance < self.half_minor:
						continue
			
					f = self._distance((y3, x3), (y2, x2))

					cost = half_distance ** 2. + center_distance ** 2. - f**2.
					cost /= 0.00001 + 2. * half_distance * center_distance

					b = (half_distance ** 2. * center_distance ** 2. * (1. - cost ** 2.))
					b /= (0.00001 + half_distance ** 2. - center_distance ** 2. * cost ** 2.)

					if b <= 0: continue
					b = int(sqrt(b))
					if b <= 0: continue

					bbins[b] += 1
			
				bbins_rev = dict([(v,k) for k,v in bbins.iteritems()])
				max_freq = max(bbins_rev.keys())
				bmax = bbins_rev[max_freq]

				if max_freq < self.minor_frequency or alfa < 0.0 or bmax < self.half_minor: continue
				
				data = self._parametric_ellipse(center, half_distance, bmax, alfa)
				supported = []
				support_ratio = 0.0

				for i in range(self.path_points):
					ely, elx = data[i]

					added = False
					for y, x in wp:

						if self._distance((ely, elx), (y,x)) > self.verification_distance:
							continue
					
						supported.append((y, x))
    	     			if not added:
							support_ratio += 1. / float(self.path_points)
							added = True


				supported = list(set(supported))

				if support_ratio < self.coverage_ratio: continue
				
				for p in supported: wp.remove(p)

				print data				
				ellipses.append(data)

		return ellipses

if __name__ == "__main__":
	from sys import argv
	from scipy.misc import imread
	
	# Hack to run on Scipy > 0.7
	try: from scipy.misc import imread
	except: from scipy.ndimage import imread

	if len(argv) < 2:
		raise Exception("Usage: ./hough atom.jpg");
	
	print Hough(imread(argv[1], True)).scan()
