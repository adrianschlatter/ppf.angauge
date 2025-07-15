#!/usr/bin/env python

from imageio.v3 import imread
from matplotlib.colors import rgb_to_hsv
import numpy as np


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


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("image_path", type=str, help="Path to the meter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    args = parser.parse_args()

    # Example configuration for clocks
    config = read_config(args.config_path)

    reading = read_meter(args.image_path, config)
    keys = sorted(reading.keys(), reverse=True)
    for k in keys:
        print(f"x{10**k}: ({reading[k][0]:.4f} ± {reading[k][1]:.4f})")
