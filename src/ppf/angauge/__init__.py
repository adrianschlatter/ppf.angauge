# -*- coding: utf-8 -*-
"""
ppf.angauge
===========

Converts images of analog gauges to numerical readings. An analog gauge is
either:

* a meter with a single indicator (dial and hand) showing an analog value,
  e.g. a thermometer
* a meter with multiple indicators (also dial and hand), each representing a
  digit in a number, e.g. a water- or gasmeter

Note: It cannot read registers that represent digits as letters.


Example
-------

```python
from ppf.angauge import read_config, read_gauge, mle
from matplotlib.pyplot import imread

# read configuration file
config = read_config('path/to/config.toml')

# read image (numpy array, h x w x color)
img = imread('path/to/meter_image.jpg')

# read the meter indicators
readings = read_gauge(img, config)

# compute maximum likelihood estimate of the meter state
s_ml, y_ml = mle(readings)

print(f'Meter reading: {s_ml:.4f}')
```

`readings` contains the raw list of readings (indicator by indicator). Using
`mle`, we make use of the redundancy of multiple indicators to compute the most
likely meter state. This is the mathematical way of saying: If the 10-liter
hand shows "5.4" the 1-liter hand should show "4.something". If there is only
one indicator, `mle` simply returns the reading of that indicator.

The configuration file (or configuration dictionary) specifies the number,
position, rotation etc. of the indicators and defines how to convert the
image to a suitable black-and-white representation showing the hand in white
on black background:

```toml
hsv_to_gray = {c0=-2.45, c1=3.45, c2=0, c3=0}
gray_to_bw = {method="global", offset=128}
indicators = [
    {x0=264, y0=148, w=83, phi=-63.35, Asin=-0.104, Acos=+0.070},
    {x0=231, y0=228, w=81, phi=-71.02, Asin=-0.044, Acos=-0.030},
    {x0=256, y0=311, w=80, phi=-69.00, Asin=-0.040, Acos=-0.045},
    {x0=325, y0=360, w=80, phi=-70.58, Asin=-0.039, Acos=-0.038}
  ]
multiplier = 0.0001
```

`hsv_to_gray` specifies the coefficients for converting the image to
grayscale. `read_gauge()` converts the image from RGB color space to HSV
(Hue, Saturation, Value) color space and then computes a weighted sum of the
HSV components:

```
gray = c0 + c1 * H + c2 * S + c3 * V
```

`gray_to_bw` specifies how to convert the grayscale image to a black-and-white
image. `method` can be either `global` or `local` thresholding. For
`global`, the `offset` parameter specifies the global threshold value. For
`local`, the `offset` parameter specifies an offset to be subtracted from the
local mean, and the `blocksize` parameter (must be odd) specifies the size of
the local neighborhood to use.

`indicators` is the list of indicators (an indicator is a hand rotating in from
of a dial) on the meter. Each indicator is specified by the position of its
upper-left corner (`x0`, `y0`), its size (`w`, assumed square), its rotation
(`phi`, in degrees), and optional sine- and cosine-correction amplitude
coefficients (`Asin`, `Acos` in units of degrees) applied to the raw hand
angle::

```
theta_corrected = theta_raw + Asin * sin(theta_raw) + Acos * cos(theta_raw)
```

Finally, `multiplier` specifies the multiplier to apply to the finest
indicator to convert the reading to physical units. E.g., if your watermeter
has indicators for `dl`, `l`, `10*l`, and `100*l`, the multiplier would be
0.0001 to get readings in m³.


Uses
----

Of course, this package is not helpful if you want to convert only a single
image to a reading. The effort to prepare a configuration is only worthwhile if
you want to convert many images of always the same meter from always the same
viewpoint. Think of a camera mounted to an analog gauge that takes images at
regular intervals.
"""

try:
    from importlib_metadata import version
except ImportError:
    from importlib.metadata import version


__version__ = version(__name__)

__all__ = []

# import every function, class, etc. that should be visible in the package
from ._angauge import *
from ._bayes import *
from ._image_processing import *
from ._io import *

__all__ += _angauge.__all__
__all__ += _bayes.__all__
__all__ += _image_processing.__all__
__all__ += _io.__all__

del _angauge
del _bayes
del _image_processing
del _io
del _utils
del version
