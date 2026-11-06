"""Workspace config, shared by every script. All scripts run with the workspace as the current directory."""
import json, os
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open('config.json'))
TZ = ZoneInfo(CFG.get('timezone', 'UTC'))

def _font(names):
    dirs = ['/System/Library/Fonts/Supplemental', '/System/Library/Fonts', '/Library/Fonts',
            '/usr/share/fonts/truetype/dejavu', '/usr/share/fonts/dejavu', '/usr/share/fonts/TTF', 'C:/Windows/Fonts']
    for n in names:
        for d in dirs:
            if os.path.exists(f'{d}/{n}'):
                return f'{d}/{n}'
    raise SystemExit(f'No usable font found. Tried {names}. Install DejaVu Sans.')

FONT_BOLD = _font(['Arial Bold.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'])
FONT = _font(['Arial.ttf', 'arial.ttf', 'DejaVuSans.ttf'])

def meta():
    return json.load(open('build/meta.json'))

def ai_releases():
    """The plugin's list, or the workspace's ai_releases.json when the user keeps their own."""
    p = 'ai_releases.json' if os.path.exists('ai_releases.json') else f'{ROOT}/data/ai_releases.json'
    return json.load(open(p))
