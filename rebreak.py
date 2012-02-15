#!/usr/bin/env python

from utils import *
from sys import argv
from scipy.misc import imshow, imresize
from os import getenv,environ
from scipy.ndimage import imread

if len(argv) < 2:
	raise Exception("Usage: ./rebreak image.jpeg")
for image in WordSlice(imread(argv[1], True)):
	print "slice", image.shape[0:2]
	for ellipse in Hough(image).find_ellipses(lambda img: imresize(img, 0.4, 'bilinear')):
		print "ellipse", ellipse
		worm_lost = WormLost(ellipse, image)
		worm_lost.solve()
		[worm_lost.worm_debug(i) for i in worm_lost.successful_worms]
