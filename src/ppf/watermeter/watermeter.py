import numpy as np
from .image_processing import read_bmp_rectangle, to_handscale, cog


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
