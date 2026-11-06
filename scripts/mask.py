"""Stand-ins for private repo names in the share cut. Fake names are random, never derived from the real name."""
import itertools, json, os, random, secrets
from PIL import Image, ImageDraw, ImageFilter

SHARE = os.environ.get('VARIANT') == 'share'
PUBLIC = set(json.load(open('build/public.json')))
_private = sorted({c['repo'] for c in json.load(open('build/commits.json'))} - PUBLIC)
ADJ = 'quiet amber silver hollow velvet distant golden lunar crimson pale sleepy electric paper glass copper misty bright salt cobalt indigo slow northern tidal gentle neon marble woven sunken ember drifting lucky tiny atomic violet coral solar ivory cedar frozen wild rusty humble curious restless polar emerald saffron twilight midnight dusty stormy sunlit'.split()
NOUN = 'harbor lantern comet orchard meadow signal compass sparrow garden beacon river atlas pebble kite anchor falcon mirror willow cinder ribbon echo tide feather parade violin orbit thimble sailboat firefly nebula quartz postcard teacup rocket tangerine origami carousel pinwheel glacier lighthouse canyon mosaic ferry dune thistle cricket walnut maple hammock kettle lagoon banjo domino zephyr tulip acorn'.split()
# The seed stays in the workspace. A fixed seed in this public code would tie each fake name to a position in the sorted real names.
if not os.path.exists('build/mask_seed'):
    open('build/mask_seed', 'w').write(secrets.token_hex(16))
_r = random.Random(open('build/mask_seed').read())
_pairs = _r.sample(list(itertools.product(ADJ, NOUN)), len(_private))
NAMES = {p: f'{a}-{n}' for p, (a, n) in zip(_r.sample(_private, len(_private)), _pairs)}

hidden = lambda name: SHARE and name not in PUBLIC
shown = lambda name: NAMES[name] if hidden(name) else name

def text(im, xy, name, font, fill, anchor='ma'):
    """Blur a private repo's fake name. The real name is never drawn, so de-blurring cannot recover it."""
    fake = NAMES[name]; tw = font.getlength(fake)
    x = xy[0] - tw / 2 if anchor == 'ma' else xy[0]
    w = int(tw) + 20; h = font.size + 18
    t = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((10, 8), fake, font=font, fill=fill)
    t = t.filter(ImageFilter.GaussianBlur(max(1.9, font.size * .14)))
    t.putalpha(t.getchannel('A').point(lambda v: min(255, int(v * 1.7))))
    im.alpha_composite(t, (max(int(x) - 10, 0), max(int(xy[1]) - 8, 0)))
