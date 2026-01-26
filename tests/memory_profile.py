# -*- coding: utf-8 -*-
"""
test command-line tool
"""

from pathlib import Path
from ppf.angauge import read_config, read_meter, numeric_from_readings


if __name__ == "__main__":
    DATADIR = Path(__file__).parent / 'data'
    img_path = DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp'
    config_path = DATADIR / 'config.tsv'
    config = read_config(config_path)
    readings = read_meter(img_path, config)
    number = numeric_from_readings(readings)
