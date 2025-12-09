import numpy as np


def cog(img: np.ndarray) -> tuple[float, float]:
    """
    Computes the center of gravity of the image.

    Args:
        img (numpy.ndarray): The input image.

    Returns:
        tuple: The x and y coordinates of the center of gravity.

    Raises:
        ValueError: If the sum of the image is zero.
    """
    h, w = img.shape[:2]
    x = np.arange(w)
    y = np.arange(h)
    X, Y = np.meshgrid(x, y, indexing='xy')
    imsum = img.sum()
    if imsum == 0:
        raise ValueError("img.sum() is zero!")
    c_x = np.sum(X * img) / imsum
    c_y = np.sum(Y * img) / imsum

    return c_x - w / 2, h / 2 - c_y


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
