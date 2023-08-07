from glob import glob
import os

for f in glob("./products_image/*.jpg"):
    try:
        os.remove(f)
    except OSError as e:
        print("f[ERROR] {f} {e.strerror}")

