# -*- coding: utf-8 -*-
"""
test _io module
"""

import pytest
from pathlib import Path
from ppf.angauge import _io as io


def test_known_img_watermeter():
    DATADIR = Path(__file__).parent / 'data'
    path = str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')
    with pytest.raises(ValueError):
        io.read_bmp_rectangle(path, x=0, y=0, w=10000, h=10000)


def test_valid_bounds_read():
    DATADIR = Path(__file__).parent / 'data'
    path = str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')
    img = io.read_bmp_rectangle(path, x=0, y=0, w=10, h=10)
    assert img.shape == (10, 10, 3)


def test_normalize_indicator_cfg_missing_gray():
    with pytest.raises(ValueError):
        io.normalize_indicator_cfg({}, {'hsv_to_gray': {}})


def test_normalize_indicator_cfg_missing_hsv():
    with pytest.raises(ValueError):
        io.normalize_indicator_cfg({}, {'gray_to_bw': {}})


def test_normalize_indicator_cfg_inherits_defaults():
    local_cfg = {'x0': 1, 'y0': 2, 'w': 3}
    global_cfg = {
        'hsv_to_gray': {'c0': 1, 'c1': 0, 'c2': 0, 'c3': -1},
        'gray_to_bw': {'method': 'global', 'offset': 128},
        'theta_min': 10.0,
    }
    io.normalize_indicator_cfg(local_cfg, global_cfg)
    assert local_cfg['hsv_to_gray'] == global_cfg['hsv_to_gray']
    assert local_cfg['gray_to_bw'] == global_cfg['gray_to_bw']
    assert local_cfg['theta_min'] == 10.0


def test_read_bmp_rectangle_out_of_bounds():
    DATADIR = Path(__file__).parent / 'data'
    path = str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')
    with pytest.raises(ValueError):
        io.read_bmp_rectangle(path, x=0, y=0, w=10000, h=10000)


def test_read_bmp_rectangle_negative_coords():
    DATADIR = Path(__file__).parent / 'data'
    path = str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')
    with pytest.raises(ValueError):
        io.read_bmp_rectangle(path, x=-1, y=-1, w=10, h=10)


def test_read_config_missing_indicator_keys(tmp_path):
    config_path = tmp_path / 'invalid.toml'
    config_path.write_text('hsv_to_gray = {c0=1, c1=0, c2=0, c3=-1}\n')
    with pytest.raises(ValueError):
        io.read_config(str(config_path))


def test_read_config_both_indicator_keys(tmp_path):
    config_path = tmp_path / 'invalid.toml'
    config_path.write_text(
        'hsv_to_gray = {c0=1, c1=0, c2=0, c3=-1}\n'
        'gray_to_bw = {method="global", offset=128}\n'
        'indicator = {x0=0, y0=0, w=10}\n'
        'indicators = [{x0=0, y0=0, w=10}]\n'
    )
    with pytest.raises(ValueError):
        io.read_config(str(config_path))
