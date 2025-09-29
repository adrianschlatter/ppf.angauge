# -*- coding: utf-8 -*-
"""
"""

from argparse import ArgumentParser
from ppf.watermeter import read_meter, read_config, mle


def main():
    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    parser.add_argument("image_path", type=str, nargs='+',
                        help="Path to the meter image")
    args = parser.parse_args()

    config = read_config(args.config_path)

    for img_path in args.image_path:
        try:
            readings = read_meter(img_path, config)
        except ValueError:
            print(f'{img_path}, nan')
            continue

        # Find maximum likelihood watermeter state given the readings:
        s_ml, y_ml = mle(readings)

        print(f'{img_path}, {s_ml:.5f}')
