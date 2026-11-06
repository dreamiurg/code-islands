import json, os, sys, datetime as dt, collections
import numpy as np
import common, mask
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080; FPS = 30
Wh = (255, 255, 255, 255); G = (165, 173, 186, 255); Dim = (95, 101, 114, 255)
GR = (143, 214, 148, 255); OR = (240, 170, 90, 255); BL = (120, 170, 250, 255); PU = (190, 140, 245, 255); PN = (15, 17, 23, 190)
A, AR = common.FONT_BOLD, common.FONT
_f = {}
def f(s, p=A): return _f.setdefault((s, p), ImageFont.truetype(p, s))

TZ = common.TZ; M = common.meta()
s0 = dt.date.fromisoformat(M['start']); e0 = dt.date.fromisoformat(M['end']); N = (e0 - s0).days + 1
D = lambda iso: (dt.date.fromisoformat(iso) - s0).days
day = lambda t: min(t / M['spd'], N - 1.0)

C = json.load(open('build/commits.json'))
repos = sorted({c['repo'] for c in C}); RI = {r: i for i, r in enumerate(repos)}
cnt = np.zeros(N); add = np.zeros(N); rem = np.zeros(N); byrepo = np.zeros((N, len(repos)))
cl = np.zeros(N); cx = np.zeros(N); cu = np.zeros(N); hrs = np.zeros((N, 24)); wkend = np.zeros(N); late = np.zeros(N)
for c in C:
    t = dt.datetime.fromtimestamp(c['t'], TZ); i = (t.date() - s0).days
    if not 0 <= i < N: continue
    cnt[i] += 1; add[i] += c['add']; rem[i] += c['rem']; byrepo[i, RI[c['repo']]] += 1; hrs[i, t.hour] += 1
    wkend[i] += t.weekday() >= 5; late[i] += t.hour >= 22 or t.hour < 5
    if c['codex']: cx[i] += 1
    elif c['claude']: cl[i] += 1
    elif c['cursor']: cu[i] += 1
pr = np.zeros(N)
for p in json.load(open('build/prs.json')):
    t = dt.datetime.fromisoformat(p['closed'].replace('Z', '+00:00')).astimezone(TZ); i = (t.date() - s0).days
    if 0 <= i < N: pr[i] += 1
cum = lambda a: np.cumsum(a, axis=0)
cC, cA, cP, cCl, cCx, cCu, cH, cW, cL = map(cum, (cnt, add, pr, cl, cx, cu, hrs, wkend, late))
seen = (cum(byrepo) > 0).sum(axis=1)
wk = np.array([cnt[max(0, i - 6):i + 1].sum() for i in range(N)]); wkl = np.array([add[max(0, i - 6):i + 1].sum() for i in range(N)])
best = np.maximum.accumulate(wk)
mon = collections.Counter(); bestm = np.zeros(N); b = 0
for i in range(N):
    k = (s0 + dt.timedelta(i)).strftime('%Y-%m'); mon[k] += cnt[i]; b = max(b, mon[k]); bestm[i] = b
stk = np.zeros(N); r = 0
for i in range(N):
    r = r + 1 if cnt[i] else 0; stk[i] = r
stkb = np.maximum.accumulate(stk)
heatq = np.quantile(cnt[cnt > 0], [.25, .5, .75, .92])
HC = [(34, 38, 46, 255), (40, 84, 58, 255), (58, 128, 80, 255), (96, 176, 110, 255), (143, 214, 148, 255), (205, 245, 190, 255)]

T = common.ai_releases()
WO = [(D(x['date']), x['name'], {'anthropic': OR, 'openai': BL}.get(x['vendor'], PU)) for x in T]

def spark(d, x, y, w, h, v, n, col):
    if n < 2: return
    v = v[:n]; mx = max(v.max(), 1); P = [(x + w * i / (n - 1), y + h - h * a / mx) for i, a in enumerate(v)]
    d.polygon(P + [(x + w, y + h), (x, y + h)], fill=col[:3] + (55,)); d.line(P, fill=col, width=2, joint='curve')
    d.ellipse((P[-1][0] - 4, P[-1][1] - 4, P[-1][0] + 4, P[-1][1] + 4), fill=Wh)

