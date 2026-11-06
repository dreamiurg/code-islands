#!/bin/sh
# OCR one frame per second of both cuts and fail if a private repo name shows in the share cut.
set -eu
OUT=${OUT:-out}
rm -rf build/scan; mkdir -p build/scan/share build/scan/full
ffmpeg -v error -y -i "$OUT/code-islands-share-1080p.mp4" -vf "fps=1,scale=3840:-1:flags=lanczos" build/scan/share/%03d.png
ffmpeg -v error -y -i "$OUT/code-islands-1080p.mp4" -vf "fps=1,scale=3840:-1:flags=lanczos" build/scan/full/%03d.png
for v in share full; do ls build/scan/$v/*.png | xargs -P 8 -I{} sh -c 'OMP_THREAD_LIMIT=1 tesseract {} {} --psm 11 >/dev/null 2>&1'; done
python3 - <<'P'
import collections, glob, json, re, shutil
pub = set(json.load(open('build/public.json')))
priv = sorted({c['repo'] for c in json.load(open('build/commits.json'))} - pub)
def scan(v):
    h = collections.Counter()
    for p in glob.glob(f'build/scan/{v}/*.txt'):
        t = open(p, errors='replace').read().lower()
        for r in priv:
            if len(r) >= 4 and re.search(r'(?<![a-z0-9-])' + re.escape(r.lower()) + r'(?![a-z0-9-])', t): h[r] += 1
    return h
full, share = scan('full'), scan('share')
print(f'{len(priv)} private repos. Control (full cut) found {len(full)} names. Share cut found {len(share)}: {share.most_common()}')
shutil.rmtree('build/scan')
assert not share, 'Private names visible in the share cut. Do not share it.'
assert full or not [r for r in priv if len(r) >= 4], 'OCR found no names in the full cut, so this scan proves nothing.'
P
