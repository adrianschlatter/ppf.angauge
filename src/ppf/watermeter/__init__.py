# -*- coding: utf-8 -*-
"""
ppf.watermeter
++++++++++++++++

Convert images of watermeters to numerical readings.
"""

try:
    from importlib_metadata import version
except ImportError:
    from importlib.metadata import version


__version__ = version(__name__)

__all__ = []

# import every function, class, etc. that should be visible in the package
from ._watermeter import *
from ._bayes import *
from ._image_processing import *
from ._io import *

__all__ += _watermeter.__all__
__all__ += _bayes.__all__
__all__ += _image_processing.__all__
__all__ += _io.__all__

del _watermeter
del _bayes
del _image_processing
del _io
del _utils
del version
