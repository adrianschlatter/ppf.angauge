import numpy as np
from typing import Callable
from .image_processing import to_handscale
from .io import read_bmp_rectangle


def flood_fill(func: Callable[[int, int], bool],
               points: set[tuple[int, int]]) -> np.ndarray[bool]:

    def uncover(pnt: tuple[int, int]) -> bool:
        i, j = pnt
        scanned.add(pnt)
        return func(i, j)

    scanned = set()
    h, w = func.n_r, func.n_theta

    while points != set():
        hits = [pnt for pnt in points - scanned if uncover(pnt)]
        points = set()
        for (di, dj) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i, j in hits:
                if 0 <= i + di < h:
                    points.add((i + di, (j + dj) % w))

    # useful for diagnostics:
    return scanned, func.theta_distrib


class ImageFunction:

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

    def __call__(self, i_r: int, i_theta: int) -> bool:
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


def read_indicator(img_hand: np.ndarray) -> tuple[float, float]:
    """
    Convert image of indicator to digit and its uncertainty.

    Parameters
    ----------

    img_hand :
        2D numpy array
        Image of the hand in grayscale (bright hand on dark background).

    Returns
    -------

    mu_theta : float
        Estimated angle of the indicator in radians [0, 2*pi[.

    sigma_theta : float
        Estimated standard deviation of the angle in radians [0, 2*pi[.

    Raises
    ------

    ValueError :
        If the center of gravity cannot be computed or if there is a division
        by zero during the calculation of the standard deviation. Both happen
        if the input image is (almost) completely black (no indicator
        detected).
    """

    # define grid in polar coordinates:
    # rmax: don't go outside image
    # rmin: larger than half of the hand's width (so that front- and back-side
    # of hand are separated in theta)
    rimg = min(img_hand.shape[:2]) / 2
    rmin, rmax = 0.25, 1.0  # relative to half image width
    n_r, n_theta = 16, 32
    threshold = 128

    func = ImageFunction(img_hand, n_r, n_theta,
                         rmin * rimg, rmax * rimg,
                         threshold=threshold)

    # starting points for flood fill: all points at minimum radius:
    points = set((0, j) for j in range(n_theta))

    # process all (hand-) pixels connected to starting points:
    flood_fill(func, points)

    # find peak of theta distribution:
    j_mu = np.argmax(func.theta_distrib)
    theta_peak = j_mu * 2 * np.pi / n_theta

    # shift theta distribution so that theta_peak is at center of left half:
    theta_dist = np.roll(func.theta_distrib, -j_mu + n_theta // 4)
    # if the back-end of the hand is visible, it is now close to the center of
    # the right half; add both halves to a) improve statistics and b) avoid
    # problems with mu calculation of a distribution with 2 peaks:
    theta_dist = theta_dist[:n_theta // 2] + theta_dist[n_theta // 2:]

    # corresponding theta axis:
    theta_axis = np.linspace(theta_peak - 0.5 * np.pi,
                             theta_peak + 0.5 * np.pi,
                             n_theta // 2, endpoint=False)

    mu_theta = (theta_dist * theta_axis).sum() / theta_dist.sum()
    sigma_theta = np.sqrt(
                        ((theta_dist * (theta_axis - mu_theta)**2).sum()
                         / theta_dist.sum()))

    return (mu_theta % (2 * np.pi), sigma_theta)


def read_meter(image_path: str, config: list[dict]) -> list[dict]:
    """
    Read meter image and extract reading of each indicator.

    Parameters
    ----------

    image_path : str
        path of image to read (.bmp file format)

    config : List[Dict]
        Configuration for clock positions, as returned by read_config().

    Returns
    -------

    list of dict:
        List of dictionaries, each containing 'mu' and 'sigma'
        for each clock in the meter. 'mu' is the estimated digit value, 'sigma'
        is the estimated uncertainty.
    """
    reading = []
    for i, cfg in enumerate(config):
        img_indicator = read_bmp_rectangle(
                        image_path, cfg['x0'], cfg['y0'], cfg['w'], cfg['w'])
        try:
            theta, dtheta = read_indicator(img_indicator)
        except ValueError:
            raise ValueError(
                    f"Failed to read clock {i} in image {image_path}")
        # compensate known rotation of clock:
        theta += cfg['phi'] / 180. * np.pi

        # compensate elliptical distortion:
        theta += cfg['Asin'] * np.sin(theta)
        theta += cfg['Acos'] * np.cos(theta)

        # convert to digit:
        digit = theta / 2 / np.pi * 10
        ddigit = dtheta / 2 / np.pi * 10
        digit = digit % 10

        reading.append({'value': digit, 'sigma': ddigit})

    return reading
