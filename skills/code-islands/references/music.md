# Soundtrack

Any audio file works. Put it in the workspace as `music.mp3`, or set `"music"` in `config.json` to another path. ffmpeg reads mp3, wav, m4a and most other formats. With no file, the video is silent.

Good sources:

- A track the user already has rights to use
- A royalty-free library
- Any AI music generator

Make the track at least as long as the video. Read `duration` in `build/meta.json`. The render fades out over the last 2.5 seconds and normalizes loudness.

Prompt that fits the video, for any generator:

> Instrumental cinematic electronic track for a time-lapse of software projects appearing as glowing islands. Starts sparse and curious with soft pulsing synth arpeggios, gradually adds warm bass and light driving drums, builds steadily with layered synths and rising energy, reaches a wide, triumphant, uplifting peak near the end, then resolves on a clean final chord. Optimistic, modern, about 112 BPM. No vocals.

Time the build to the user's own story. A rise at a known turning point lands better than an even climb.

`examples/music-elevenlabs.py` shows one way to do this through an API. Generators cost credits, so confirm first.

Before publishing a video, check the license terms of the track.
