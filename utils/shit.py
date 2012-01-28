import sys
from PIL import Image,ImageFilter, ImageDraw
from math import *
from scipy.misc import imshow

# some global constants
EL_COVERAGE_RATIO = 0.9
EL_VERIFICATION_DISTANCE = 1.
EL_PATH_POINTS = 51
MIN_MINOR_FREQUENCY = 30
MIN_HALF_MAJOR = 8
MIN_HALF_MINOR = 6

def distance(p1,p2):
 x1,y1 = p1
 x2,y2 = p2
 return sqrt((x1-x2)**2 + (y1-y2)**2)

def nonnegative(v):
 return v if v >= 0 else 0

def parametricEllipse(center, a, b, angle):
 xc,yc = center
 elx = lambda t: xc + a * cos(t) * cos(angle) - b * sin(t) * sin(angle)
 ely = lambda t: yc + a * cos(t) * sin(angle) + b * sin(t) * cos(angle)
 return [(int(elx(2.*pi*x/float(EL_PATH_POINTS-1))),int(ely(2.*pi*x/float(EL_PATH_POINTS-1)))) for x in range(EL_PATH_POINTS)]

assert len(sys.argv)!=2, "missing input and/or output file !"

im = Image.open(sys.argv[1])
width, height = im.size
io = Image.new('RGB',(width, height),(255,255,255))
draw = ImageDraw.Draw(io)

# converting image to grayscale
im = im.convert('L')

# detecting edge pixels
im = im.filter(ImageFilter.FIND_EDGES)

# converting to binary image
im = im.convert('1')
pixels = im.load()
pxy = []

# extracting binary pixels coordinates
for x in range(width):
 for y in range(height):
  if pixels[x,y]==255:
   pxy.append((x,y))

# applying Hough transform for ellipses detection.
# algorithm is taken from this paper:
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.1.8792&rep=rep1&type=pdf
cIx = -1
colors = [(255,0,0),(0,200,0),(0,0,255)]
for x1,y1 in pxy:
  for x2,y2 in pxy:
    bbins = {}
    dist = distance((x1,y1),(x2,y2))
    if dist >= 2*MIN_HALF_MAJOR:
     cent = ((x1+x2)/2.,(y1+y2)/2.)
     a = dist/2. # semi-length of major axis
     alfa = atan2((y2 - y1),(x2 - x1))
     for rx,ry in pxy:
      d = distance((rx,ry),cent)
      if d >= MIN_HALF_MINOR:
       f = distance((rx,ry),(x2,y2))
       cost = (a**2. + d**2. - f**2.)/(0.00001+2.*a*d)
       b = sqrt(nonnegative((a**2. * d**2. * (1.-cost**2.))/(0.00001 + a**2. - d**2. * cost**2.)))  # semi-length of minor axis
       b = int(b)
       if bbins.has_key(b):
        bbins[b]+=1
       elif b > 0:
        bbins[b]=1
     bbins_rev = dict([(v,k) for k,v in bbins.iteritems()])
     max_freq = max(bbins_rev.keys())
     bmax = bbins_rev[max_freq]
     # Did we found probable ellipse ?
     if max_freq >= MIN_MINOR_FREQUENCY and alfa >=0.0 and bmax >= MIN_HALF_MINOR:
      elData = parametricEllipse(cent, a, bmax, alfa)
      supported = []
      supportRatio = 0.0
      # counting how much pixels lies on ellipse path
      for i in range(EL_PATH_POINTS):
       elx,ely = elData[i]
       added = False
       for x,y in pxy:
        if distance((elx,ely),(x,y)) <= EL_VERIFICATION_DISTANCE:
         supported.append((x,y))
         if not added:
          supportRatio += 1./float(EL_PATH_POINTS)
          added = True
      supported = list(set(supported))
      # if number of pixels on ellipse path is big enough
      if supportRatio >= EL_COVERAGE_RATIO:
       cIx = (cIx+1)%3
       print "coverage %.2f" % supportRatio,"frequency ", max_freq, "center ", cent, "angle %.2f" % alfa, "axes (%.2f,%.2f)" % (a, bmax)
       # removing founded ellipse pixels from further analysis
       for p in supported:
        pxy.remove(p)
       # drawing founded ellipse
       for i in range(EL_PATH_POINTS):
        elx,ely = elData[i]
        if i < EL_PATH_POINTS-1:
         draw.line(elData[i] + elData[i+1], fill=colors[cIx])
io.save(sys.argv[2])
print "***************************************************************"
print "************************** DONE *******************************"
print "***************************************************************"
