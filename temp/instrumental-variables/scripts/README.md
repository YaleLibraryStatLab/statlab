# Figure scripts

## `weak-instrument-coverage.gif`

Regenerate the animation in @fig-weak-coverage (Weak Instruments section):

```sh
cd research-guides/instrumental-variables
Rscript scripts/weak-instrument-coverage-frames.R /tmp/wi-frames
python3 scripts/weak-instrument-coverage-gif.py /tmp/wi-frames images/weak-instrument-coverage.gif
```

Requires `ggplot2` and `patchwork` in R, and Pillow in Python. The animation is
pre-rendered and committed rather than built at render time: it is a simulation
over 18 first-stage strengths at 8,000 replications each, and no GIF encoder
(`gifski`, `magick`, ImageMagick) is assumed to be present on machines rendering
the guide.

The simulation is a just-identified IV design with `n = 500` and
`corr(u, v) = 0.95`. The error draws are generated once and reused across every
frame, so only the first-stage coefficient changes and the intervals sharpen
smoothly instead of being redrawn at random.
