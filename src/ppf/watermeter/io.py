import numpy as np
import string


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

    # convert to numpy recarray:
    dt = np.dtype([('pow', 'i4'), ('value', 'f4'), ('sigma', 'f4')])
    rec_array = np.recarray((len(readings),), dtype=dt)
    lst = []
    for pow, (mu, sigma) in readings.items():
        lst.append((pow, mu, sigma))
    lst.sort(reverse=True)  # sort by pow
    for i, (pow, mu, sigma) in enumerate(lst):
        rec_array[i] = (pow, mu, sigma)

    return rec_array
