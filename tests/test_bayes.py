# -*- coding: utf-8 -*-
"""
test _bayes module
"""

import numpy as np
from ppf.angauge import _bayes as bayes


def test_loglikelihood_single_reading():
    readings = [{'value': 0.0, 'sigma': 1.0}]
    s = np.array([0.0])
    ll = bayes.loglikelihood(s, readings)
    expected = -0.5 * np.log(2 * np.pi * 1.0)
    assert np.isclose(ll, expected)


def test_brillouin_zone_multiple_readings():
    readings = [{'value': 1.2, 'sigma': 0.5}, {'value': 3.4, 'sigma': 0.5}]
    s = np.array([12.0])
    bmi = bayes.brillouin_zone(s, readings)
    assert bmi.shape[0] == 2


def test_digit_centered_uses_bmi():
    readings = [{'value': 2.0, 'sigma': 1.0}]
    s = np.array([12.0])
    bmi = bayes.brillouin_zone(s, readings)
    centered = bayes.digit_centered(s, 0, readings, bmi)
    expected = s * 10**0 - readings[0]['value'] - bmi[0] * 10
    assert np.isclose(centered, expected)


def test_smax_and_ymax_brillouin_zone():
    readings = [{'value': 1.0, 'sigma': 1.0}, {'value': 2.0, 'sigma': 2.0}]
    bmi = np.array([0.0, 0.0])
    smax = bayes.smax_brillouin_zone(readings, bmi)
    ymax = bayes.ymax_brillouin_zone(readings, bmi)
    assert np.isfinite(smax)
    assert np.isfinite(ymax)
