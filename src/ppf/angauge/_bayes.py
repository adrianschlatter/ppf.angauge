from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from ._utils import export


def loglikelihood(s: NDArray,
                  readings: list[dict], offset: float = 0.) -> NDArray:
    # The likelihood on the circle is the sum of the likelihoods in all
    # "Brillouin" zones of
    # the unwrapped likelihood. Wrapping means calculating an infinite sum over
    # these zones. I don't want sums (bad for logarithms), and I don't want an
    # infinite number of terms.
    # Assumption: The normal distribution is much narrower than 1 Brillouin
    # zone => we have to sum only a few zones.
    # Trick: We center the first Brillouin zone on the maximum of the normal
    # distribution => no summing, just crop to the first Brillouin zone.
    # This centering is done by digit_centered().
    p = 0.
    for n, reading in enumerate(readings):
        sigma2 = reading['sigma']**2
        bmi = brillouin_zone(s, readings)
        p += -0.5 * np.log(2 * np.pi * sigma2) \
             - digit_centered(s, n, readings, bmi,
                              offset=offset)**2 / (2 * sigma2)
    return p


def brillouin_zone(s: NDArray, readings: list[dict]) -> NDArray:
    # returns the integers m_k so that:
    # s * 10**-k - readings[k][0] - m_k * 10 is in [-5, 5]
    # in other words: To replace the modulo in wm.digit_centered() by a
    # subtraction of an integer multiple of 10.
    return np.array([(s * 10.**-i - r['value'] + 5.) // 10
                     for i, r in enumerate(readings)])


def digit_centered(s: NDArray, k: int, readings: list[dict],
                   bmi: NDArray, offset=0) -> NDArray:
    # the digit_centered function that accepts known brillouin zones
    # instead of using a modulo operation as does wm.digit_centered()
    return s * 10**-k - readings[k]['value'] - bmi[k] * 10


def ymax_brillouin_zone(readings: list[dict], bmi: NDArray) -> float:
    assert len(readings) == len(bmi)

    values = np.array([r['value'] for r in readings])
    sigmas = np.array([r['sigma'] for r in readings])

    m_k = bmi
    t = 10.**-np.arange(len(readings))
    W = np.diag(1 / sigmas**2)
    b = (values + 10 * m_k)
    C = np.log(2 * np.pi * sigmas**2).sum()

    return -0.5 * (C + b.T @ W @ b - (t.T @ W @ b)**2 / (t.T @ W @ t))


def smax_brillouin_zone(readings: list[dict], bmi: NDArray) -> float:
    assert len(readings) == len(bmi)

    values = np.array([r['value'] for r in readings])
    sigmas = np.array([r['sigma'] for r in readings])

    m_k = bmi
    t = 10.**-np.arange(len(readings))
    W = np.diag(1 / sigmas**2)
    b = (values + 10 * m_k)

    return (t.T @ W @ b) / (t.T @ W @ t)


def initial_guess(readings: list[dict]) -> float:
    return sum([10.**i * r['value'] for i, r in enumerate(readings)])


@export
def mle(readings: list[dict]) -> (float, float):
    """
    Return maximum likelihood of density function defined by readings.

    Parameters
    ----------

    readings : list of dict
        List of readings, each reading is a dictionary with keys 'value' and
        'sigma'. 'value' is the digit value read from the indicator [0, 10),
        'sigma' is the standard error of the reading.

    Returns
    -------

    s_max : float
        Maximum likelihood estimate given the readings.

    y_max : float
        Log-likelihood value at s_max.
    """

    s_max = initial_guess(readings)
    bmi_0 = brillouin_zone(s_max, readings)
    y_max = ymax_brillouin_zone(readings, bmi_0)

    def find_better_neighbor():
        """
        Tries all neighboring Brillouin zones searching for a higher ymax.

        Returns True if a better neighbor was found, False otherwise.
        """
        nonlocal y_max, s_max
        for k in range(len(readings)):
            for delta in [-1, 1]:
                # shift s up or down so that reading[k] stays the same:
                s_shifted = s_max + delta * 10.**(k + 1)
                bmi = brillouin_zone(s_shifted, readings)
                y_new = ymax_brillouin_zone(readings, bmi)
                if y_new > y_max:
                    y_max = y_new
                    s_max = smax_brillouin_zone(readings, bmi)
                    # Stop searching this neighborhood. Return true and let
                    # caller start over from the new position.
                    return True
        return False

    # find Brillouin zone that has no better neighbor:
    while find_better_neighbor():
        pass

    # sometimes, we slip below zero if s is close to zero and the narrowest
    # Brillouin zone is cut at zero and has its maximum below zero.
    # We want the result to be within the largest Brillouin zone:
    s_max = s_max % (10**len(readings))

    return s_max, y_max
