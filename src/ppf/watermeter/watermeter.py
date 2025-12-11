import numpy as np
from .image_processing import flood_fill, VirtualImage
from .io import read_bmp_rectangle


def read_indicator(img_hand: np.ndarray) -> tuple[float, float]:
    """
    Estimate angle of hand and error bare from image of an indicator
    (=dial and hand).

    It does this by detecting the hand in polar coordinates using a
    flood-fill-like algorithm to find all connected hand pixels starting
    from the center of the dial. From the detected hand pixels, a
    distribution of pixel intensities over angle is computed, from which
    the mean angle and standard deviation is calculated.

    Note: It does not analyze the dial: It determines the clockwise angle of
    the hand relative to the image's upward direction. If the dial's 0
    direction is not aligned with the image's upward direction, this must be
    compensated for later.

    Parameters
    ----------

    img_hand :
        Image (2D numpy array) of an indicator (dial and hand).

    Returns
    -------

    mu_theta : float
        Estimated angle of the indicator in radians [0, 2*pi[.

    sigma_theta : float
        Estimated standard deviation of the angle in radians.
    """

    # define grid in polar coordinates:
    # rmax: don't go outside image
    # rmin: larger than half of the hand's width (so that front- and back-side
    # of hand are separated in theta)
    rimg = min(img_hand.shape[:2]) / 2
    rmin, rmax = 0.25, 1.0  # relative to half image width
    n_r, n_theta = 16, 32
    threshold = 128

    func = VirtualImage(img_hand, n_r, n_theta, rmin * rimg, rmax * rimg,
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
    Reads state of a meter with multiple clock-type indicators from an image.

    Parameters
    ----------

    image_path : str
        path of image to read (.bmp file format)

    config : List[Dict]
        Configuration for clock positions, as returned by read_config().

    Returns
    -------

    list of dict:
        List of dictionaries, each containing 'value' and 'sigma'
        for each clock in the meter. 'value' is the estimated digit value,
        'sigma' is the estimated uncertainty.
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
