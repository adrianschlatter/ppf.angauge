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
from ppf.angauge import read_config, read_multi_gauge, mle
from matplotlib.pyplot import imread

# read configuration file:
config = read_config('config.toml')

# read image:
img = imread('image.jpg')

# read meter hands from image:
readings = read_multi_gauge(img, config)

# determine most likely meter state given readings:
value, errorbar = mle(readings)
```

If you have a large set of images to process, you may value GNU`s `parallel`
tool. Leverage it as follows:

```shell
> printf "%s\0" *.bmp | parallel -0 -L 64 read_gauge <config.toml> \
  | sort | tee -a readings.csv
```

Let's break this down step by step:

* `printf "%s\0" *.bmp` generates a null-separated list of all `.bmp` files in
  the current directory. The null-separation avoids problems with filenames
  that contain spaces or special characters. Furthermore, `printf` avoids
  problems with (very) long argument lists: If you have a really large number
  of images, just using `ls *.bmp` may result in `zsh: argument list too long`.
* `parallel -0 -L 64 read_gauge <config.toml>` runs `read_gauge <config.toml>
  <image>` for each image in the list. `-0` tells `parallel` that the input
  list is null-separated. `-L 64` tells `parallel` to take 64 input arguments
  at a time and give them as arguments to a single `read_gauge` call. This is
  much more efficient than running `read_gauge` once per image, because it
  avoids the overhead of loading the python interpreter for each image.
  `parallel` will use all CPU cores in your system. If you want it to use less,
  use the `-j` argument.
* `sort`: Sorts the output of `read_gauge`
* `tee -a readings.csv`: Print results on screen but simultaneously also append
  them to `readings.csv`
