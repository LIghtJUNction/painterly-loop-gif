# Background design and motion limits

Use this when generating a scene or deciding whether an existing still suits
this renderer. Keep the user's theme, medium, colours and framing.

## Prompt scaffold

```text
Use case: illustration-story.
Asset type: original opaque painted environment for a looping GIF.
Scene: [USER'S SCENE], [DESIRED PALETTE / MEDIUM / LIGHTING].
Composition: [FRAMING AND ASPECT RATIO], stable perspective and camera.
Use foreground foliage or other organic texture that can accept a little
local displacement. Place buildings or sharp rigid details in the protected
upper region; leave their silhouettes clear. Reserve some negative space
for subtle moving light points and/or rain when those effects are wanted.
This is the STILL background. Do not paint rain, fireflies, glowing floating
dots, motion streaks or lettering; those layers will be added separately.
Original composition; no logos, watermarks, UI or borders unless requested.
```

Use the built-in image_gen tool for the raster painting. Inspect an input
reference first, state whether it is inspiration or an edit target, and retain
the selected generated file and complete prompt. The built-in tool saves its
output under Codex's generated-image area; copy the selected file into the
user's delivery folder rather than leaving a project dependency there.
The example's exact prompt lives in `../assets/examples/background-prompt.txt`.

## What actually moves

The background is a single opaque raster. The camera stays fixed. Periodic
displacement grows toward the bottom and is weaker around the central path.
The protected top has zero geometric displacement; screen-blended rain and
lights can still alter its visible pixels. This is not per-object protection.

Rain is a wrapped scrolling layer of short streaks. Fireflies are analytic
warm-coloured soft light points with periodic drift and blinking; they are
not simulated insects. The example avoids large lights over the upper-left
greenhouse, but this is a fixed spatial preference, not recognition of a new
scene's building. Always inspect particles in a newly chosen composition.

Sway strength is measured in output pixels; choose a small value for a subtle
effect. Rain/firefly counts and the fixed top fraction can be changed without
editing the script. Water ripples, snow, moving characters, independently
articulated leaves or camera parallax require an extension or another workflow;
do not describe this renderer as already providing them.

## Loop and proof

The script rounds `duration × FPS` to an integer count and uses that count's
period for the sine fields and scrolling layer. A loop continues normally from
last to first; duplicating the first frame is unnecessary. GIF delay precision
is 10 ms, so report the actual exported duration.

Its motion check streams one 64-pixel-wide grayscale frame at a time and keeps
small hashes/differences, not full RGB frame caches. Unique grayscale-frame
counts and pixel changes confirm observed motion at that small size, not that
every depicted object moves realistically. Review actual playback and decoded
proof for that judgement.
