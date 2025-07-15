# README

## Project goals

* connect analog watermeters to homeassistant


Project overview

* esp32-cam
* take still images
* detect hands of analog digit indicators
* Bayesian filter to determine most likely digit combination
* homeassistant api
* MQTT


## Project structure

* web interface to configure:
    - camera- and illumination settings (brightness of illumination, exposure
      time, gain)
    - sampling rate (how often to take images)
    - image-processing parameters to separate hands from background
      (black point, white point, gamma correction, unsharp masking)
    - pixel-processing settings to convert an (r, g, b) triplet to a gray
      scale value f(r, g, b) indicating the presence (or not) of a hand
    - location, size, and orientation of analog digit indicators
    - *no* configuration for non-analog digit indicators (rotating
      number-wheels). We will not read these. Instead, we will track overflows
      of the (smaller) analog digit indicators to determine the value of the
      (higher) non-analog digit indicators, anyway.
    - first reading of water meter (including analog and non-analog
      digit indicators). Assumed uncertainty is 0.5 units of the lowest
      indicator.
    - minimum and maximum possible change of reading between two images (for
      Bayesian filter). Initial assumption: Any change within that interval has
      the same probability.
    - homeassistant settings
    - MQTT settings
    - yaml-based configuration file
* business logic:
    - pixel-processing function f to convert an (r, g, b) triplet to a gray
      scale value f(r, g, b) indicating the presence (or not) of a hand
    - for each indicator using this indicator's configuration:
        * scan grid of polar coordinates [0, 360] deg x [0.5, 1] radius
        * convert polar coordinates to Cartesian coordinates
        * read f(r, g, b) of that pixel ...
        * ... and calculate weighted average of Cartesian coordinates (*not* of
          polar coordinates)
        * convert weighted average back to polar coordinates
        * convert polar coordinates to digit value in [0, 10[ (as float, not
          yet rounded to integer)
    - Bayesian filter to determine most likely digit combination:
        * for each digit in turn:
            - using the value of digit 10**n (e.g., 5.6)
            - and value of digit 10**(n-1) (e.g., 5.7)
            - and the uncertainty of each reading
            - to calculate the most likely hand position (given that the higher
              digit is near 5.*6*, the lower digit should be near 6.
        * use most likely digit combination (and its uncertainty) and
          prediction from previous reading (and uncertainty) to obtain most
          likely final result (including uncertainty)
        * when highest digit overflows, add 1 to the even higher, non-analog
          digit indicator (that we do not read from the image)
    - send result to homeassistant via api
    - publish result to MQTT topic


## Where we are now

* Experimenting with GIMP showed that we can convert watermeter images to
  grayscale where the hands are white on featureless black background
* using the clock areas (squares) determined in GIMP, we did
    - the grayscale conversion in ImageMagick
    - converted the result to polar coordinates
    - read the hands positions including an error bar from these polar
      coordinates
    - corrected for the known rotation of the entire image
* we had write a little python script to determine the center of gravity of a
  grayscale image (ImageMagick can't do this, apparently)
* from the 4 hand positions and error bars, we determined the most likely 4
  digit number they are indicating
* we have adjusted the initial estimate of the image rotation determined from
  GIMP to maximize the likelihood of the 4 digit number (and confirmed the
  better result by looking at the image)
* we record a series of images by using an automation in homeassistant. We had
  to set fixed exposure and gain to avoid oscillations in image brightness. We
  also had to introduce delays between turning on the illumination and taking a
  picture as well as between taking a picture and turning off the illumination


### Maximum Likelihood Estimation

This turned out a little more tricky than expected. The problem is the circular
nature of the clocks. If the hand is between 0 and 1 with an error bar of 0.2,
there is a decent chance that the hand is actually at 9 - a much higher number
than 1. But there is zero chance that the hand is on a negative digit (there
are no negative digits). The probability density "wraps around".

This is very annoying because "wrapping" the distribution means adding up all
the Brillouin zones. This infinite sum poses two problems:

* we don't have infinite time
* as it is a *sum* and not a *product*, we cannot avoid multiplication of
  exponentials by simply switching to log-likelihoods

We solve this as follows: We note that the error bar is always a lot narrower
than 360 deg. Therefore, we can reasonably approximate the infinite sum by a
sum over only the lowest order Brillouin zones. But not to a single one as the
hand may be near zero, spilling a lot of probability to the neighboring zone.

Next, we *center* the probability distribution at 5: If the estimate is 1.2, we
remember this but declare 1.2 to be the new 5. Now, the probability densities
at 0 and at 9.999 become very small, spilling very little probability into
neighboring zones. Voila, there is no sum anymore and we can apply the
log-likelihood trick, thereby avoiding the calculation of exponentials and
replacing multiplications by additions.
