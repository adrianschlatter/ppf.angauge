from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from skimage.color import rgb2hsv
from skimage.filters import threshold_local

__all__ = []


def to_gray(img: NDArray,
            c0: float, c1: float, c2: float, c3: float) -> NDArray:
    """
    Convert RGB image to grayscale using weighted HSV components.

    Args:
        img: Input RGB image as numpy ndarray of shape (h, w, 3)
        c0, c1, c2, c3: Weights for constant term, H, S, V components

    Returns:
        Grayscale image as numpy ndarray of shape (h, w) with dtype 'uint8'
    """
    img_hsv = rgb2hsv(img / 256.)
    img_gray = (c0
                + c1 * img_hsv[:, :, 0]
                + c2 * img_hsv[:, :, 1]
                + c3 * img_hsv[:, :, 2])
    return np.clip(img_gray * 256, 0, 255).astype('uint8')


def to_bw(img_gray: NDArray, method: str, offset: float,
          blocksize: int = None, invert: bool = False) -> NDArray:
    """
    Binarize grayscale image using global or local thresholding.

    Args:
        img_gray: Input grayscale image as numpy ndarray of shape (h, w)
        method: 'global' for global thresholding, 'local' for local
                thresholding
        offset: Offset value for thresholding
        blocksize: Size of the local neighborhood for local thresholding
                   (ignored for global thresholding)

    Returns:
        Binarized image as numpy ndarray of shape (h, w) with dtype 'bool'
    """
    if method == 'global':
        img_bw = img_gray > offset
    elif method == 'local':
        local_thresh = threshold_local(img_gray,
                                       block_size=blocksize, offset=offset)
        img_bw = img_gray > local_thresh
    else:
        raise ValueError(f'Unknown binarization method: {method}')

    return img_bw if not invert else ~img_bw


def to_polar(img: NDArray, n_r: int, n_theta: int,
             r_min: float, r_max: float) -> NDArray:
    h_half, w_half = 0.5 * img.shape[0], 0.5 * img.shape[1]
    h_max, w_max = img.shape[0] - 1, img.shape[1] - 1
    r = np.linspace(r_min, r_max, n_r, endpoint=True).reshape(-1, 1)
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False).reshape(1, -1)

    # precompute sine and cosine tables:
    sine_table = np.sin(theta)
    cosine_table = np.cos(theta)

    X = np.clip(np.round(w_half + r * sine_table), 0, w_max).astype(int)
    Y = np.clip(np.round(h_half - r * cosine_table), 0, h_max).astype(int)

    return img[Y, X]


def flood_fill(img: NDArray,
               points: set[tuple[int, int]]) -> NDArray[bool]:

    def uncover(pnt: tuple[int, int]) -> bool:
        i, j = pnt
        scanned.add(pnt)
        return img[i, j]

    scanned = set()
    h, w = img.shape

    while points != set():
        hits = [pnt for pnt in points - scanned if uncover(pnt)]
        points = set()
        for (di, dj) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i, j in hits:
                if 0 <= i + di < h:
                    points.add((i + di, (j + dj) % w))

    return scanned
