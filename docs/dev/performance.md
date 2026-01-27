# Performance

Thoughts on performance:

* do cropping early (reduces image size dramatically)
* use memory-mapping for reading images (saves memory)
* flood-fill algorithm:
    - we follow the pixels we are actually interested in
    - don't do all the image processing and -transformation, and *then* run the
      flood-fill algorithm. Instead, start from an empty polar grid (not even
      allocated yet, just a thought model of a coordinate system). Then,
      calculate the pixel as soon as the flood-fill algorithm requests it.
    - This mean we need a way to stack virtual image operations (such as
      coordinate transforms, color transform, thresholding, etc.)
    - Note: In pure python, this is likely slower than pre-computing the entire
      image. But as soon as we move to Cython, or implement the algorithm in C
      for use directly on an ESP32 module or similar, this should be much
      faster.
