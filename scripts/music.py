"""Optional soundtrack from ElevenLabs. Needs ELEVENLABS_API_KEY. Usage: music.py [prompt]"""
import json, os, sys, urllib.error, urllib.request

meta = json.load(open('build/meta.json'))
prompt = sys.argv[1] if len(sys.argv) > 1 else ("Instrumental cinematic electronic track for a time-lapse of software projects appearing as glowing islands. "
    "Starts sparse and curious with soft pulsing synth arpeggios, gradually adds warm bass and light driving drums, builds steadily with layered "
    "synths and rising energy, reaches a wide, triumphant, uplifting peak near the end, then resolves on a clean final chord. "
    "Optimistic, modern, about 112 BPM. No vocals.")
req = urllib.request.Request('https://api.elevenlabs.io/v1/music',
    data=json.dumps({'prompt': prompt, 'music_length_ms': int((meta['duration'] + .5) * 1000), 'force_instrumental': True}).encode(),
    headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=280) as r:
        open('music.mp3', 'wb').write(r.read())
    print('wrote music.mp3')
except urllib.error.HTTPError as e:
    raise SystemExit(f'ElevenLabs error {e.code}: {e.read()[:300].decode(errors="replace")}')
