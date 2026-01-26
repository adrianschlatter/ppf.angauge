# -*- coding: utf-8 -*-
"""
test command-line tool
"""

from unittest.mock import patch
from pathlib import Path
from ppf.watermeter import _cli as cli


def test_known_img_watermeter(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_meter',
                str(DATADIR / 'config_watermeter.toml'),
                str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '0.6331' in out.strip() or '0.6332' in out.strip()


def test_known_img_thermometer(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_meter',
                str(DATADIR / 'config_thermometer.toml'),
                str(DATADIR / '2026-01-02T06:30:10.662715+01:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '49.2' in out.strip()
