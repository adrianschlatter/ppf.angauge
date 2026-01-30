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
