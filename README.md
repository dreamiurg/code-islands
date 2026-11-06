# Code Islands

Turn your commits across every repo into a video. Each repo is a separate floating island that appears when you start it and grows as you work, with a live HUD of your speed, streaks, AI mix and the model releases happening around you.

[![Example video](https://img.youtube.com/vi/9C3tzDGUd-c/maxresdefault.jpg)](https://youtu.be/9C3tzDGUd-c)

Why islands? Gource draws one connected tree, which works for a single repo. Separate projects are not connected, so here they float apart.

## Install

```text
/plugin marketplace add dreamiurg/code-islands
/plugin install code-islands@code-islands
```

Then ask Claude Code something like "make a video of my last year of commits". It asks for a start date, length and sound, finds your repos, and renders.

## Needs

`git`, `ffmpeg`, the GitHub CLI signed in (`gh auth login`), Python 3.9+ with `pillow` and `numpy`. `tesseract` is optional and powers the leak scan. An ElevenLabs key is optional and generates a soundtrack.

## What you get

- **Full cut:** every repo named, for you.
- **Share cut:** private repos show a blurred fake name, so de-blurring reveals nothing. Public repos keep their names. A scan reads the finished video and fails if a private name shows up.

Both come at 1080p and 720p. Your history stays on your machine: clones and data live in a local workspace, and the only network calls go to GitHub and, if you choose, ElevenLabs.

## Test

```sh
sh tests/smoke.sh
```

Builds two throwaway repos, renders both cuts, and checks that the private name stays out of the share cut.

## License

MIT
