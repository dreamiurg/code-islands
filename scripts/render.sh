#!/bin/sh
# Islands + HUD + optional music. Run from the workspace. VARIANT=share blurs private repo names.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
export VARIANT=${VARIANT:-}
DUR=${DUR:-$(python3 -c "import json;print(json.load(open('build/meta.json'))['duration'])")}
OUT=${OUT:-out}; NAME=code-islands${VARIANT:+-$VARIANT}
FADE=$(awk -v d="$DUR" 'BEGIN{printf "%.2f",d-2.5}')
mkdir -p "$OUT"
python3 "$HERE/islands.py" "$DUR" | ffmpeg -y -v error -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i pipe:0 -c:v libx264 -preset medium -crf 15 -pix_fmt yuv420p build/islands.mp4
MUSIC=$(python3 -c "import json;print(json.load(open('config.json')).get('music', 'music.mp3'))")
set -- -i build/islands.mp4 -f rawvideo -pix_fmt rgba -s 1920x1080 -r 30 -i pipe:0
[ -f "$MUSIC" ] && set -- "$@" -i "$MUSIC" || echo "No audio file at $MUSIC, rendering silent" >&2
set -- "$@" -filter_complex "[0:v][1:v]overlay=shortest=1,format=yuv420p[v]" -map "[v]"
[ -f "$MUSIC" ] && set -- "$@" -map 2:a -af "afade=t=in:d=0.3,afade=t=out:st=$FADE:d=2.5,loudnorm=I=-14:TP=-1.5,aresample=48000" -c:a aac -b:a 256k
python3 "$HERE/hud.py" "$DUR" | ffmpeg -y -v error "$@" \
 -c:v libx264 -preset medium -crf 17 -profile:v high -colorspace bt709 -color_primaries bt709 -color_trc bt709 -t "$DUR" -movflags +faststart "$OUT/$NAME-1080p.mp4"
ffmpeg -y -v error -i "$OUT/$NAME-1080p.mp4" -vf scale=1280:-2:flags=lanczos -c:v libx264 -preset slow -crf 25 -c:a aac -b:a 160k -movflags +faststart "$OUT/$NAME-720p.mp4"
echo "$OUT/$NAME-1080p.mp4"
