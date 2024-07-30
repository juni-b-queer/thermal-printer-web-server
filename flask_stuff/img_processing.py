import math

import PIL
from PIL import Image

from flask_stuff.utils import getFilenameWithoutExtension


def resizeImage(path, width=0, height=0):
    importedImage = Image.open(path)
    w, h = importedImage.size
    gcd = math.gcd(w, h)
    wratio = w/gcd
    hratio = h/gcd
    wMax = width/wratio
    hMax = height/hratio
    mult = min(wMax, hMax)
    newWidth = math.ceil(wratio*mult)
    newHeight = math.ceil(hratio*mult)
    im = importedImage.resize((newWidth, newHeight))
    im = im.rotate(-90, PIL.Image.NEAREST, expand = 1)
    return im


def convertJpgToBmp(filename):
    path = './static/uploads/' + filename
    resizedImage = resizeImage(path , 640, 360)
    im = resizedImage.convert('1')
    im.save("./static/converted/" + getFilenameWithoutExtension(filename) + ".bmp")
    return True