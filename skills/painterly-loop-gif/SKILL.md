---
name: painterly-loop-gif
description: Create looping GIFs from original painterly scenes using subtle foreground displacement, rain and warm firefly particles, with MP4 previews and decoded motion proof. Use for gently animated painted environments.
---

# Painterly Loop GIF

Make a painting feel gently alive while keeping its composition and important
architecture stable. Match the user's scene and palette. The bundled night
garden is one example; other painted scenes can use the same restrained motion.
This workflow uses an **opaque, fixed still background** with local raster
displacement and procedural particles. It does not simulate individual stems,
3D depth, character motion, physical rain impacts or a moving camera.

## Background

Read [references/backgrounds.md](references/backgrounds.md) when creating or
adapting a scene. Use the built-in `image_gen` tool for an original painted
background; follow the installed imagegen skill when available. Built-in
generation needs no API key. If that tool is unavailable, report the missing
capability rather than silently choosing a paid API.

Ask for a stable opaque composition without pre-painted rain or glowing
floating dots; particles are added later. Put structures that must stay fixed
in the protected upper region. Save the selected generated image and complete
prompt beside the outputs. Inspect a local reference image before supplying
it to image_gen and distinguish visual inspiration from the image to be edited.
Existing user-owned stills can also be animated when this motion suits them.

## Render

Requires Python 3 and system FFmpeg/ffprobe with geq, displace, scroll, blend,
GIF, FFV1 and libx264 support. The script uses the standard library only;
no pip install is needed. Resolve paths from this skill directory, so installing
only this folder is sufficient:

```sh
python3 <skill-dir>/scripts/render_loop.py \
  --background <output-dir>/background.png --output <output-dir>/scene.gif \
  --width 384 --fps 24 --duration 4.8 --seed 37 \
  --rain-streaks 62 --fireflies 27 --sway-px 3.2 --protect-top .54
```

The bundled [background](assets/examples/night-garden-background.png) is the
default input, so it can be rendered offline. Omit `--background` to try it.
Output aspect ratio follows the image. Width must be even; height is rounded
to an even value for MP4. Duration is aligned to an integer frame period.
GIF delays are quantized to 10 ms.

Adjust density and sway to fit the scene. Set a particle count to `0` to disable
that layer. `--protect-top` sets the fixed upper fraction; `1` disables geometric
displacement everywhere, while particles can still pass over the image.
The central foreground is also attenuated to keep a path quieter. This is
spatial protection, not automatic object segmentation.

FFmpeg does the displacement, particles, scaling and encoding sequentially;
Python does not cache full-size RGB animation frames. A fresh output stem
gets its own working directory, MP4, contact sheet, mobile preview and JSON
report. Use `--overwrite` only when replacing that output is intended.

## Inspect and deliver

Play the exported GIF/MP4 and inspect the actual decoded contact sheet and
240-pixel preview. Check stable architecture, gentle readable movement,
particle direction/density, frame borders and the loop seam. The report records
source/output hashes, actual frames/time, infinite-loop metadata, and coarse
decoded frame differences. Compare seam change with ordinary adjacent changes;
the last frame need not be an identical copy of the first.

If the painting is wrong, correct it through image_gen. If motion is too strong
or a building bends, adjust sway/protection or the foreground layout.
Keep captions/branding separate by default unless the user requests in-art
text. Deliver clickable GIF, MP4 and proof paths plus the generation prompt,
and describe the motion honestly. Publishing needs authorization; existing
explicit publishing instructions remain valid.

The [example bundle](assets/examples/) includes the original background,
prompt, reviewed GIF/MP4 and decoded proof. It includes no downloaded
third-party reference video or reference frames.
