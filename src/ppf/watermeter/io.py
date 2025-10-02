import numpy as np
import string


def read_config(config_path):
    """
    Reads the configuration file for clock positions.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        list of dict: A list of dictionaries, each containing the keys 'x0',
        'y0', 'w', and 'phi'. Index in list is the clock index: Lowest-value
        clock is index 0, next is index 1, etc.
    """
    config = []
    with open(config_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split()
                x0, y0, w = map(int, parts[:3])
                phi = float(parts[3])
                config.append({'x0': x0, 'y0': y0, 'w': w, 'phi': phi})

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
