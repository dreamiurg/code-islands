"""List the repos the signed-in GitHub user can reach, then bare-clone them into repos/."""
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

def clone(r):
    d = f"repos/{r['name'].replace('/', '__')}.git"
    if os.path.exists(f'{d}/HEAD'):
        return subprocess.run(['git', '-C', d, 'fetch', '-q', 'origin', '+refs/heads/*:refs/heads/*'], capture_output=True).returncode == 0 or print('FAILED fetch', r['name'], file=sys.stderr)
    ok = subprocess.run(['git', 'clone', '-q', '--bare', f"https://github.com/{r['name']}.git", d], capture_output=True).returncode == 0
    if not ok: print('FAILED clone', r['name'], file=sys.stderr)

with ThreadPoolExecutor(8) as ex:
    list(ex.map(clone, repos))
print(len(repos), 'repos pushed since', since, f"({sum(r['private'] for r in repos)} private)")
