---
name: code-islands
description: Make a video of one person's coding history across all their repositories, where each repo is a separate floating island that grows as they commit, with a live stats HUD, AI model release timeline and an optional soundtrack. Also makes a shareable cut with private repo names blurred. Use when someone asks for a video, animation or visualization of their commits, contributions, year in code, or agentic coding history, across one or many repos.
---

# Code Islands

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts`. Each one runs with the workspace as its current directory.

## 1. Set up

Run `sh ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh` and fix what it reports.

Ask the user for anything you cannot work out:

- **Workspace folder.** Default `~/code-islands`. It holds full clones, so it can take gigabytes.
- **Start date.** Suggest a round date, then offer the first AI co-authored commit once step 2 has found it.
- **Length in seconds.** Default 90. Pacing follows from the length, so about 0.2 seconds a day suits a year or more.
- **Which cuts.** The full cut shows every repo name. The share cut blurs private ones.
- **Sound.** The user's own `music.mp3`, a generated track, or silent.

Write `config.json` in the workspace:

```json
{
  "since": "2025-01-01",
  "timezone": "America/New_York",
  "duration": 90,
  "authors": ["login-or-name-regex", "email@example\\.com"],
  "exclude_repos": [],
  "local_repos": []
}
```

- `authors` are regexes matched against `name|email` of each commit. Start from `gh api user` (login, name) and `git config user.email`. Ask for old names and emails, since they split history.
- `local_repos` are paths to repos that are not on GitHub. They always count as private.
- `exclude_repos` takes `owner/name`. Ask before including work or client repos in a cut other people will see.

Save the user's GitHub avatar as `avatar.png`, square, at least 128px:
`curl -sL "https://github.com/<login>.png?size=200" -o avatar.png`

## 2. Gather

```sh
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/discover.py
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prs.py
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect.py
```

`prs.py` is slow on purpose, because GitHub search is rate limited. Run it in the background on long ranges. Rerun `collect.py` after any `config.json` change.

Show the user the totals and top repos. Check for name variants that were missed, and for near-duplicate repos worth adding to `exclude_repos`.

## 3. AI releases

`data/ai_releases.json` drives the left panel and the heatmap ticks. Search the web for releases newer than its last entry, then write the full list to `ai_releases.json` in the workspace, which takes priority. Entries are `{"date", "name", "vendor"}`. `anthropic` is orange, `openai` is blue, and any other vendor is purple. Check dates against the vendors' own announcements.

## 4. Sound

For a generated track, the user needs `ELEVENLABS_API_KEY` set. Generating costs credits, so confirm first:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/music.py "optional prompt"`
Without `music.mp3` the video is silent.

## 5. Preview

Pick a time late in the video and check a real frame before the full render:

```sh
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/islands.py test 60
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hud.py test 60 build/isl_60.png
```

This writes `build/hud_60.png`. Look at it. Island size is set by `R0` and `EXP` at the top of `islands.py`. `SAFE` is the area the HUD leaves free.

## 6. Render

```sh
sh ${CLAUDE_PLUGIN_ROOT}/scripts/render.sh
VARIANT=share sh ${CLAUDE_PLUGIN_ROOT}/scripts/render.sh
sh ${CLAUDE_PLUGIN_ROOT}/scripts/scan.sh
```

Run these in the background. Files land in `out/`, at 1080p and 720p. `DUR=10 OUT=/tmp/try` makes a short test.

`scan.sh` reads one frame per second with OCR and fails if a private repo name shows in the share cut. The full cut is its control, so it should report names found there. It skips names under four characters.

## Before anyone shares a cut

Tell the user plainly:

- The share cut blurs a fake name, so de-blurring reveals nothing. Public repos keep their real names.
- Totals, activity patterns and the relative size of each island stay visible. Someone who knows the user may guess a large project.
- Run `scan.sh` first, and view the result. It samples frames, so it is a check and not a proof.
- Nothing in `repos/` or `build/` should be published. Those folders hold the private history.

## What the numbers mean

- A commit counts once, even when forks share it. Merge commits are skipped.
- Only each repo's default branch is read.
- Line counts skip lockfiles, generated code, build output, binaries, and any file changing more than 5,000 lines in one commit.
- AI mix covers commits with an AI co-author trailer, shared across those commits only.
- Tools that leave no trailer do not appear in the AI mix.
