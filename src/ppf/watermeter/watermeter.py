from imageio.v3 import imread
import numpy as np
import string
# from memory_profiler import profile


def rgb_to_hsv(rgb):
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


def read_config(config_path):
    """
    Reads the configuration file for clock positions.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Configuration dictionary with clock names and their parameters.
    """
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split()
                clockname = parts[0]
                clock_exponent = round(np.log10(float(clockname[1:])))
                x0, y0, w = map(int, parts[1:4])
                phi = float(parts[4])
                config[clock_exponent] = {'x0': x0, 'y0': y0, 'w': w,
                                          'phi': phi}

    return config


# @profile
def to_handscale(img):
    """
    Convert to grayscale showing bright hand on dark background.

    Args:
        img (numpy.ndarray): The input image.
    Returns:
        numpy.ndarray: The processed image in hand scale.
    """
    h = rgb_to_hsv(img / 255.)[:, :, 0]
    return np.clip((h - 0.71) / (1 - 0.71), 0., 1.)


# @profile
def cog(img):
    """
    Computes the center of gravity of the image.

    Args:
        img (numpy.ndarray): The input image.

    Returns:
        tuple: The x and y coordinates of the center of gravity.
    """
    h, w = img.shape[:2]
    x = np.arange(w)
    y = np.arange(h)
    X, Y = np.meshgrid(x, y, indexing='xy')
    c_x = np.sum(X * img) / np.sum(img)
    c_y = np.sum(Y * img) / np.sum(img)
    return c_x - w / 2, h / 2 - c_y


# @profile
def hand2digit(img_hand):
    c_x, c_y = cog(img_hand)
    theta0 = np.arctan2(c_x, c_y)
    r_max = min(img_hand.shape) / 2.
    r_min = 14/40 * r_max
    r = np.linspace(r_min, r_max, img_hand.shape[0])
    theta = np.linspace(theta0 - np.pi / 2, theta0 + np.pi / 2,
                        img_hand.shape[1])
    X = r[:, None] * np.sin(theta[None, :]) + img_hand.shape[1] / 2
    Y = img_hand.shape[0] / 2 - r[:, None] * np.cos(theta[None, :])
    img_polar = img_hand[Y.astype(int), X.astype(int)]

    # center of gravity in polar coordinates:
    c_theta, c_r = cog(img_polar)
    c_theta *= np.pi / len(theta)

    # update estimate of hand angle:
    theta0 += c_theta

    # get the std dev in angle
    dtheta = theta - c_theta
    theta_polar = img_polar.sum(axis=0)
    sigma_theta = np.sqrt((dtheta**2 * theta_polar).sum() / theta_polar.sum())
    sigma_theta = np.pi / len(theta)

    return (theta0, sigma_theta)


# @profile
def read_meter(image_path, config):
    """
    Reads a meter image and extracts the meter reading.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Extracted meter reading.
    """
    # Read the image
    img_full = imread(image_path)

    reading = {}
    for clock_exponent, cfg in config.items():
        img_clock = img_full[cfg['y0']:cfg['y0'] + cfg['w'],
                             cfg['x0']:cfg['x0'] + cfg['w']]
        img_hand = to_handscale(img_clock)
        theta, dtheta = hand2digit(img_hand)
        # compensate known rotation of clock:
        theta += cfg['phi'] / 180. * np.pi
        # convert to digit:
        digit = theta / 2 / np.pi * 10
        ddigit = dtheta / 2 / np.pi * 10
        digit = digit % 10

        reading[clock_exponent] = (digit, ddigit)

    # return reading as number
    return reading


def read_readings(filename):
    """Read the readings from a file."""

    readings = {}
    with open(filename, 'r') as f:
        for line in f:
            name, rest = line.split(':')
            # in rest, remove anything not a number or dot or space:
            to_remove = list(string.punctuation)
            to_remove.remove('.')
            to_remove.append('±')
            rest = rest.translate(str.maketrans('', '', ''.join(to_remove)))
            mu = float(rest.split()[0])
            sigma = float(rest.split()[1])
            exponent = round(np.log10(float(name[1:])))
            readings[exponent] = (mu, sigma)

    return readings


def digit(n, s):
    return (10**-n * s) % 10


def loglikelihood_uncentered(s, readings):
    p = 0.
    for n in readings.keys():
        sigma2 = readings[n][1]**2
        p += -0.5 * np.log(2 * np.pi * sigma2) \
             - ((digit(n, s) - readings[n][0])**2 / (2 * sigma2))
    return p


# @profile
def digit_centered(s, k, readings, offset=0.):
    return (s * 10**-k - readings[k][0] + 5. - offset) % 10 - 5


# @profile
def loglikelihood(s, readings, offset=0.):
    # The likelihood on the circle is the sum of the likelihoods in all
    # "Brillouin" zones of
    # the unwrapped likelihood. Wrapping means calculating an infinite sum over
    # these zones. I don't want sums (bad for logarithms), and I don't want an
    # infinite number of terms.
    # Assumption: The normal distribution is much narrower than 1 Brillouin
    # zone => we have to sum only a few zones.
    # Trick: We center the first Brillouin zone on the maximum of the normal
    # distribution => no summing, just crop to the first Brillouin zone.
    # This centering is done by digit_centered().
    p = 0.
    for n in readings.keys():
        sigma2 = readings[n][1]**2
        p += -0.5 * np.log(2 * np.pi * sigma2) \
             - digit_centered(s, n, readings, offset=offset)**2 / (2 * sigma2)
    return p


# @profile
def numeric_from_readings(readings):
    s = np.linspace(0., 1., 50000)
    llh = loglikelihood(s, readings)
    i_max = np.argmax(llh)

    return s[i_max]


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    parser.add_argument("image_path", type=str, help="Path to the meter image")
    args = parser.parse_args()

    # Example configuration for clocks
    config = read_config(args.config_path)

    readings = read_meter(args.image_path, config)

    s = np.linspace(0., 1., 50000)
    llh = loglikelihood(s, readings)
    i_max = np.argmax(llh)
    s_max = s[i_max]
    llh_max = llh[i_max]

    print(f'{args.image_path}, {s_max:.5f}')
