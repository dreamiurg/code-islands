"""List the repos the signed-in GitHub user can reach. With `clone`, also bare-clone them into repos/."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import common

since = common.CFG['since']; skip = set(common.CFG.get('exclude_repos', []))
out = subprocess.run(['gh', 'api', 'user/repos?per_page=100&affiliation=owner,collaborator,organization_member&sort=pushed',
                      '--paginate', '-q', f'.[]|select(.pushed_at>="{since}")|[.full_name,.private]|@tsv'],
                     capture_output=True, text=True, check=True).stdout
repos = [{'name': l.split('\t')[0], 'private': l.split('\t')[1] != 'false'} for l in out.splitlines() if l.split('\t')[0] not in skip]
os.makedirs('repos', exist_ok=True); os.makedirs('build', exist_ok=True)
json.dump(repos, open('build/repos.json', 'w'), indent=1)

print(len(repos), 'repos pushed since', since, f"({sum(r['private'] for r in repos)} private)")
for r in repos:
    print(' ', r['name'], 'private' if r['private'] else 'public')
if sys.argv[1:] != ['clone']:
    sys.exit()

def clone(r):
    d = f"repos/{r['name'].replace('/', '__')}.git"
    if os.path.exists(f'{d}/HEAD'):
        cmd = ['git', '-C', d, 'fetch', '-q', 'origin', '+refs/heads/*:refs/heads/*']
    else:
        cmd = ['git', 'clone', '-q', '--bare', f"https://github.com/{r['name']}.git", d]
    return None if subprocess.run(cmd, capture_output=True).returncode == 0 else r['name']

with ThreadPoolExecutor(8) as ex:
    failed = [n for n in ex.map(clone, repos) if n]
if failed:
    raise SystemExit(f'Could not fetch {len(failed)} repos, try `gh auth setup-git`: {failed}')
print('cloned into repos/')
