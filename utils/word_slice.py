#!/usr/bin/env python
import numpy

class WordSlice:

	_end_points = []
	_threshold = 127
	_separator = 8
	_image = None
	_minimum_size = 0

	def __init__(self, image, separator = 8, threshold = 127, minimum_size = 15):
		self._image = image
		self._threshold = threshold
		self._separator = separator
		self._minimum_size = minimum_size

	def _scan(self):
		had_content = False

		for x in range(0, self._image.shape[1]):
			# This Y line has content?
			content = False
			for y in range(0, self._image.shape[0]):
				if self._image[y][x] < self._threshold: 
					content = True

			# If yes, this is not blank.
			if content:
				empty_line = 0
				had_content = True
				continue

			if not had_content:
				continue

			empty_line += 1
			if empty_line == self._separator:
				self._end_points.append(x)
				had_content = False

		if had_content:
			self._end_points.append(size_x)
			
	def get_words(self):
		
		self._scan()

		images = []
		next_start = 0

		for end in self._end_points:

			current_start = next_start
			next_start = end

			if end-current_start < self._minimum_size: continue

			image = numpy.zeros((self._image.shape[0], end-current_start))
			for x in range(current_start, end):
				for y in range(0, self._image.shape[0]):
					image[y][x-current_start] = self._image[y][x]

			images.append(image)

		return images


if __name__ == "__main__":
	from sys import argv
	from scipy.misc import imshow
	
	# Hack to run on Scipy > 0.7
	try: from scipy.misc import imread
	except: from scipy.ndimage import imread

	if len(argv) < 2:
		raise Exception("Usage: ./wordslice recaptcha.jpeg");
	for i in WordSlice(imread(argv[1], True)).get_words():
		imshow(i)
