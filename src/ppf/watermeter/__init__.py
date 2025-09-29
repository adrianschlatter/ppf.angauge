# -*- coding: utf-8 -*-
"""
ppf.watermeter
++++++++++++++++

Convert images of watermeters to numerical readings.
"""

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version


__version__ = version(__name__)

# import every function, class, etc. that should be visible in the package
from .watermeter import *
from .bayes import *
from .image_processing import *
from .io import *

del watermeter
del bayes
del image_processing
del io
