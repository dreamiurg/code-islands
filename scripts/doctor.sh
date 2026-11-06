#!/bin/sh
# Report missing tools. Exits non-zero if a required one is absent.
bad=0
for t in git gh ffmpeg ffprobe python3; do command -v $t >/dev/null || { echo "MISSING: $t"; bad=1; }; done
python3 -c "import PIL, numpy" 2>/dev/null || { echo "MISSING: python packages. Run: python3 -m pip install pillow numpy"; bad=1; }
gh auth status >/dev/null 2>&1 || { echo "MISSING: GitHub sign-in. Run: gh auth login"; bad=1; }
command -v tesseract >/dev/null || echo "OPTIONAL: tesseract is needed for scan.sh, which checks a share cut for leaks"
[ $bad = 0 ] && echo "ready"
exit $bad
