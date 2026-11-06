#!/bin/sh
# End to end on two throwaway repos: one public, one private. Needs ffmpeg and tesseract, not GitHub.
set -eu
S=$(cd "$(dirname "$0")/../scripts" && pwd)
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; cd "$W"
export GIT_CONFIG_GLOBAL=/dev/null GIT_AUTHOR_NAME="Test Dev" GIT_AUTHOR_EMAIL=dev@example.com GIT_COMMITTER_NAME="Test Dev" GIT_COMMITTER_EMAIL=dev@example.com
for r in open-widget hidden-treasure; do
  git init -q "src/$r"
  i=1; while [ $i -le 30 ]; do
    d=$(printf '2026-0%d-%02d' $(((i - 1) / 10 + 1)) $(((i - 1) % 10 * 2 + 3)))
    mkdir -p "src/$r/lib/d$((i % 4))"; echo "$i" > "src/$r/lib/d$((i % 4))/f$i.txt"
    git -C "src/$r" add -A
    GIT_AUTHOR_DATE="${d}T12:00:00" GIT_COMMITTER_DATE="${d}T12:00:00" git -C "src/$r" commit -qm "$r $i" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
    i=$((i + 1))
  done
done
mkdir -p repos build
git clone -q --bare src/open-widget repos/acme__open-widget.git
echo '[{"name": "acme/open-widget", "private": false}]' > build/repos.json
echo '[]' > build/prs.json
python3 -c "
from PIL import Image
Image.new('RGB', (128, 128), (200, 120, 60)).save('avatar.png')
import json
json.dump(dict(since='2026-01-01', timezone='UTC', duration=8, authors=['test dev'], local_repos=['$W/src/hidden-treasure']), open('config.json', 'w'))"
ffmpeg -v error -f lavfi -i "sine=frequency=220:duration=9" music.mp3
python3 "$S/collect.py"
python3 -c "import json;assert json.load(open('build/public.json'))==['open-widget']"
python3 -c "
import json;c=json.load(open('config.json'));c['exclude_repos']=['acme/open-widget'];json.dump(c,open('config.json','w'))"
python3 "$S/collect.py"
python3 -c "import json;assert {c['repo'] for c in json.load(open('build/commits.json'))}=={'hidden-treasure'}"
python3 -c "
import json;c=json.load(open('config.json'));c['exclude_repos']=[];json.dump(c,open('config.json','w'))"
python3 "$S/collect.py"
sh "$S/render.sh"
VARIANT=share sh "$S/render.sh"
for f in out/code-islands-1080p.mp4 out/code-islands-share-720p.mp4; do
  [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f | cut -d. -f1)" = 8 ] || [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f | cut -d. -f1)" = 7 ]
done
[ "$(ffprobe -v error -show_entries stream=codec_type -of csv=p=0 out/code-islands-1080p.mp4 | sort | tr -d '\n')" = audiovideo ]
sh "$S/scan.sh"
echo PASS
