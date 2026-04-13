# Known Bugs

## Wrap around

** solved **

When the meter wraps at 1 m^3, sometimes this happens:

```
2025-09-28T23:10:10.175096+02:00, 0.97650
2025-09-28T23:15:10.176407+02:00, 0.97650
2025-09-28T23:20:10.174625+02:00, 0.99169
2025-09-28T23:25:10.174892+02:00, -0.00443
2025-09-28T23:30:10.174587+02:00, -0.00142
2025-09-28T23:35:10.174087+02:00, 0.00673
2025-09-28T23:40:10.174458+02:00, 0.00673
2025-09-28T23:45:10.174872+02:00, 0.00930
2025-09-28T23:50:10.175324+02:00, 0.00830
```

## Damaged images

Sometimes, we get corrupted images. As I convert them from jpg to bmp using
imagemagick, first, the corruption is fixed in the bmp. However, the bmp still
is not ok: it usually has a left-shifted lower half. This leads to strange
input - I think after "hand-color" conversion, the image may be completely
black. This in turn leads to sums and means that are zero which is not good for
division
=> inspect the code and make it more robust against these things.
