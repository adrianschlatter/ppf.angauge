import numpy as np
from .image_processing import read_bmp_rectangle, to_handscale, cog
from typing import Callable


def to_polar(img_hand: np.ndarray) -> np.ndarray:
    """
    Convert hand image to polar coordinates.
    """

    r_max = min(img_hand.shape) / 2.
    x_pixel = np.arange(img_hand.shape[1]) - img_hand.shape[1] / 2
    y_pixel = img_hand.shape[0] / 2 - np.arange(img_hand.shape[0])
    r2_pixel = x_pixel[None, :]**2 + y_pixel[:, None]**2

    try:
        c_x, c_y = cog(img_hand * (r2_pixel >= (0.35 * r_max)**2))
    except ValueError:
        raise ValueError("Failed to compute center of gravity of hand image")

    mu_theta = np.arctan2(c_x, c_y)
    r_min = 14/40 * r_max
    r = np.linspace(r_min, r_max, img_hand.shape[0], endpoint=False)
    theta = np.linspace(mu_theta - np.pi / 2, mu_theta + np.pi / 2,
                        img_hand.shape[1])
    X = r[:, None] * np.sin(theta[None, :]) + img_hand.shape[1] / 2
    Y = img_hand.shape[0] / 2 - r[:, None] * np.cos(theta[None, :])
    img_polar = img_hand[Y.astype(int), X.astype(int)]

    return img_polar, theta, mu_theta


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


class ImageFunction:

    def __init__(self, img: np.ndarray, n_r: int, n_theta: int,
                 r_min: float, r_max: float, threshold: float):
        self.img = img
        self.n_r, self.n_theta = n_r, n_theta
        self.r_min, self.r_max = r_min, r_max
        self.threshold = threshold
        self.dr = (r_max - r_min) / self.n_r
        self.dtheta = 2 * np.pi / self.n_theta

        self.sum_i_y = self.sum_i_x = 0.
        self.sum_count = 0.
        self.theta_distrib = np.zeros(n_theta, dtype='float')

    def __call__(self, i_r: int, i_theta: int) -> bool:
        # convert polar pixel numbers to (r, theta):
        r = self.r_min + i_r * self.dr
        theta = i_theta * self.dtheta

        # convert polar to cartesian:
        x = r * np.sin(theta) + 0.5 * self.img.shape[1]
        y = 0.5 * self.img.shape[0] - r * np.cos(theta)

        # convert to pixel indices:
        i_y = max(0, min(self.img.shape[0] - 1, round(y)))
        i_x = max(0, min(self.img.shape[1] - 1, round(x)))

        # lookup pixel in original image:
        rgb = self.img[i_y, i_x]

        # convert to grayscale:
        # value = to_handscale(rgb)
        value = rgb

        # is this a bright pixel?
        is_bright = value > self.threshold

        # accumulate center of gravity sums:
        self.sum_i_y += i_y * value
        self.sum_i_x += i_x * value
        self.sum_count += value

        # accumulate theta distribution for std dev calculation:
        self.theta_distrib[i_theta] += value

        # lookup pixel in image and compare to threshold:
        return is_bright

    def cog(self) -> tuple[float, float]:
        if self.sum_count == 0:
            raise ValueError("No bright pixels found!")
        return (self.sum_i_y / self.sum_count, self.sum_i_x / self.sum_count)


def hand2digit(img_hand: np.ndarray) -> tuple[float, float]:
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
    # rmin: avoid seeing tail of the hand
    rmin, rmax = 18/40, 1.0  # relative to half image size
    rimg = min(img_hand.shape) / 2
    n_r, n_theta = 32, 64

    func = ImageFunction(img_hand, n_r, n_theta,
                         rmin * rimg, rmax * rimg,
                         threshold=0.5 * img_hand.max())

    # starting points for flood fill: all points at minimum radius:
    points = set((0, j) for j in range(n_theta))

    # process all (hand-) pixels connected to starting points:
    flood_fill(func, points)

    # retrieve center of gravity in cartesian coordinates:
    c_y, c_x = func.cog()

    # derive hand angle:
    mu_theta_init = np.arctan2(c_x - img_hand.shape[1] / 2,
                               img_hand.shape[0] / 2 - c_y)

    # j_index of center of gravity in polar coordinates:
    j_mu = round((mu_theta_init % (2 * np.pi)) / (2 * np.pi) * n_theta)

    # get theta distribution shifted so that mu_theta is at center index:
    theta_dist = np.roll(func.theta_distrib, -j_mu + n_theta // 2)

    # corresponding theta axis:
    theta_axis = np.linspace(mu_theta_init - np.pi, mu_theta_init + np.pi,
                             n_theta, endpoint=False)

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
        img_clock = read_bmp_rectangle(
                        image_path, cfg['x0'], cfg['y0'], cfg['w'], cfg['w'])
        img_hand = to_handscale(img_clock)
        # img_hand = img_clock
        try:
            theta, dtheta = hand2digit(img_hand)
        except ValueError:
            raise ValueError(
                    f"Failed to read clock {i}" f"in image {image_path}")
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
