# README

`ppf.angauge` - from "analog gauge", pronounced similar to "engage" - reads
your analog meter from a photo. It reads meters having multiple indicators each
showing a [0, 10[ digit using a hand on a circular dial (such as a water meter).
It also reads meters having only one digit indicator and meters with non-digit
indicators such as a pressure gauge that shows a value, e.g., from 0 to 5 bar.

Isn't this very similar to
["AI-on-the-edge"](https://github.com/jomjol/AI-on-the-edge-device)? Yes,
indeed. However, 

* `ppf.angauge` is a python package, not a firmware for an esp32-cam board
* `ppf.angauge` also reads classic gauges showing a range of analog values
  (such as a speedometer) in addition to meters having indicators to show
  digits
* `ppf.angauge` proudly avoids AI. Instead, it uses old-school image
  processing, coordinate transformations, and a little maximum-likelihood magic
  dating back to the outset of the last century.

The package provides python code to use in your own scripts as well as a
command line tool `read_meter` if you don't feel like programming.


# Usage

The command-line tool works as follows:

```shell
> read_meter <config.toml> <image.bmp>
image.bmp, 0.5632
```

where `config.toml` is a configuration file specifying location, size, and
orientation of the indicators in `image.bmp`, which we will explain in a
second. For more information on command line options, see `read_meter --help`.

The following code snippet shows how to do the same in python:

```python
from ppf.angauge import read_config, read_meter, mle
from matplotlib.pyplot import imread

# read configuration file:
config = read_config('config.toml')

# read image:
img = imread('image.bmp')

# read meter hands from image:
readings = read_meter(img, config)

# determine most likely meter state given readings:
value, errorbar = mle(readings)
```

## Configuration

`read_meter` needs a bit of configuration to find the indicators in your image
and to process the image appropriately. The following image shows an example of
a water meter with 4 analog digit indicators (marked by pink squares added for
illustration purposes):

![example photo](./assets/indicator_config.jpg)

The configuration file corresponding to the above image above looks something
like this:

```toml
hsv_to_gray = {c0=-2.45, c1=3.45, c2=0, c3=0}
gray_to_bw = {method="global", offset=128}
indicators = [
    {x0=264, y0=148, w=83, phi=-63.35, Asin=-5.959, Acos=+4.011},
    {x0=231, y0=228, w=81, phi=-71.02, Asin=-2.521, Acos=-1.719},
    {x0=256, y0=311, w=80, phi=-69.00, Asin=-2.292, Acos=-2.578},
    {x0=325, y0=360, w=80, phi=-70.58, Asin=-2.235, Acos=-2.177}
  ]
multiplier = 0.0001
```

`hsv_to_gray` specifies the coefficients for converting the image to grayscale.
The `read_meter()` function converts the image from RGB to HSV
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

`indicators` is the list of indicators (an indicator is a hand rotating in
front of a dial) on the meter. Each indicator is specified by the position of
its upper-left corner (`x0`, column no., left is 0; `y0` row no., top is zero),
its size (`w`, assumed square), its rotation (`phi`, in degrees), and optional
sine- and cosine-correction coefficients (`Asin`, `Acos` in units of degrees)
applied to the raw hand angle:

```
theta_corrected = theta_raw + Asin * sin(theta_raw) + Acos * cos(theta_raw)
```

If your picture is well aligned (front view) and your hands are well centered
and moving in proper circles, you can omit `Asin` and `Acos` or set both to 0.

Finally, `multiplier` specifies the multiplier to apply to the finest indicator
to convert the reading to physical units. E.g., if your water meter has
indicators for `0.1 liters`, `liters`, `10 liters`, and `100 liters` (as the
one in the image above), the multiplier would be 0.0001 to get readings in m³.

Note: There is *no* configuration for the digit indicators showing letters in
the image (the so-called register). `ppf.angauge` will not read these. (If you
need them, read off the register manually once, and from then on track
overflows of the analog digit indicators to determine the value of the
register.)


# Installation

```shell
pip install ppf.angauge
```

# Still reading?

If you read this far, you're probably not here for the first time. If you use
and like this project, would you consider giving it a Github Star? (The button
is at the top of this website.) If not, maybe you're interested in one of
[my other projects](https://github.com/adrianschlatter/ppf.sample/blob/develop/docs/list_of_projects.md)?


# Contributing

Did you find a bug and would like to report it? Or maybe you've fixed it
already or want to help fixing it? That's great! Please read
[CONTRIBUTING](./CONTRIBUTING.md) to learn how to proceed.

To help ascertain that contributing to this project is a pleasant experience,
we have established a [code of conduct](./CODE_OF_CONDUCT.md). You can expect
everyone to adhere to it, just make sure you do as well.


# Change Log

* 0.1:	Initial demo.
