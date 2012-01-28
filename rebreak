#!/usr/bin/env python

from sys import argv
from scipy.misc import imshow
from utils import WordSlice, Hough
# Hack to run on Scipy > 0.7
try: from scipy.misc import imread
except: from scipy.ndimage import imread

if len(argv) < 2:
	raise Exception("Usage: ./wordslice recaptcha.jpeg");
for i in WordSlice(imread(argv[1], True)).get_words():
	print Hough(i).scan()
