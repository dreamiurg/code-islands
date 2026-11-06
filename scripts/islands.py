"""Each repo is a separate floating island. Usage: islands.py test <seconds> | islands.py <seconds of video> (raw RGB to stdout)."""
import colorsys, json, math, multiprocessing as mp, os, sys, datetime as dt
import numpy as np
import common, mask
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, SS, FPS = 1920, 1080, 2, 30
BG = np.array([15, 17, 23], np.uint8)
SAFE = (960, 462, 1190, 770)  # centre x, centre y, width, height left free by the HUD panels
R0, EXP = 15.0, 0.40          # island radius = R0 * files ** EXP
M = common.meta(); SPD = M['spd']; TZ = common.TZ
s0 = dt.date.fromisoformat(M['start']); N = (dt.date.fromisoformat(M['end']) - s0).days + 1
T0 = dt.datetime(s0.year, s0.month, s0.day, tzinfo=TZ).timestamp()

# ---- read the log into per-repo node tables and events
class Repo:
    def __init__(self, name):
        self.name, self.ids, self.parent, self.isfile, self.lab = name, {'': 0}, [-1], [False], ['']
        self.by_day = {}
    def node(self, path):
        if path in self.ids: return self.ids[path]
        par = self.node(path.rsplit('/', 1)[0] if '/' in path else '')
        i = len(self.parent); self.ids[path] = i; self.parent.append(par); self.isfile.append(False); self.lab.append(path)
        return i

