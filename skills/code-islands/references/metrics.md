# What the numbers mean

- A commit counts once, even when forks share it. Merge commits are skipped.
- GitHub repos are read at their default branch. `local_repos` are read at their checked-out HEAD.
- Line counts skip lockfiles, generated code, build output, binaries, and any file changing more than 5,000 lines in one commit.
- PR counts come from GitHub search and skip `exclude_repos`.
- AI mix covers commits with an AI co-author trailer, shared across those commits only. When a commit carries several, Codex wins, then Claude, then Cursor.
- Tools that leave no trailer do not appear in the AI mix.
- A day is a calendar day in `timezone`. Late night means 10pm to 5am.
- Best week is a rolling 7 days. Best month is a calendar month.
