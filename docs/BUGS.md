# Known Bugs

## Damaged images

Sometimes, we get corrupted images. As I convert them from jpg to bmp using
imagemagick, first, the corruption is fixed in the bmp. However, the bmp still
is not ok: it usually has a left-shifted lower half. This leads to strange
input - I think after "hand-color" conversion, the image may be completely
black. This in turn leads to sums and means that are zero which is not good for
division
=> inspect the code and make it more robust against these things.
