from __future__ import annotations
import numpy as np
from .image_processing import flood_fill, to_polar, to_gray, to_bw


def read_indicator(img_hand: np.ndarray,
                   to_gray_params={'c0': 0, 'c1': 0, 'c2': 0, 'c3': 1},
                   to_bw_params={'method': 'global', 'offset': 128}
                   ) -> tuple[float, float]:
    """
    Estimate angle of hand +/- error bar from image of indicator (=dial and
    hand).

    Angle is 0 for hand pointing upwards, increases clockwise. Orientation of
    the dial is not considered: A possible rotation of the dial relative to
    the image's upward direction must be compensated for later.

    Parameters
    ----------

    img_hand :
        Image (3D numpy ndarray [h, w, rgb]) of an indicator (dial and hand).

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
    n_r, n_theta = 16, 128

    img_gray = to_gray(img_hand, **to_gray_params)
    img_bw = to_bw(img_gray, **to_bw_params)


    img_polar_gray = to_polar(img_gray, n_r, n_theta, rmin * rimg, rmax * rimg)
    img_polar_bw = to_polar(img_bw, n_r, n_theta, rmin * rimg, rmax * rimg)

    # starting points for flood fill: all points at minimum radius:
    starting_points = set((0, j) for j in range(n_theta))

    # process all (hand-) pixels connected to starting points:
    points_connected = flood_fill(img_polar_bw, starting_points)

    theta_distrib = np.zeros(n_theta, dtype='float')
    for (i_r, i_theta) in points_connected:
        theta_distrib[i_theta] += img_polar_gray[i_r, i_theta]

    # find peak of theta distribution:
    j_mu = np.argmax(theta_distrib)
    theta_peak = j_mu * 2 * np.pi / n_theta

    # shift theta distribution so that theta_peak is at center of left half:
    theta_dist = np.roll(theta_distrib, -j_mu + n_theta // 4)
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


def read_meter(img: np.ndarray, config: list[dict]) -> list[dict]:
    """
    Reads state of a meter with multiple clock-type indicators from an image.

    Parameters
    ----------

    img : np.ndarray-like
        Image (3D numpy array, h x w x color) of the entire meter.

    config : dict
        Configuration for image processing and clock positions, as returned by
        read_config().

    Returns
    -------

    list[dict]:
        List of dictionaries, each containing 'value' and 'sigma'
        for each clock in the meter. 'value' is the estimated digit value,
        'sigma' is the estimated uncertainty.
    """

    reading = []
    indicators = config['indicators']
    for i, cfg in enumerate(indicators):
        img_indicator = img[cfg['y0']: cfg['y0'] + cfg['w'],
                            cfg['x0']:(cfg['x0'] + cfg['w'])]
        theta, dtheta = read_indicator(img_indicator, config['hsv_to_gray'],
                                       config['gray_to_bw'])
        # compensate known rotation of clock:
        theta += cfg['phi'] / 180. * np.pi

        # compensate elliptical distortion:
        theta += getattr(cfg, 'Asin', 0) * np.sin(theta)
        theta += getattr(cfg, 'Acos', 0) * np.cos(theta)

        # convert to digit:
        digit = theta / 2 / np.pi * 10
        ddigit = dtheta / 2 / np.pi * 10
        digit = digit % 10

        reading.append({'value': digit, 'sigma': ddigit})

    return reading
