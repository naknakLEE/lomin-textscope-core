import glob
import numpy
import tifffile
from PIL import Image


def PIL2array(img):
    """Convert a PIL/Pillow image to a numpy array"""
    return numpy.array(img.getdata(), numpy.uint8).reshape(img.size[1], img.size[0], 3)


FRAMES = []
FIRST_SIZE = None
OUT_NAME = "./others/assets/tiff_register/kbcard_multipagetiff.tiff"
filelist = glob.glob("./others/assets/kbcard/**/*.png")

for fn in filelist:
    import numpy as np

    img = Image.open(fn)
    if FIRST_SIZE is None:
        FIRST_SIZE = img.size
    if img.size == FIRST_SIZE:
        print("Adding:", fn)
        FRAMES.append(img)
    else:
        base_w, base_h = FIRST_SIZE
        img = np.array(img)
        h, w, c = img.shape
        canvas = np.ones(shape=(base_h, base_w, c)) * 255
        canvas[:h, :w] = img
        FRAMES.append(Image.fromarray(img))
        print("Discard:", fn, img.size, "<>", FIRST_SIZE)


print("Frames:", len(FRAMES))
print("Writing", len(FRAMES), "frames to", OUT_NAME)
with tifffile.TiffWriter(OUT_NAME) as tiff:
    for img in FRAMES:
        tiff.write(PIL2array(img), photometric="rgb")

with tifffile.TiffFile(OUT_NAME) as tif:
    for page in tif.pages:
        print(page.shape)

print("Done")
