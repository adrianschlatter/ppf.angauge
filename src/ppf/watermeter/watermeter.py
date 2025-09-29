import numpy as np
from typing import Tuple
from .image_processing import read_bmp_rectangle, to_handscale, cog


def hand2digit(img_hand) -> Tuple[float, float]:
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
        Estimated angle of the indicator as a digit [0, 10[.

    sigma_theta : float
        Estimated standard deviation of the angle in digit units [0, 10[.

    Raises
    ------

    ValueError :
        If the center of gravity cannot be computed or if there is a division
        by zero during the calculation of the standard deviation. Both happen
        if the input image is (almost) completely black (no indicator
        detected).
    """

    try:
        c_x, c_y = cog(img_hand)
    except ValueError:
        raise ValueError("Failed to compute center of gravity of hand image")

    mu_theta = np.arctan2(c_x, c_y)
    r_max = min(img_hand.shape) / 2.
    r_min = 14/40 * r_max
    r = np.linspace(r_min, r_max, img_hand.shape[0])
    theta = np.linspace(mu_theta - np.pi / 2, mu_theta + np.pi / 2,
                        img_hand.shape[1])
    X = r[:, None] * np.sin(theta[None, :]) + img_hand.shape[1] / 2
    Y = img_hand.shape[0] / 2 - r[:, None] * np.cos(theta[None, :])
    img_polar = img_hand[Y.astype(int), X.astype(int)]

    # center of gravity in polar coordinates:
    c_theta, c_r = cog(img_polar)
    c_theta *= np.pi / len(theta)

    # update estimate of hand angle:
    mu_theta += c_theta

    # get the std dev in angle
    dtheta = theta - c_theta
    theta_polar = img_polar.sum(axis=0)
    theta_polar_sum = theta_polar.sum()
    if theta_polar_sum == 0:
        raise ValueError("theta_polar.sum() is zero!")
    sigma_theta = np.sqrt((dtheta**2 * theta_polar).sum() / theta_polar_sum)
    sigma_theta = np.pi / len(theta)

    return (mu_theta, sigma_theta)


def read_meter(image_path, config):
    """
    Reads a meter image and extracts the meter reading.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Extracted meter reading.
    """
    reading = {}
    for clock_exponent, cfg in config.items():
        img_clock = read_bmp_rectangle(
                        image_path, cfg['x0'], cfg['y0'], cfg['w'], cfg['w'])
        img_hand = to_handscale(img_clock)
        try:
            theta, dtheta = hand2digit(img_hand)
        except ValueError:
            raise ValueError(
                    f"Failed to read clock {clock_exponent}"
                    f"in image {image_path}")
        # compensate known rotation of clock:
        theta += cfg['phi'] / 180. * np.pi
        # convert to digit:
        digit = theta / 2 / np.pi * 10
        ddigit = dtheta / 2 / np.pi * 10
        digit = digit % 10

        reading[clock_exponent] = (digit, ddigit)

    # convert to numpy recarray:
    dt = np.dtype([('pow', 'i4'), ('value', 'f4'), ('sigma', 'f4')])
    rec_array = np.recarray((len(reading),), dtype=dt)
    lst = []
    for pow, (mu, sigma) in reading.items():
        lst.append((pow, mu, sigma))
    lst.sort(reverse=True)  # sort by pow
    for i, (pow, mu, sigma) in enumerate(lst):
        rec_array[i] = (pow, mu, sigma)

    return rec_array
