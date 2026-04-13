# Roadmap

* improve diagnostics:
    * make it easier to find / correct the processing parameters
    * make it easier to detect anomalies (e.g., someone bumped against the
      camera)
* automatic rotation correction for multi-indicator meters:
    * assume same rotation for all indicators
    * find the rotation that results in the highest maximum-likelihood value
* better settings for thermometer-like gauges: setting the zero point may not
  be enough. Imagine a Kelvin gauge that has a temperature range around room
  temperature. The zero point would be way off scale.
* Performance improvements:
    * I think the flood-fill algorithm is a good approach
    * Unfortunately, it does not suit python very well. Maybe use a C
      implementation?
    * don't waste time on parallelism: Just remain compatible with `parallel`.
* Documentation:
    * the Bayes / maximum likelihood approach is not explained very well
      (developer docs, not relevant for user docs)
