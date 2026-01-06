# -*- coding: utf-8 -*-
"""
"""

from argparse import ArgumentParser
from ppf.watermeter import read_meter, read_config, mle
from sys import stderr


def main():
    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    parser.add_argument("image_path", type=str, nargs='+',
                        help="Path to the meter image")
    parser.add_argument("--multiplier", type=float, default=0.0001,
                        help="Multiplier of finest indicator (e.g. 0.0001)")
    parser.add_argument("--hands", action="store_true",
                        help="print hand readings")
    args = parser.parse_args()

    config = read_config(args.config_path)

    for img_path in args.image_path:
        try:
            readings = read_meter(img_path, config)
        except ValueError:
            print(f'{img_path}, nan')
            continue
        except FileNotFoundError:
            print(f'File not found: {img_path}', file=stderr)
            continue

        # Find maximum likelihood watermeter state given the readings:
        s_ml, y_ml = mle(readings)

        # Apply units
        s_ml *= args.multiplier

        if args.hands:
            hand_readings = ', '.join([f'{r["value"]:.2f}' for r in readings])
            sigmas = ', '.join([f'{r["sigma"]:.3f}' for r in readings])
            print(f'{img_path}, {s_ml:.5f}, {hand_readings}, {sigmas}')
        else:
            print(f'{img_path}, {s_ml:.5f}')
