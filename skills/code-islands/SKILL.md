---
name: code-islands
description: This skill should be used when someone asks for a video, animation, timelapse, year in review or "wrapped" of their commits, contributions or agentic coding history, across one or many repos. Renders each repo as a separate floating island that grows with their work, with a stats HUD and AI release timeline, plus a share cut that blurs private repo names.
---

# Code Islands

Turn one person's commits across all their repos into a 1080p video. Works on macOS and Linux.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts`. Run every command from the workspace folder, written below as `cd <workspace> && ...`, because each script reads `config.json` and `build/` from the current directory.

## 1. Set up

Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh"` and fix what it reports. Run `gh auth setup-git` so private repos can be cloned.

Ask for anything that cannot be worked out:

- **Workspace folder.** Default `~/code-islands`. It holds full clones, so it can take gigabytes.
- **Start date.** Suggest a round date. Offer the first AI co-authored commit once `collect.py` has reported it.
- **Timezone.** Sets the hour-of-day chart and day boundaries.
- **Length in seconds.** Default 90. Pacing follows from the length.
- **Sound.** An audio file, or silent. See `references/music.md`.

Write `config.json` in the workspace, following `examples/config.json`. Only `since` and `authors` are required.

`authors` are case-insensitive regexes matched against `name|email` of each commit. Start from `gh api user` (login, name) and `git config user.email`, and wrap names in `\b` so `dan` does not match `daniel`. Ask for old names and emails, since they split history.

Save a square avatar of at least 128px as `avatar.png`:

```sh
cd <workspace> && curl -sL "https://github.com/<login>.png?size=200" -o avatar.png
```

## 2. Choose repos

List repos without cloning anything:

```sh
cd <workspace> && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/discover.py"
```

Show the list. Ask which employer, client or other sensitive repos to leave out, and add those to `exclude_repos` as `owner/name`. Add repos that are not on GitHub to `local_repos`. Those always count as private.

## 3. Gather

```sh
cd <workspace> && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/discover.py" clone && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/prs.py" && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/collect.py"
```

`prs.py` waits between requests because GitHub search is rate limited, so run long ranges in the background and let the chain finish before step 5.

Show the totals and top repos. Look for missed name variants, and for wrong people caught by a loose regex.

Rerun `collect.py` after any `config.json` change. After moving `since` earlier, rerun all three commands.

## 4. AI releases

`${CLAUDE_PLUGIN_ROOT}/data/ai_releases.json` drives the left panel and the heatmap ticks. Search the web for releases newer than its last entry, then write the full list to `ai_releases.json` in the workspace, which takes priority. Entries are `{"date", "name", "vendor"}`. `anthropic` draws orange, `openai` blue, and any other vendor purple. Check dates against the vendors' own announcements.

## 5. Preview

Check a real frame before the full render. Use a time late in the video:

```sh
cd <workspace> && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/islands.py" test 60 && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hud.py" test 60 build/isl_60.png
```

This writes `build/hud_60.png`. View it. `R0` and `EXP` at the top of `islands.py` set island size. `SAFE` is the area the HUD leaves free.

## 6. Render

Run as one background job, because both cuts share `build/islands.mp4`:

```sh
cd <workspace> && sh "${CLAUDE_PLUGIN_ROOT}/scripts/render.sh" && VARIANT=share sh "${CLAUDE_PLUGIN_ROOT}/scripts/render.sh" && sh "${CLAUDE_PLUGIN_ROOT}/scripts/scan.sh"
```

Files land in `out/` at 1080p and 720p. `DUR=10 OUT=/tmp/try` in front of `render.sh` makes a short test.

`scan.sh` needs `tesseract` and both cuts. It reads one frame per second with OCR, using the full cut as its control. It fails if a private name shows in the share cut, or if it cannot read names at all. Skip the share cut and the scan if the video stays private.

## Before anyone shares a cut

Tell the user plainly:

- The share cut blurs a random fake name, so de-blurring reveals nothing. Public repos keep their real names.
- Totals, activity patterns and the size of each island stay visible. Someone who knows the user may guess a large project.
- `scan.sh` samples frames and skips names under four characters, so it is a check and not a proof. View the video too.
- Nothing in `repos/` or `build/` should be published. Those folders hold private history.

## Additional resources

- `references/metrics.md`: what each number counts. Consult when a total looks wrong or the user asks.
- `references/music.md`: where to get a track, plus a prompt for AI music tools.
- `examples/config.json`: every config option.
- `examples/music-elevenlabs.py`: generating a track through one API.
