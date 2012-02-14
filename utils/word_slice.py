#!/usr/bin/env python
__all__ = ["WordSlice"]

class WordSlice:
    def __init__(self, image, separator=8, threshold=127, minimum_size=15):
        self.image = image
        self.threshold = threshold
        self.separator = separator
        self.minimum_size = minimum_size
        self.current_start = 0
        self.end_points = iter(self.scan())

    def scan(self):
        end_points = []
        had_content = False

        height, width = self.image.shape[0:2]

        for x in xrange(width):
            # This Y line has content?
            content = False
            for y in range(height):
                if self.image[y,x] < self.threshold:
                    content = True

            # If yes, this is not blank.
            if content:
                empty_line = 0
                had_content = True
                continue

            if not had_content:
                continue

            empty_line += 1
            if empty_line == self.separator:
                end_points.append(x)
                had_content = False

        if had_content:
            end_points.append(height)

        return end_points

    def __iter__(self):
        return self

    def next(self): #@ReservedAssignment

        data = None
        while data is None:

            end = self.end_points.next()

            if end - self.current_start > self.minimum_size:
                data = self.image[:, self.current_start:end]

            self.current_start = end

        return data

if __name__ == "__main__":
    from sys import argv
    from scipy.misc import imshow
    from scipy.ndimage import imread

    if len(argv) < 2:
        raise Exception("Usage: ./wordslice recaptcha.jpeg")

    for i in WordSlice(imread(argv[1], True)):
        imshow(i)
