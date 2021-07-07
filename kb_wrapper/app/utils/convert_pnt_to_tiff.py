import glob
from PIL import Image
import tifffile
import numpy


def PIL2array(img):
    """Convert a PIL/Pillow image to a numpy array"""
    return numpy.array(img.getdata(), numpy.uint8).reshape(img.size[1], img.size[0], 3)


FRAMES = []
FIRST_SIZE = None
OUT_NAME = "/workspace/others/assets/tiff_register/generation_multipagetiff.tiff"
filelist = glob.glob("/workspace/others/assets/tiff_register/*.png")

for fn in filelist:
    img = Image.open(fn)
    if FIRST_SIZE is None:
        FIRST_SIZE = img.size
    if img.size == FIRST_SIZE:
        print("Adding:", fn)
        FRAMES.append(img)
    else:
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
