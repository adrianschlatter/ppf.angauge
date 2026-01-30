# -*- coding: utf-8 -*-
"""
test command-line tool
"""

from unittest.mock import patch
import pytest
from pathlib import Path
from ppf.angauge import _cli as cli


def test_known_img_watermeter(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                str(DATADIR / 'config_watermeter.toml'),
                str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '0.6331' in out.strip() or '0.6332' in out.strip()


def test_multiplier_arg(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                '--multiplier',
                '0.0001',
                str(DATADIR / 'config_watermeter.toml'),
                str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '0.6331' in out.strip() or '0.6332' in out.strip()


def test_hands_arg(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                '--hands',
                str(DATADIR / 'config_watermeter.toml'),
                str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '1.89, 3.24, 3.34, 6.31, 0.468, 0.430, 0.453, 0.437' \
            in out.strip()


def test_known_img_thermometer(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                str(DATADIR / 'config_thermometer.toml'),
                str(DATADIR / '2026-01-02T06:30:10.662715+01:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '49.2' in out.strip()


def test_invalid_path(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                str(DATADIR / 'config_thermometer.toml'),
                str(DATADIR / 'nonexistant.bmp')]):

        with pytest.raises(FileNotFoundError):
            cli.main()


def test_invalid_img(capfd):
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                str(DATADIR / 'config_thermometer.toml'),
                str(DATADIR / 'config_thermometer.toml')]):

        with pytest.raises(ValueError):
            cli.main()


def test_unprocessable_img(capfd):
    """Test an "all black" image not having a single hand pixel."""
    DATADIR = Path(__file__).parent / 'data'
    with patch('sys.argv',
               ['read_gauge',
                str(DATADIR / 'config_watermeter.toml'),
                str(DATADIR / '2025-07-07T22:35:05.261227+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert ' nan' in out.strip()
