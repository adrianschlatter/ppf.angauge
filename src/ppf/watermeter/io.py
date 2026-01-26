from __future__ import annotations
import mmap
import struct
import numpy as np

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError('This package requires either tomllib or tomli')


def read_config(config_path: str) -> list[dict]:
    """
    Reads the configuration file for clock positions.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        list of dict: A list of dictionaries, each containing the keys 'x0',
        'y0', 'w', and 'phi'. Index in list is the clock index: Lowest-value
        clock is index 0, next is index 1, etc.
    """
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)

    return config


def read_bmp_rectangle(file_path: str, x: int = 0, y: int = 0,
                       w: int = 0, h: int = 0) -> np.memmap:
    """
    Returns memory-mapped array of rectangle (x,y,w,h) of BMP file.
    """
    with open(file_path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            file_header = struct.unpack('<2sIHHI', mm[0:14])
            offset = file_header[4]
            dib_header = struct.unpack('<IiiHH', mm[14:14+16])
            img_width = dib_header[1]
            img_height = dib_header[2]
            bits_per_pixel = dib_header[4]

            if bits_per_pixel != 24:
                raise ValueError("Only 24-bit BMP supported")

            if x < 0 or y < 0 or x + w > img_width or y + h > img_height:
                raise ValueError("Rectangle out of bounds")

            if w == 0:
                w = img_width
            if h == 0:
                h = img_height

            row_size = ((img_width * 3 + 3) // 4) * 4  # row size with padding
            image_mm = np.memmap(
                            file_path, dtype=np.uint8, mode='r', offset=offset,
                            shape=(img_height, row_size))
            sub_mm = image_mm[img_height - y - h:img_height - y,
                              x * 3:(x + w) * 3]
            rgb_mm = sub_mm.reshape(h, w, 3)[::-1, :, ::-1]

            return rgb_mm
