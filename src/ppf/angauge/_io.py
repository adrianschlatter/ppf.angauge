from __future__ import annotations
import mmap
import struct
import numpy as np
from ._utils import export

try:
    import tomllib
except ModuleNotFoundError:                                 # pragma: no cover
    try:                                                    # pragma: no cover
        import tomli as tomllib                             # pragma: no cover
    except ImportError:                                     # pragma: no cover
        raise ImportError(                                  # pragma: no cover
          'This package requires either tomllib or tomli')  # pragma: no cover


def normalize_indicator_cfg(local_cfg, global_cfg):
    """
    Inherit properties in local_cfg from global_cfg if missing. Ensure no
    missing required properties.
    """
    # inherit properties local <= global <= default:
    for prop in ['hsv_to_gray', 'gray_to_bw', 'phi', 'theta_min',
                 'theta_range', 'value_min', 'value_max']:
        local_cfg[prop] = local_cfg.get(prop, global_cfg.get(prop, None))
        if local_cfg[prop] is None:
            del local_cfg[prop]

    # check that all required properties are present:
    for prop in ['hsv_to_gray', 'gray_to_bw']:
        if prop not in local_cfg:
            raise ValueError(f"Missing '{prop}' key in config file")


@export
def read_config(config_path: str) -> list[dict]:
    """
    Read TOML configuration file.

    The configuration file specifies:

    * for each indicator:
        - position (upper-left corner)
        - rotation
        - size (of square)
        - sine- and cosine correction coefficients
    * HSV to grayscale conversion coefficients
    * Grayscale to black-and-white conversion method and parameters
    * Multiplier for the finest indicator

    Parameters
    ----------

    config_path (str): Path to the configuration file.


    Returns
    -------

    dict:
        Dictionary with keys (if present in file): 'hsv_to_gray',
        'gray_to_bw', 'multiplier', 'indicators'.

        'indicators' is a list of dictionaries, each containing the keys 'x0',
        'y0', 'w', 'phi', 'Asin', 'Acos'.

        'hsv_to_gray' is a dictionary with keys 'c0', 'c1', 'c2', 'c3', the
        multiplier coefficients for 1, H, S, and V components.

        'gray_to_bw' is a dictionary with keys 'method', 'offset', 'blocksize',
        specifying the binarization method and parameters.

        Note: It will also return any other object found in the toml file, even
        though not used by the package.
    """
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)

    # normalize config

    # we either have a single_gauge or multi_gauge config:
    if 'indicator' in config and 'indicators' in config:
        raise ValueError("Config file cannot contain both 'indicator' and "
                         "'indicators' keys")
    elif 'indicator' not in config and 'indicators' not in config:
        raise ValueError("Neither 'indicator' nor 'indicators' key "
                         "found in config file")
    elif 'indicator' in config:
        normalize_indicator_cfg(config['indicator'], config)
    else:  # multi_gauge config:
        for i, indicator in enumerate(config['indicators']):
            normalize_indicator_cfg(config['indicators'][i], config)

    for prop in ['hsv_to_gray', 'gray_to_bw', 'phi', 'theta_min',
                 'theta_range', 'value_min', 'value_max']:
        if prop in config:
            del config[prop]

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
