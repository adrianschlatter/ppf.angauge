import mmap
import struct
import numpy as np


def read_bmp_rectangle(file_path: str,
                       x: int, y: int, w: int, h: int) -> np.memmap:
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

            row_size = ((img_width * 3 + 3) // 4) * 4  # row size with padding
            image_mm = np.memmap(
                            file_path, dtype=np.uint8, mode='r', offset=offset,
                            shape=(img_height, row_size))
            sub_mm = image_mm[img_height - y - h:img_height - y,
                              x * 3:(x + w) * 3]
            rgb_mm = sub_mm.reshape(h, w, 3)[::-1, :, ::-1]

            return rgb_mm


def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """
    Convert RGB values to HSV.

    Parameters:
    rgb : ndarray
        An array of RGB values with shape (..., 3) and values in [0, 1].

    Returns:
    ndarray
        An array of HSV values with the same shape as the input, except
        the last dimension is still 3 (for H, S, V).
    """
    # Extract R, G, B channels
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]

    # Compute maximum and minimum values
    mx = np.maximum(np.maximum(r, g), b)  # Value (V)
    mn = np.minimum(np.minimum(r, g), b)
    delta = mx - mn  # Difference

    # Compute Saturation (S)
    s = np.where(mx == 0, 0, delta / mx)

    # Compute Hue (H)
    h = np.zeros_like(r)  # Initialize H array

    # Masks for the cases where R, G, or B is the maximum
    mask_r = (mx == r) & (delta > 0)
    mask_g = (mx == g) & (delta > 0)
    mask_b = (mx == b) & (delta > 0)

    h[mask_r] = (g[mask_r] - b[mask_r]) / delta[mask_r]
    h[mask_g] = 2.0 + (b[mask_g] - r[mask_g]) / delta[mask_g]
    h[mask_b] = 4.0 + (r[mask_b] - g[mask_b]) / delta[mask_b]

    h = (h % 6.0) / 6.0  # Scale H to [0, 1]

    # Stack H, S, V into the output array
    hsv = np.stack([h, s, mx], axis=-1)  # mx is V

    return hsv


def to_handscale(img: np.ndarray) -> np.ndarray:
    """
    Convert to grayscale showing bright hand on dark background.

    Args:
        img (numpy.ndarray): The input image.
    Returns:
        numpy.ndarray: The processed image in hand scale.
    """
    h = rgb_to_hsv(img / 255.)[:, :, 0]

    return np.clip((h - 0.71) / (1 - 0.71), 0., 1.)
