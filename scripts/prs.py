"""Fetch the user's merged PRs half a month at a time. GitHub search returns 1000 results at most per query."""
import datetime as dt, json, subprocess, time
import common

login = subprocess.run(['gh', 'api', 'user', '-q', '.login'], capture_output=True, text=True, check=True).stdout.strip()
a = dt.date.fromisoformat(common.CFG['since']); end = dt.date.today(); P = {}
while a <= end:
    b = min(a + dt.timedelta(14), end)
    for attempt in range(4):
        r = subprocess.run(['gh', 'search', 'prs', '--author', login, '--merged', '--merged-at', f'{a}..{b}', '--limit', '1000',
                            '--json', 'repository,closedAt,number'], capture_output=True, text=True)
        if r.returncode == 0: break
        time.sleep(65)  # search allows few requests a minute
    else:
        raise SystemExit(f'PR search failed for {a}..{b}: {r.stderr[:300]}')
    got = json.loads(r.stdout)
    assert len(got) < 1000, f'{a}..{b} hit the 1000 result cap; shorten the window'
    for p in got: P[(p['repository']['nameWithOwner'], p['number'])] = p['closedAt']
    a = b + dt.timedelta(1); time.sleep(7)
json.dump([{'repo': k[0], 'closed': v} for k, v in P.items()], open('build/prs.json', 'w'))
print(len(P), 'merged PRs')
