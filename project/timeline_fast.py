"""FAST-PACED cut: auto-detected phrase regions, gaps trimmed to ~0.1 s, punch-in framing
alternating per phrase, short title stinger, compact end card, 120 BPM score."""
import json, wave, numpy as np
FPS = 25
def fr(t): return round(t * FPS) / FPS
W = '/tmp/claude-0/work/'

# --- speech regions from the enhanced dialogue
w = wave.open(W + 'dfout/src48_df24.wav'); SR = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = SR // 100; n = len(a) // hop
db = 20 * np.log10(np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
thr = -38.0
act = db > thr
regs = []; i = 0
while i < n:
    if act[i]:
        j = i
        while j < n and act[j]: j += 1
        regs.append([i / 100, j / 100]); i = j
    else: i += 1
fine = []
for r in regs:
    if fine and r[0] - fine[-1][1] < 0.10: fine[-1][1] = r[1]
    else: fine.append(r)
fine = [r for r in fine if r[1] - r[0] >= 0.06 and r[0] >= 1.0 and r[1] <= 56.3]
EXCL = (42.40, 46.90)            # false start "Tapi berapa rakyat... eh" + breath
fine = [r for r in fine if not (r[0] >= EXCL[0] and r[1] <= EXCL[1])]
# chunks: keep pauses < 0.25 s untouched; longer pauses (and the excluded section) become 0.15 s
chunks = []
for r in fine:
    if chunks and r[0] - chunks[-1][1] < 0.25: chunks[-1][1] = r[1]
    else: chunks.append(list(r))
reg = [[c[0] - 0.075, c[1] + 0.075] for c in chunks]
SPLITS = [8.62, 10.78, 50.66]                  # sentence boundary "...ada tak? | Sebab..." (title stinger goes here)
for sp in SPLITS:
    for i, (r0, r1) in enumerate(reg):
        if r0 < sp < r1:
            reg[i:i + 1] = [[r0, sp], [sp, r1]]; break
# --- framing per section (source-time based); alternate punch-in per phrase
def framing(src_t, k):
    if src_t < 4.4:   z, cx, cy = 1.00, 975, 520
    elif src_t < 9.0: z, cx, cy = 1.12, 985, 480
    elif src_t < 12.0: z, cx, cy = 1.26, 985, 440
    elif src_t < 20.3: z, cx, cy = 1.14, 900, 470
    elif src_t < 37.0: z, cx, cy = 1.00, 975, 520
    elif src_t < 46.0: z, cx, cy = 1.28, 760, 420
    elif src_t < 53.6: z, cx, cy = 1.18, 1120, 500
    else:             z, cx, cy = 1.38, 985, 410
    return z, cx, cy

EDL = []; t = 0.0; k = 0; prev_z = 0.0
TITLE_AFTER = 8.55   # stinger after "...ada tak?"
title_done = False
for s, e in reg:
    if not title_done and s > TITLE_AFTER:
        d = 1.40
        EDL.append(dict(id='TITLE', kind='ins', out=(fr(t), fr(t + d)))); t = fr(t + d); title_done = True
    s, e = fr(s), fr(e)
    z0, cx, cy = framing(s, k)
    cand = [z0, min(1.45, z0 * 1.13)] if k % 2 == 0 else [min(1.45, z0 * 1.13), z0]
    z = next((c for c in cand if abs(c - prev_z) >= 0.08), cand[0] if abs(cand[0] - prev_z) > abs(cand[1] - prev_z) else cand[1])
    if z > z0 + 1e-6: cy -= 30
    prev_z = z; k += 1
    EDL.append(dict(id=f'R{k}', kind='a', src=(s, e), zoom=(z, z * 1.02), cx=cx, cy=cy, out=(fr(t), fr(t + e - s))))
    t = fr(t + e - s)
END_D = 5.6
EDL.append(dict(id='END', kind='ins', out=(fr(t), fr(t + END_D))))
TOTAL = fr(t + END_D)

def map_src(x):
    best = None
    for E in EDL:
        if E['kind'] != 'a': continue
        if E['src'][0] - 1e-6 <= x <= E['src'][1] + 1e-6:
            return fr(E['out'][0] + x - E['src'][0])
        if E['src'][0] > x and best is None:
            best = E['out'][0]
    return best

from timeline import SUBS
subs = []
for s0, s1, ms, en in SUBS:
    subs.append(dict(t0=map_src(s0), t1=map_src(min(s1, 56.0)) if map_src(s1) else map_src(s0) + 1.5, ms=ms, en=en))
# fix ends that landed in trimmed gaps
for i, s in enumerate(subs):
    if s['t1'] is None or s['t1'] <= s['t0']: s['t1'] = s['t0'] + 1.2
    if i + 1 < len(subs): s['t1'] = min(s['t1'], subs[i + 1]['t0'] - 0.04)

M = map_src
seg = {E['id']: E['out'] for E in EDL}
first_after = lambda x: next(E for E in EDL if E['kind'] == 'a' and E['src'][0] >= x - 0.1)
last_before = lambda x: [E for E in EDL if E['kind'] == 'a' and E['src'][1] <= x + 0.1][-1]
q_end = seg['TITLE'][0]
EV = dict(
    hook=dict(t0=0.30, t1=M(4.25), count_at=M(2.06)),
    web1=dict(t0=M(4.36) - 0.05, t1=M(5.80) + 0.04),
    question=dict(t0=M(6.0), t1=q_end),
    title=dict(t0=seg['TITLE'][0], t1=seg['TITLE'][1]),
    map=dict(t0=M(12.00), t1=M(16.15), bina=M(12.45), jaga=M(13.20), urus=M(13.90), tenaga=M(14.40)),
    roles=dict(t0=M(16.30), t1=last_before(19.9)['out'][1], k=[M(16.45), M(17.10), M(18.05), M(19.05)]),
    jobs=dict(t0=M(22.15), t1=last_before(31.7)['out'][1], n37=M(23.05), pembinaan=M(25.95), n9=M(28.80)),
    web2=dict(t0=last_before(31.7)['out'][1], t1=last_before(36.9)['out'][1], hl=M(33.40)),
    quote=dict(t0=M(37.55), t1=last_before(42.5)['out'][1], bukan=M(38.96)),
    dci=dict(t0=M(47.30), t1=M(50.55)),
    suppliers=dict(t0=M(50.75), t1=last_before(53.5)['out'][1]),
    end=dict(t0=seg['END'][0], t1=seg['END'][1], sources=seg['END'][0] + 2.6),
)
T = TOTAL; ti = EV['title']['t0']; en = EV['end']['t0']
auto = dict(
    pad=[(0, 0.8), (ti - 0.1, 0.8), (ti, 1.0), (T - 1.5, 1.0), (T, 0)],
    arp=[(0, 0.9), (ti - 0.1, 0.9), (ti, 1.0), (ti + 1.4, 0.75), (en, 0.75), (en + 0.1, 1.0), (T - 1.2, 0.8), (T, 0)],
    bass=[(0, 0.7), (T - 1.2, 0.8), (T, 0)],
    drums=[(0, 0.55), (ti - 0.05, 0.55), (ti, 1.0), (en - 0.05, 1.0), (en, 0.55), (T - 1.5, 0.4), (T, 0)],
    boost=[(0, 1), (ti - 0.05, 1), (ti, 1.8), (ti + 1.35, 1.8), (ti + 1.5, 1), (en - 0.1, 1), (en + 0.2, 1.8), (T, 1.8)],
)
chapters = [
    dict(t0=0, t1=EV['web1']['t0'], n='01', label='Pelaburan'),
    dict(t0=EV['web1']['t1'], t1=q_end, n='01', label='Pelaburan'),
    dict(t0=seg['TITLE'][1], t1=EV['map']['t0'] - 0.5, n='02', label='Tenaga kerja'),
    dict(t0=EV['roles']['t1'], t1=EV['jobs']['t0'] - 0.5, n='03', label='Unjuran pekerjaan'),
    dict(t0=EV['web2']['t1'], t1=EV['end']['t0'], n='04', label='Ukuran kejayaan'),
]
out = dict(fps=FPS, total=TOTAL, edl=EDL, subs=subs, ev=EV, style='fast', bpm=120, auto=auto,
           chapters=chapters, warp=dict(title=2.0, web1=2.4, end=1.7), tail=dict(title=0, web1=0))
json.dump(out, open(W + 'timeline_fast.json', 'w'), indent=1)
if __name__ == '__main__':
    for E in EDL: print(E['id'], E.get('src'), E['out'], [round(v, 2) for v in E.get('zoom', [])])
    print('TOTAL', TOTAL, 'speech segments', sum(1 for E in EDL if E['kind'] == 'a'))
    for k2, v in EV.items(): print(k2, v)
    for s in subs: print(round(s['t0'], 2), round(s['t1'], 2), s['ms'])
