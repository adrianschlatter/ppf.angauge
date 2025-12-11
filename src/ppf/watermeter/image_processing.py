
def to_handscale(r: int, g: int, b: int) -> int:
    """
    Convert to grayscale showing bright hand on dark background.

    Args:
        r, g, b (int): RGB triplet in 2**-8 fixed point.
    Returns:
        hs: processed value in hand scale (2**-8 fixed point)
    """

    r, g, b = map(int, (r, g, b))               # * 2**-8
    r, g, b = r << 8, g << 8, b << 8            # * 2**-16

    # Compute maximum and minimum values
    mx = max(r, max(g, b))                      # * 2**-16
    mn = min(r, min(g, b))                      # * 2**-16
    delta = mx - mn                             # * 2**-16

    # Compute Hue (H)
    if delta > 0:
        r, g, b = r << 5, g << 5, b << 5        # * 2**-21
        mx = mx << 5                            # * 2**-21
        delta = delta >> 5                      # * 2**-11
        if mx == r:
            h = (g - b) // delta                # * 2**-10
        elif mx == g:
            h = (2 << 10) + (b - r) // delta    # * 2**-10
        else:  # mx == b
            h = (4 << 10) + (r - g) // delta    # * 2**-10

        h = ((h << 6) % (6 << 16)) // 6         # * 2**-16
    else:
        h = 0                                   # * 2**-16

    # 0.71 in 2**-16 fixed point: 46530
    # (1 - 0.71) in 2**-8 fixed point: 74
    handscale = (h - 46530) // 74               # * 2**-8

    return 0 if handscale <= 0 else handscale   # * 2**-8
