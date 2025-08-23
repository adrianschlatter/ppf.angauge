# -*- coding: utf-8 -*-
"""
"""

from argparse import ArgumentParser
from ppf.watermeter import read_meter, read_config, loglikelihood
import numpy as np


def main():
    parser = ArgumentParser(description="Read watermeter image")
    parser.add_argument("config_path", type=str, help="Path to config file")
    parser.add_argument("image_path", type=str, nargs='+',
                        help="Path to the meter image")
    args = parser.parse_args()

    config = read_config(args.config_path)
    s = np.linspace(0., 1., 50000)

    for img_path in args.image_path:
        readings = read_meter(img_path, config)
        llh = loglikelihood(s, readings)
        i_max = np.argmax(llh)
        s_max = s[i_max]

        print(f'{img_path}, {s_max:.5f}')
