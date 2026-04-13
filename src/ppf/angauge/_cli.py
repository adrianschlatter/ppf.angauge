# -*- coding: utf-8 -*-
"""
"""

from argparse import ArgumentParser
from ppf.angauge import read_single_gauge, read_multi_gauge, read_config, mle
from ppf.angauge._io import read_bmp_rectangle


def load_img_or_raise(img_path):
    try:
        img = read_bmp_rectangle(img_path, x=0, y=0, w=0, h=0)
    except ValueError:
        raise ValueError(f"Failed to read image {img_path}")

    return img


def main():
    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    parser.add_argument("image_path", type=str, nargs='+',
                        help="Path to the meter image")
    parser.add_argument("--multiplier", type=float, default=None,
                        help="Multiplier of finest indicator (e.g. 0.0001)")
    parser.add_argument("--hands", action="store_true",
                        help="print hand readings")
    args = parser.parse_args()

    # read the config file:
    config = read_config(args.config_path)

    # check for incompatible arguments:
    if args.hands and 'indicators' not in config:
        print("Warning: --hands flag is ignored for single_gauge config")

    # Apply units
    multiplier = 1.
    if args.multiplier is not None:
        multiplier = args.multiplier
    elif 'multiplier' in config:
        multiplier = config['multiplier']

    # process images:
    if 'indicators' in config:
        for img_path in args.image_path:
            img = load_img_or_raise(img_path)

            try:
                readings = read_multi_gauge(img, config['indicators'])
            except ValueError:
                print(f'{img_path}, nan')
                continue

            # Find maximum likelihood meter state given the readings:
            value, y_ml = mle(readings)

            # Apply units:
            value *= multiplier

            # Print hand readings if requested:
            if args.hands:
                hand_readings = ', '.join([f'{r["value"]:.2f}'
                                           for r in readings])
                sigmas = ', '.join([f'{r["sigma"]:.3f}' for r in readings])
                print(f'{img_path}, {value:.5f}, {hand_readings}, {sigmas}')
            # Otherwise, just print the final meter reading:
            else:
                print(f'{img_path}, {value:.5f}')
    else:  # single_gauge config:
        for img_path in args.image_path:
            img = load_img_or_raise(img_path)

            try:
                reading = read_single_gauge(img, **config['indicator'])
            except ValueError:
                print(f'{img_path}, nan')
                continue

            value = reading['value']

            # Apply units:
            value *= multiplier

            # Print:
            print(f'{img_path}, {value:.5f}')
