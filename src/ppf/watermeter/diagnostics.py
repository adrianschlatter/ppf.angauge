from __future__ import annotations
import numpy as np


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


def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
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
