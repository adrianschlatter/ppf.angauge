# -*- coding: utf-8 -*-
"""
"""

from argparse import ArgumentParser
from ppf.angauge import read_gauge, read_config, mle
from ppf.angauge._io import read_bmp_rectangle


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

    config = read_config(args.config_path)

    for img_path in args.image_path:
        try:
            img = read_bmp_rectangle(img_path, x=0, y=0, w=0, h=0)
        except ValueError:
            raise ValueError(f"Failed to read image {img_path}")

        try:
            readings = read_gauge(img, config)
        except ValueError:
            print(f'{img_path}, nan')
            continue

        # Find maximum likelihood meter state given the readings:
        s_ml, y_ml = mle(readings)

        # Apply units
        if args.multiplier is not None:
            s_ml *= args.multiplier
        elif 'multiplier' in config:
            s_ml *= config['multiplier']

        if args.hands:
            hand_readings = ', '.join([f'{r["value"]:.2f}' for r in readings])
            sigmas = ', '.join([f'{r["sigma"]:.3f}' for r in readings])
            print(f'{img_path}, {s_ml:.5f}, {hand_readings}, {sigmas}')
        else:
            print(f'{img_path}, {s_ml:.5f}')
