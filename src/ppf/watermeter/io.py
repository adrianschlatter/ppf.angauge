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
