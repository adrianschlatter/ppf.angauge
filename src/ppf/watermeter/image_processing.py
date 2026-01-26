from __future__ import annotations
import numpy as np
from skimage.color import rgb2hsv
from skimage.filters import threshold_local


def to_handscale(r: int, g: int, b: int) -> int:
    """
    Convert to grayscale showing bright hand on dark background.

    Args:
        r, g, b (int): RGB triplet in 2**-8 fixed point.
    Returns:
        hs: processed value in hand scale (2**-8 fixed point)
    """

    r, g, b = map(int, (r, g, b))               # * 2**-8
    r, g, b = r << 8, g << 8, b << 8            # * 2**-16

    # Compute maximum and minimum values
    mx = max(r, max(g, b))                      # * 2**-16
    mn = min(r, min(g, b))                      # * 2**-16
    delta = mx - mn                             # * 2**-16

    # Compute Hue (H)
    if delta > 0:
        r, g, b = r << 5, g << 5, b << 5        # * 2**-21
        mx = mx << 5                            # * 2**-21
        delta = delta >> 5                      # * 2**-11
        if mx == r:
            h = (g - b) // delta                # * 2**-10
        elif mx == g:
            h = (2 << 10) + (b - r) // delta    # * 2**-10
        else:  # mx == b
            h = (4 << 10) + (r - g) // delta    # * 2**-10

        h = ((h << 6) % (6 << 16)) // 6         # * 2**-16
    else:
        h = 0                                   # * 2**-16

    # 0.71 in 2**-16 fixed point: 46530
    # (1 - 0.71) in 2**-8 fixed point: 74
    handscale = (h - 46530) // 74               # * 2**-8

    return 0 if handscale <= 0 else handscale   # * 2**-8


def to_gray(img: np.ndarray,
            c0: float, c1: float, c2: float, c3: float) -> np.ndarray:
    """
    Convert RGB image to grayscale using weighted HSV components.

    Args:
        img: Input RGB image as numpy ndarray of shape (h, w, 3)
        c0, c1, c2, c3: Weights for constant term, H, S, V components

    Returns:
        Grayscale image as numpy ndarray of shape (h, w) with dtype 'uint8
    """
    img_hsv = rgb2hsv(img / 256.)
    img_gray = (c0
                + c1 * img_hsv[:, :, 0]
                + c2 * img_hsv[:, :, 1]
                + c3 * img_hsv[:, :, 2])
    return np.clip(img_gray * 256, 0, 255).astype('uint8')


def to_bw(img_gray: np.ndarray, method: str, offset: float,
          blocksize: int = None, invert: bool = False) -> np.ndarray:
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


def to_polar(img: np.ndarray, n_r: int, n_theta: int,
             r_min: float, r_max: float) -> np.ndarray:
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


class VirtualImage:
    """
    A VirtualImage represents an image in polar coordinates

    It behaves like a (read-only) 2D numpy array of booleans but it actually
    computes its pixels on-the-fly from a given cartesian image.

    Also, it accumulates a theta distribution of all pixel values accessed via
    __getitem__.
    """

    def __init__(self, img: np.ndarray, n_r: int, n_theta: int,
                 r_min: float, r_max: float, threshold: float):
        self.img = img
        self.h_half, self.w_half = 0.5 * img.shape[0], 0.5 * img.shape[1]
        self.h_max, self.w_max = img.shape[0] - 1, img.shape[1] - 1
        self.n_r, self.n_theta = n_r, n_theta
        self.r_min, self.r_max = r_min, r_max
        self.dr = (r_max - r_min) / self.n_r
        self.dtheta = 2 * np.pi / self.n_theta
        self.threshold = threshold

        self.theta_distrib = np.zeros(n_theta, dtype='float')

        # precompute sine and cosine tables:
        theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
        self.sine_table = np.sin(theta)
        self.cosine_table = np.cos(theta)

    def __getitem__(self, key: tuple[int, int]) -> bool:
        i_r, i_theta = key

        # convert polar pixel numbers to (r, theta):
        r = i_r * self.dr + self.r_min

        # convert polar to cartesian:
        x = self.w_half + r * self.sine_table[i_theta]
        y = self.h_half - r * self.cosine_table[i_theta]

        # convert to pixel indices:
        i_y = max(0, min(self.h_max, round(y)))
        i_x = max(0, min(self.w_max, round(x)))

        # lookup pixel in original image and convert to grayscale:
        value = to_handscale(*self.img[i_y, i_x])

        # accumulate theta distribution for std dev calculation:
        self.theta_distrib[i_theta] += value

        # return whether pixel is above threshold:
        return value > self.threshold

    @property
    def shape(self) -> tuple[int, int]:
        return (self.n_r, self.n_theta)


def flood_fill(img: np.ndarray,
               points: set[tuple[int, int]]) -> np.ndarray[bool]:

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
