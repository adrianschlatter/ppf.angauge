from __future__ import annotations
import numpy as np


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
