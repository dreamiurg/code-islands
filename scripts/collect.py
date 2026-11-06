"""Merge the user's commits from every repo into build/commits.json, build/clean.log and build/meta.json."""
import collections, datetime as dt, glob, json, os, re, subprocess
import common

CFG = common.CFG; SINCE = CFG['since']
ME = re.compile('|'.join(CFG['authors']), re.I)
SKIP = re.compile(r'(generated|\.lock$|lock\.ya?ml$|lock\.json$|\.lock\.hcl|\.snap$|(^|/)dist/|(^|/)build/|(^|/)node_modules/|(^|/)vendor/|\.min\.(js|css)$|\.svg$|\.(png|jpe?g|gif|ico|pdf|mp4|mp3|woff2?|ttf|zip|csv|sqlite|db)$)', re.I)
BIG = 5000  # a single file changing more lines than this is treated as a data dump
vis = {r['name'].replace('/', '__'): r for r in json.load(open('build/repos.json'))} if os.path.exists('build/repos.json') else {}

src = [(os.path.basename(p)[:-4].split('__', 1)[1], p, vis.get(os.path.basename(p)[:-4], {}).get('private', True)) for p in glob.glob('repos/*.git')]
src += [(os.path.basename(p.rstrip('/')), p, True) for p in map(os.path.expanduser, CFG.get('local_repos', []))]
seen, commits, log, private = set(), [], [], collections.defaultdict(bool)
for repo, path, priv in sorted(src):
    out = subprocess.run(['git', '-C', path, 'log', f'--since={SINCE}', '--no-merges', '--no-renames', '--numstat', '--raw',
                          '--format=%x01%H%x02%at%x02%an|%ae%x02%B%x03', 'HEAD'], capture_output=True, text=True, errors='replace').stdout
    for rec in out.split('\x01')[1:]:
        h, at, who, rest = rec.split('\x02', 3)
        body, stat = rest.split('\x03', 1)
        if not ME.search(who) or h in seen:  # forks share history, so a commit counts once
            continue
        seen.add(h); private[repo] |= priv
        add = rem = 0; files = 0
        for ln in stat.splitlines():
            if ln.startswith(':'):
                st, fn = ln.split()[4][0], ln.split('\t', 1)[1]
                if not SKIP.search(fn):
                    files += 1; log.append((int(at), {'A': 'A', 'D': 'D'}.get(st, 'M'), f'/{repo}/{fn}'))
            elif ln and ln[0] in '0123456789-':
                a, r, fn = ln.split('\t', 2)
                if a != '-' and not SKIP.search(fn) and int(a) <= BIG and int(r) <= BIG:
                    add += int(a); rem += int(r)
        b = body.lower()
        commits.append(dict(t=int(at), repo=repo, add=add, rem=rem, files=files,
                            claude=bool(re.search(r'co-authored-by:\s*claude', b)),
                            codex='(codex)' in b or bool(re.search(r'co-authored-by:\s*codex', b)),
                            cursor=bool(re.search(r'co-authored-by:\s*cursor', b))))
assert commits, f'No commits match {CFG["authors"]} since {SINCE}'
commits.sort(key=lambda c: c['t'])
days = [dt.datetime.fromtimestamp(c['t'], common.TZ).date() for c in commits]
start, end = dt.date.fromisoformat(SINCE), max(days)
n = (end - start).days + 1; dur = CFG.get('duration', 90)
os.makedirs('build', exist_ok=True)
json.dump(commits, open('build/commits.json', 'w'))
json.dump(sorted(r for r, p in private.items() if not p), open('build/public.json', 'w'))
json.dump(dict(start=start.isoformat(), end=end.isoformat(), spd=(dur - 3) / n, duration=dur), open('build/meta.json', 'w'))
with open('build/clean.log', 'w') as f:
    for t, st, p in sorted(log):
        f.write(f'{t}|me|{st}|{p}\n')
first_ai = next((d for d, c in zip(days, commits) if c['claude'] or c['codex'] or c['cursor']), None)
print(f"{len(commits)} commits, {len(private)} repos ({sum(private.values())} private), {start} to {end}, first AI co-authored commit {first_ai}")
print(collections.Counter(c['repo'] for c in commits).most_common(12))
