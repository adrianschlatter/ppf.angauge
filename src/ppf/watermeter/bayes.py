import numpy as np


def loglikelihood(s, readings, offset=0.):
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
    for n in readings.keys():
        sigma2 = readings[n][1]**2
        p += -0.5 * np.log(2 * np.pi * sigma2) \
             - digit_centered(s, n, readings, offset=offset)**2 / (2 * sigma2)
    return p


# If you want the maximum value as well:
def max_loglikelihood(s, readings, offset=0.0):
    p = 0.0
    for n in readings.keys():
        sigma2 = readings[n][1] ** 2
        dc = ((s * 10.0**(-n) - readings[n][0] + 5.0 - offset) % 10.0) - 5.0
        p += -0.5 * np.log(2 * np.pi * sigma2) - (dc * dc) / (2 * sigma2)
    return p


def brillouin_zone(s, readings):
    # returns the integers m_k so that:
    # s * 10**-k - readings[k][0] - m_k * 10 is in [-5, 5]
    # in other words: To replace the modulo in wm.digit_centered() by a
    # subtraction of an integer multiple of 10.
    # ks = list(readings.keys())
    # ms = {k: int((s * 10**-k - readings[k][0] + 5.) // 10) for k in ks}

    ik = ((s * 10.**-readings['pow'] -
          readings['value'] + 5.) // 10).astype(int)
    return {pow: i for pow, i in zip(readings['pow'], ik)}


def digit_centered(s, k, readings, bmi, offset=0):
    # the digit_centered function that accepts known brillouin zones
    # instead of using a modulo operation as does wm.digit_centered()
    return s * 10**-k - readings[k][0] - bmi[k] * 10


def ymax_brillouin_zone(readings, bmi):
    assert set(readings['pow']) == set(bmi.keys())

    m_k = np.array(list(bmi.values()))
    t = 10.**-readings['pow']
    W = np.diag(1 / readings['sigma']**2)
    b = (readings['value'] + 10 * m_k)
    C = np.log(2 * np.pi * readings['sigma']**2).sum()

    return -0.5 * (C + b.T @ W @ b - (t.T @ W @ b)**2 / (t.T @ W @ t))


def smax_brillouin_zone(readings, bmi):
    assert set(readings['pow']) == set(bmi.keys())

    m_k = np.array(list(bmi.values()))
    t = 10.**-readings['pow']
    W = np.diag(1 / readings['sigma']**2)
    b = (readings['value'] + 10 * m_k)

    return (t.T @ W @ b) / (t.T @ W @ t)


def initial_guess(readings):
    return sum(10.**readings['pow'] * np.round(readings['value']))


def numeric_from_readings(readings):
    s = np.linspace(0., 1., 50000)
    llh = loglikelihood(s, readings)
    i_max = np.argmax(llh)

    return s[i_max]


def mle(readings):
    """Maximum likelihood of density function defined by readings."""

    s_max = initial_guess(readings)
    bmi_0 = brillouin_zone(s_max, readings)
    y_max = ymax_brillouin_zone(readings, bmi_0)

    def find_better_neighbor():
        """
        Tries all neighboring Brillouin zones searching for a higher ymax.

        Returns True if a better neighbor was found, False otherwise.
        """
        nonlocal bmi_0, y_max, s_max
        for k in readings['pow'][1:]:
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
    s_max = s_max % (10**(max(readings['pow']) + 1))

    return s_max, y_max