repos, ev = {}, []
for ln in open('build/clean.log'):
    ts, _, st, p = ln.rstrip('\n').split('|', 3)
    name, path = p[1:].split('/', 1)
    r = repos.setdefault(name, Repo(name)); i = r.node(path); r.isfile[i] = True
    d = int((int(ts) - T0) // 86400)
    if 0 <= d < N:
        r.by_day.setdefault(d, []).append((i, st))
        ev.append(((int(ts) - T0) / 86400 * SPD, name, i))
repos = {n: r for n, r in repos.items() if r.by_day}
order = sorted(repos, key=lambda n: min(repos[n].by_day))
RI = {n: k for k, n in enumerate(order)}
ev.sort(key=lambda e: e[0])
ET = np.array([e[0] for e in ev]); ER = np.array([RI[e[1]] for e in ev]); EN = np.array([e[2] for e in ev])

# ---- layout: a radial tree per repo, recomputed on the days that repo changed
def layout(r):
    n = len(r.parent); pos = np.full((N, n, 2), np.nan, np.float32); rad = np.zeros(N)
    alive = np.zeros(n, bool); seq = {}; kids = [[] for _ in range(n)]
    for i, p in enumerate(r.parent):
        if p >= 0 and not r.isfile[i]: kids[p].append(i)
    files_of = [[] for _ in range(n)]
    for i, p in enumerate(r.parent):
        if r.isfile[i]: files_of[p].append(i)
    cur = np.full((n, 2), np.nan, np.float32); curR = 0.0; s = 0.0
    for d in range(N):
        if d in r.by_day:
            for i, st in r.by_day[d]: alive[i] = st != 'D'
            w = [0.0] * n
            for i in range(n - 1, -1, -1):
                if r.isfile[i]: w[i] = 1.0 if alive[i] else 0.0
                if r.parent[i] >= 0: w[r.parent[i]] += w[i]
            cur = np.full((n, 2), np.nan, np.float32); dist = [0.0]
            def place(u, x, y, a0, a1, depth):
                cur[u] = (x, y)
                k = 0
                for f in files_of[u]:
                    if alive[f]:
                        rr = .16 * math.sqrt(k + 1); th = k * 2.39996
                        cur[f] = (x + rr * math.cos(th), y + rr * math.sin(th)); k += 1
                        dist[0] = max(dist[0], math.hypot(cur[f][0], cur[f][1]))
                sub = [c for c in sorted(kids[u], key=lambda c: r.lab[c]) if w[c] > 0]
                tot = sum(w[c] ** .7 for c in sub); a = a0
                for c in sub:
                    span = (a1 - a0) * w[c] ** .7 / tot; mid = a + span / 2; half = max(span, 1.1) / 2
                    L = (.75 + .16 * math.log1p(w[c])) * .86 ** depth + .16 * math.sqrt(k + 1) * .6
                    place(c, x + L * math.cos(mid), y + L * math.sin(mid), mid - half, mid + half, depth + 1); a += span
            place(0, 0.0, 0.0, 0.0, math.tau, 0)
            nf = alive.sum(); curR = R0 * max(nf, 1) ** EXP
            t = curR / max(dist[0], .3); s = t if s == 0 else .85 * s + .15 * t
            cur = cur * s
        pos[d] = cur; rad[d] = curR
    return pos, rad

POS, RAD = {}, np.zeros((N, len(order)))
for k, n in enumerate(order):
    POS[n], RAD[:, k] = layout(repos[n])

# ---- float the islands apart: overlap pushes them away, gravity keeps the group together
XY = np.full((N, len(order), 2), np.nan); cur = np.full((len(order), 2), np.nan); GOLD = 2.39996
for d in range(N):
    on = RAD[d] > 0
    for k in np.where(on & np.isnan(cur[:, 0]))[0]:
        ext = np.nanmax(np.hypot(cur[:, 0], cur[:, 1]) + np.nan_to_num(RAD[d])) if np.any(~np.isnan(cur[:, 0])) else 0
        cur[k] = (ext * .8 + RAD[d, k]) * np.array([math.cos(k * GOLD) * 1.2, math.sin(k * GOLD)])
    idx = np.where(on)[0]
    for _ in range(70):
        P = cur[idx]; R = RAD[d, idx] * 1.15 + 22
        D = P[:, None] - P[None]; L = np.hypot(D[..., 0], D[..., 1]) + 1e-6
        ov = np.clip(R[:, None] + R[None] - L, 0, None); np.fill_diagonal(ov, 0)
        m = R[None] / (R[:, None] + R[None])
        P = P + .5 * ((D / L[..., None]) * (ov * m)[..., None]).sum(1)
        P = P - np.array([.0012, .0028]) * P
        cur[idx] = P
    XY[d] = cur

def smooth(a, win):
    w = np.hanning(win + 2)[1:-1]; w /= w.sum(); pad = win // 2
    b = np.pad(a, ((pad, pad),) + ((0, 0),) * (a.ndim - 1), mode='edge')
    return np.apply_along_axis(lambda v: np.convolve(v, w, 'valid'), 0, b)

for k in range(len(order)):
    v = np.where(~np.isnan(XY[:, k, 0]))[0]
    XY[v, k] = smooth(XY[v, k], 9)

cam = np.zeros((N, 3))
for d in range(N):
    on = RAD[d] > 0
    if not on.any(): cam[d] = (0, 0, 1); continue
    x0 = (XY[d, on, 0] - RAD[d, on]).min(); x1 = (XY[d, on, 0] + RAD[d, on]).max()
    y0 = (XY[d, on, 1] - RAD[d, on]).min(); y1 = (XY[d, on, 1] + RAD[d, on]).max()
    cam[d] = ((x0 + x1) / 2, (y0 + y1) / 2, min(SAFE[2] / max(x1 - x0, 1), SAFE[3] / max(y1 - y0, 1), 1.6))
cam = smooth(cam, 21)

# ---- colour and static drawing data
TOP = max(order, key=lambda n: len(repos[n].parent))
HUE = [.38 if n == TOP else (.09 + k * .618034) % 1 for k, n in enumerate(order)]
COL = np.array([colorsys.hsv_to_rgb(h, .58, 1) for h in HUE]) * 255
SEG = {n: (np.array([i for i, p in enumerate(repos[n].parent) if p >= 0]), np.array([p for p in repos[n].parent if p >= 0])) for n in order}
ISF = {n: np.array(repos[n].isfile) for n in order}
PHASE = [k * 1.7 for k in range(len(order))]
SIZE = np.array([len(repos[n].parent) for n in order])
LABEL = set(np.argsort(-SIZE)[:26])
FONT = {s: ImageFont.truetype(common.FONT_BOLD, s) for s in (12, 13, 15, 22)}
av = Image.open(common.CFG.get('avatar', 'avatar.png')).convert('RGBA').resize((46, 46), Image.LANCZOS)
m = Image.new('L', (46 * 4, 46 * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, 183, 183), fill=255); av.putalpha(m.resize((46, 46), Image.LANCZOS))
av_ring = Image.new('RGBA', (54, 54), (0, 0, 0, 0)); ImageDraw.Draw(av_ring).ellipse((1, 1, 52, 52), outline=(255, 255, 255, 230), width=2)

def at_day(arr, x):
    a = int(min(x, N - 1)); b = min(a + 1, N - 1); f = x - a
    return arr[a] * (1 - f) + arr[b] * f

def island_xy(k, t):
    """World position of island k at video time t, including its slow drift."""
    x = min(t / SPD, N - 1.001); a = int(x)
    A, B = XY[a, k], XY[a + 1, k]
    p = B if np.isnan(A[0]) else A if np.isnan(B[0]) else A * (a + 1 - x) + B * (x - a)
    return p + np.array([math.sin(t * .37 + PHASE[k]), math.cos(t * .29 + PHASE[k])]) * (5 + RAD[int(x), k] * .012)

def to_px(p, c, t_scale=SS):
    return ((p - c[:2]) * c[2] + np.array(SAFE[:2])) * t_scale

def nodes_px(k, t):
    n = order[k]; x = min(t / SPD, N - 1.001); a = int(x); f = x - a
    A, B = POS[n][a], POS[n][a + 1]
    P = np.where(np.isnan(A), B, A * (1 - f) + B * f) if RAD[a, k] > 0 else np.full_like(A, np.nan)
    if np.isnan(P[0, 0]) and np.isnan(B[0, 0]): return None
    th = t * .012 * (1 if k % 2 else -1) + PHASE[k]; ct, st = math.cos(th), math.sin(th)
    P = np.stack((P[:, 0] * ct - P[:, 1] * st, P[:, 0] * st + P[:, 1] * ct), 1)
    c = at_day(cam, x); o = island_xy(k, t)
    return to_px(P + o, c), c, o

# avatar path: chase the island of the latest commit
FRAMES_MAX = int((N * SPD + 4) * FPS)
def avatar_path():
    out = []; p = None
    for fr in range(FRAMES_MAX):
        t = fr / FPS; i = int(np.searchsorted(ET, t)) - 1
        if i < 0: out.append(None); continue
        k = ER[i]; c = at_day(cam, min(t / SPD, N - 1.001)); tgt = to_px(island_xy(k, t), c, 1)
        p = tgt if p is None else p + (tgt - p) * .13
        out.append(p.copy())
    return out
AV = avatar_path()

def frame(fr):
    t = fr / FPS; x = min(t / SPD, N - 1.001); a = int(x)
    im = Image.new('RGB', (W * SS, H * SS), tuple(int(v) for v in BG)); d = ImageDraw.Draw(im, 'RGBA')
    a0 = int(np.searchsorted(ET, t - 2.2)); a1 = int(np.searchsorted(ET, t))
    labels, dots = [], []
    for k, n in enumerate(order):
        if RAD[a, k] == 0 and RAD[a + 1, k] == 0: continue
        res = nodes_px(k, t)
        if res is None: continue
        P, c, o = res
        ctr = to_px(o, c); rp = RAD[a, k] * c[2] * SS * 1.1 + 8; col = COL[k]
        d.ellipse((ctr[0] - rp, ctr[1] - rp, ctr[0] + rp, ctr[1] + rp), fill=tuple(int(v * .10) for v in col) + (120,))
        ch, pa = SEG[n]; ok = ~np.isnan(P[ch, 0]) & ~np.isnan(P[pa, 0])
        lc = tuple(int(v * .42) for v in col)
        for u, v in zip(P[ch[ok]].tolist(), P[pa[ok]].tolist()): d.line((u[0], u[1], v[0], v[1]), fill=lc, width=1)
        last = np.full(P.shape[0], -9.0)
        mine = ER[a0:a1] == k
        last[EN[a0:a1][mine]] = ET[a0:a1][mine]
        heat = np.exp(-(t - last) / .55)
        f = ISF[n] & ~np.isnan(P[:, 0])
        dots.append((P[f], (col * .78)[None] * (1 - heat[f, None]) + 255 * heat[f, None], heat[f]))
        recent = ET[a0:a1][mine].max() if mine.any() else -9
        labels.append((k, ctr / SS, rp / SS, recent))
        for e in EN[a0:a1][mine][-14:]:
            if AV[fr] is not None and t - last[e] < .3 and not np.isnan(P[e, 0]):
                al = int(150 * (1 - (t - last[e]) / .3)); d.line((AV[fr][0] * SS, AV[fr][1] * SS, P[e, 0], P[e, 1]), fill=tuple(int(v) for v in col) + (al,), width=2)
    arr = np.array(im)
    for P, C, h in dots:
        if not len(P): continue
        xy = P.astype(int); C = C.astype(np.uint8)
        for r, sel in ((1, np.ones(len(xy), bool)), (2, h > .25), (3, h > .6)):
            q, c2 = xy[sel], C[sel]
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy > r * r + 1: continue
                    X, Y = q[:, 0] + dx, q[:, 1] + dy; g = (X >= 0) & (X < W * SS) & (Y >= 0) & (Y < H * SS)
                    arr[Y[g], X[g]] = c2[g]
    base = Image.fromarray(arr).resize((W, H), Image.LANCZOS)
    glow = base.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    out = Image.fromarray(np.clip(np.array(base, np.int16) + (np.array(glow, np.int16) - BG) .clip(0) * .85, 0, 255).astype(np.uint8)).convert('RGBA')
    txt = ImageDraw.Draw(out)
    taken = []
    for k, ctr, rp, recent in sorted(labels, key=lambda l: (t - l[3] >= 1.6, -l[2])):
        live = t - recent < 1.6
        if not (k in LABEL or live): continue
        hide = mask.hidden(order[k]); w = len(mask.shown(order[k])) * 4.4 + 6; y = ctr[1] + rp + 3
        if any(abs(ctr[0] - a) < w + b and abs(y - c) < 19 for a, c, b in taken): continue
        taken.append((ctr[0], y, w))
        s = 22 if order[k] == TOP and not hide else 15 if live or rp > 34 else 13
        al = 255 if live else 150
        if hide:
            mask.text(out, (ctr[0], y), order[k], FONT[s], tuple(min(255, int(v * .6 + 110)) for v in COL[k]) + (al,)); continue
        txt.text((ctr[0], y), order[k], font=FONT[s], fill=tuple(min(255, int(v * .6 + 110)) for v in COL[k]) + (al,), anchor='ma', stroke_width=2, stroke_fill=(15, 17, 23, 220))
    if AV[fr] is not None:
        ax, ay = AV[fr].astype(int); out.alpha_composite(av_ring, (int(ax) - 27, int(ay) - 27)); out.alpha_composite(av, (int(ax) - 23, int(ay) - 23))
    return out.convert('RGB')

if __name__ == '__main__':
    if sys.argv[1] == 'test':
        t = float(sys.argv[2]); frame(int(t * FPS)).save(f'build/isl_{int(t)}.png'); sys.exit()
    total = int(float(sys.argv[1]) * FPS)
    with mp.get_context('fork').Pool(max(2, (os.cpu_count() or 4) - 2)) as pool:
        for im in pool.imap(frame, range(total), chunksize=8):
            sys.stdout.buffer.write(im.tobytes())
