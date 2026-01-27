# README

<img alt="pypi downloads/month" src="https://img.shields.io/pypi/dm/ppf.angauge.svg">

Ever stared at an old analog gauge - like that dusty water meter in your
basement - and wished you could convert its indicators into actionable data?

`ppf.angauge` (pronounced like "engage") to the rescue: It converts photos of
your gauge to digital readings. It handles

* meters with a single indicator showing an analog value (like an ammeter or
  the gauge in the logo)
* meters having multiple indicators each showing a digit [0, 10) of the actual
  reading (like the water meter shown below).

Note: It reads indicators (hands rotating in front of dials). It does not read
registers (rotating drums with printed digits).

It provides:

* a python package to integrate into your own projects
* a command line tool for quick testing and prototyping

Isn't this very similar to
["AI-on-the-edge"](https://github.com/jomjol/AI-on-the-edge-device)? It is. In
fact, if you are looking for a firmware to run on an esp32-cam board, you are
better off using that project. If you are working on a different platform, if
you want the flexibility to integrate with your own (python) code, or if you
are reading value-indicators (not digit-indicators), keep reading.


# Usage

The command-line tool works as follows:

```shell
> read_gauge <config.toml> <image.bmp>
image.bmp, 0.5632
```

where `config.toml` is a configuration file specifying location, size, and
orientation of the indicators in `image.bmp`, which we will explain in a
second. For more information on command line options, see `read_gauge --help`.

The following code snippet shows how to do the same in python:

```python
from ppf.angauge import read_config, read_gauge, mle
from matplotlib.pyplot import imread

# read configuration file:
config = read_config('config.toml')

# read image:
img = imread('image.jpg')

# read meter hands from image:
readings = read_gauge(img, config)

# determine most likely meter state given readings:
value, errorbar = mle(readings)
```
