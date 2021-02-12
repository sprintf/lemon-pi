
import sys
import os
from PIL import Image


def crop(file):
    im:Image.Image = Image.open(file)
    width, height = im.size

    print('original size = {},{}'.format(width, height))

    crop = im.crop((32, 51, width - 64, height - 100))

    file, ext = os.path.splitext(file)
    crop.save("{}-clipped.jpg".format(file), "JPEG")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("need a filename")
        sys.exit(0)

    file = sys.argv[1]
    crop(file)

