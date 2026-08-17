#!/usr/bin/env python3
"""Stitch the coverage frames into a looping GIF with a shared palette."""
import sys, glob
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
paths = sorted(glob.glob(f"{src}/frame_*.png"))
frames = [Image.open(p).convert("RGB") for p in paths]
w, h = frames[0].size

# One adaptive palette for every frame, so colours don't shimmer between frames.
ref = Image.new("RGB", (w, h * len(frames)))
for i, f in enumerate(frames):
    ref.paste(f, (0, i * h))
pal = ref.quantize(colors=96, method=Image.MEDIANCUT)
quant = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]

# Hold the first and last frames so the contrast is readable before it loops.
durations = [1600] + [450] * (len(quant) - 2) + [2200]

quant[0].save(out, save_all=True, append_images=quant[1:],
              duration=durations, loop=0, disposal=2, optimize=True)
print(f"{out}  {w}x{h}  {len(quant)} frames")
