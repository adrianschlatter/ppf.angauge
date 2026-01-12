import numpy as np


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


def flood_fill(img: np.ndarray | VirtualImage,
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

    # useful for diagnostics:
    return scanned