short = lambda v: f'{v / 1e6:.2f}M' if v >= 1e6 else f'{v / 1e3:.0f}K' if v >= 1e4 else f'{v:,.0f}'
HX = lambda i: 44 + (((s0 + dt.timedelta(i)).toordinal() - (s0.toordinal() - s0.weekday())) // 7) * ((W - 88) / (N // 7 + 2))
CW = (W - 88) / (N // 7 + 2) - 2

def frame(t):
    dy = day(t); n = int(dy) + 1; i = min(n - 1, N - 1); fr = dy - int(dy)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dd = s0 + dt.timedelta(int(dy)); d.text((W / 2, 12), dd.strftime('%B ') + str(dd.day) + dd.strftime(', %Y'), font=f(30), fill=Wh, anchor='ma')
    p = lambda b: d.rounded_rectangle(b, 12, fill=PN)
    # speed
    p((24, 24, 330, 322)); d.text((44, 40), 'SPEED', font=f(16), fill=GR)
    d.text((44, 68), f'{wk[i]:,.0f}', font=f(50), fill=Wh); d.text((172, 90), 'commits this week', font=f(16, AR), fill=G)
    spark(d, 44, 126, 200, 40, wk, n, GR)
    d.text((44, 180), short(wkl[i]), font=f(38), fill=Wh); d.text((172, 194), 'lines added', font=f(16, AR), fill=G)
    spark(d, 44, 226, 200, 32, wkl, n, BL)
    d.text((44, 268), f'Best week {best[i]:,.0f}  ·  Best month {bestm[i]:,.0f}', font=f(17, AR), fill=G)
    if i > 7 and best[i] > best[max(0, i - 12)]: d.text((44, 292), 'New record', font=f(16), fill=OR)
    # AI mix
    p((24, 336, 330, 424)); d.text((44, 350), 'AI MIX', font=f(16), fill=GR); d.text((310, 352), 'attributed commits', font=f(14, AR), fill=Dim, anchor='ra')
    a = [cCl[i], cCx[i], cCu[i]]; s = max(sum(a), 1); xx = 44.0
    for v, col in zip(a, (OR, BL, PU)):
        w = 266 * v / s; d.rectangle((xx, 376, xx + w, 386), fill=col); xx += w
    d.text((44, 394), f'Claude {100 * a[0] / s:.0f}%', font=f(14), fill=OR); d.text((177, 394), f'Codex {100 * a[1] / s:.0f}%', font=f(14), fill=BL, anchor='ma'); d.text((310, 394), f'Cursor {100 * a[2] / s:.0f}%', font=f(14), fill=PU, anchor='ra')
    # world
    sn = [w for w in WO if w[0] <= dy]
    if sn:
        p((24, 438, 330, 650)); d.text((44, 454), 'THE WORLD', font=f(16), fill=GR)
        for k, (wd, nm, col) in enumerate(sn[-5:]):
            yy = 486 + k * 32; ds = s0 + dt.timedelta(wd); d.rectangle((44, yy + 2, 48, yy + 22), fill=col)
            d.text((58, yy + 2), ds.strftime('%b ') + str(ds.day), font=f(15, AR), fill=G); d.text((122, yy), nm, font=f(19), fill=col if dy - wd < 6 else Wh)
    # when
    p((24, 664, 330, 884)); d.text((44, 680), 'WHEN', font=f(16), fill=GR); d.text((310, 682), 'hour of day', font=f(14, AR), fill=Dim, anchor='ra')
    h = cH[i]; mx = max(h.max(), 1)
    for k in range(24):
        x = 44 + k * 11.1; b = 96 * h[k] / mx; col = PU if k >= 22 or k < 5 else GR
        d.rectangle((x, 806 - b, x + 8, 806), fill=col)
    for k, l in ((0, '12a'), (6, '6a'), (12, '12p'), (18, '6p')): d.text((44 + k * 11.1, 812), l, font=f(12, AR), fill=Dim)
    tot = max(cC[i], 1)
    d.text((44, 838), f'{100 * cL[i] / tot:.0f}%', font=f(26), fill=PU); d.text((100, 846), 'late night', font=f(14, AR), fill=G)
    d.text((190, 838), f'{100 * cW[i] / tot:.0f}%', font=f(26), fill=Wh); d.text((246, 846), 'weekends', font=f(14, AR), fill=G)
    # totals
    p((W - 340, 24, W - 24, 256)); d.text((W - 44, 40), 'SO FAR', font=f(16), fill=GR, anchor='ra')
    d.text((W - 44, 62), f'{cC[i]:,.0f}', font=f(50), fill=Wh, anchor='ra'); d.text((W - 44, 118), 'commits', font=f(16, AR), fill=G, anchor='ra')
    for k, (v, l) in enumerate(((f'{cP[i]:,.0f}', 'PRs merged'), (short(cA[i]), 'lines added'), (f'{seen[i]:,.0f}', 'repos'))):
        y = 146 + k * 34; d.text((W - 170, y), v, font=f(26), fill=Wh, anchor='ra'); d.text((W - 160, y + 7), l, font=f(16, AR), fill=G)
    # now on
    p((W - 340, 270, W - 24, 500)); d.text((W - 320, 286), 'WORKING ON', font=f(16), fill=GR); d.text((W - 44, 288), 'last 30 days', font=f(14, AR), fill=Dim, anchor='ra')
    w30 = byrepo[max(0, i - 29):i + 1].sum(axis=0); top = np.argsort(-w30)[:6]; mx = max(w30.max(), 1)
    for k, r in enumerate(x for x in top if w30[x] > 0):
        y = 316 + k * 30; bw = 276 * (w30[r] / mx) ** .4
        d.rectangle((W - 320, y + 20, W - 320 + bw, y + 24), fill=GR)
        if mask.hidden(repos[r]): mask.text(im, (W - 320, y), repos[r], f(16), Wh, 'la')
        else: d.text((W - 320, y), repos[r][:24], font=f(16), fill=Wh)
        d.text((W - 44, y), f'{w30[r]:,.0f}', font=f(15, AR), fill=G, anchor='ra')
    # streak
    p((W - 340, 514, W - 24, 620)); d.text((W - 320, 530), 'STREAK', font=f(16), fill=GR)
    d.text((W - 320, 552), f'{stk[i]:.0f}', font=f(42), fill=Wh); d.text((W - 320, 596), 'days running', font=f(14, AR), fill=G)
    d.text((W - 44, 552), f'{stkb[i]:.0f}', font=f(42), fill=OR, anchor='ra'); d.text((W - 44, 596), 'longest', font=f(14, AR), fill=G, anchor='ra')
    # heat grid
    p((24, 904, W - 24, 1068)); y0 = 916; ch = 16
    for k in range(N):
        x = HX(k); r = (s0 + dt.timedelta(k)).weekday(); on = k <= i
        lv = 0 if not on or not cnt[k] else 1 + int(np.searchsorted(heatq, cnt[k]))
        d.rectangle((x, y0 + r * (ch + 2), x + CW, y0 + r * (ch + 2) + ch), fill=HC[lv])
    for m in range((e0.year - s0.year) * 12 + e0.month - s0.month + 1):
        q = dt.date(s0.year + (s0.month - 1 + m) // 12, (s0.month - 1 + m) % 12 + 1, 1)
        if s0 <= q: d.text((HX((q - s0).days), y0 + 7 * (ch + 2) + 2), q.strftime('%b'), font=f(13, AR), fill=Dim)
    # AI releases as ticks along the top of the heat grid
    for wd, nm, col in WO:
        if 0 <= wd <= dy: d.rectangle((HX(wd) + CW / 2 - 1, y0 - 8, HX(wd) + CW / 2 + 1, y0 - 2), fill=col)
    return im

if __name__ == '__main__':
    if sys.argv[1] == 'test':
        t = float(sys.argv[2]); bg = Image.new('RGBA', (W, H), (15, 17, 23, 255))
        bg.paste(Image.open(sys.argv[3]).convert('RGBA'), (0, 0)); bg.alpha_composite(frame(t)); bg.convert('RGB').save(f'build/hud_{int(t)}.png'); sys.exit()
    out = sys.stdout.buffer
    for k in range(int(float(sys.argv[1]) * FPS)): out.write(frame(k / FPS).tobytes())
