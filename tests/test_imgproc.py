# -*- coding: utf-8 -*-
"""
test _image_processing
"""

import numpy as np
import pytest
from ppf.angauge import _image_processing as imgproc


def test_invalid_binarization_method():
    with pytest.raises(ValueError):
        imgproc.to_bw(None, method='invalid_method', offset=128)


def test_local_binarization_invert():
    img = (np.arange(16).reshape(4, 4) * 10).astype('uint8')
    bw = imgproc.to_bw(img, method='local', offset=0, blocksize=3, invert=True)
    assert bw.dtype == bool
    assert bw.shape == img.shape
