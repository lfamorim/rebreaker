#!/usr/bin/env python

from utils import Hough, WordSlice
from sys import argv
from scipy.misc import imshow, imresize
from os import getenv,environ
from scipy.ndimage import imread

if len(argv) < 2:
	raise Exception("Usage: ./rebreak image.jpeg")
for i in WordSlice(imread(argv[1], True)).get_words():
	Hough(i).find_ellipses(lambda img: imresize(img, 0.4, 'bilinear'))
