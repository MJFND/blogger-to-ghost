from pathlib import Path
from PIL import Image
import glob

"""
Conver Images to webp post download
"""

PATH = "../images"
paths = Path(PATH).glob("*/*")
for source in paths:
    destination = source.with_suffix(".webp")
    image = Image.open(source)
    image.save(destination, format="webp")
    print(f"image saved at {destination}")