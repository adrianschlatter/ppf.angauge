# -*- coding: utf-8 -*-
"""
test command-line tool
"""

from unittest.mock import patch
from pathlib import Path
from ppf.watermeter import cli


def test_known_img(capfd):
    DATADIR = Path(__file__).parent / 'data'
    print(DATADIR)
    with patch('sys.argv',
               ['read_meter',
                str(DATADIR / 'config.tsv'),
                str(DATADIR / '2025-08-20T00:00:10.059926+02:00.bmp')]):
        cli.main()
        out, err = capfd.readouterr()
        assert '0.63317' in out.strip()
