"""Voice edit + original synthesized score + SFX + ducking -> mix.wav (48 kHz stereo)."""
import json, subprocess, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
W = '/tmp/claude-0/work/'
TL = json.load(open(W + 'timeline.json'))
N = int(round(TL['total'] * SR))
rng = np.random.default_rng(7)

# ---------- VOICE ----------
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/tmp/claude-0/raw/C0019.MP4', '-vn',
                      '-af', 'pan=mono|c0=0.5*c0+0.5*c1', '-ar', str(SR), '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
src = np.frombuffer(raw, np.float32).copy()
voice = np.zeros(N, np.float32)
F = int(0.012 * SR)
for e in TL['edl']:
    if e['kind'] != 'a': continue
    a, b = int(round(e['src'][0] * SR)), int(round(e['src'][1] * SR))
    seg = src[a:b].copy()
    ramp = np.linspace(0, 1, F, dtype=np.float32)
    seg[:F] *= ramp; seg[-F:] *= ramp[::-1]
    o = int(round(e['out'][0] * SR))
    voice[o:o + len(seg)] += seg[:N - o]
voice.tofile(W + 'voice_raw.f32')
# clean: highpass, gentle denoise, de-mud EQ, presence, compression, normalise
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', W + 'voice_raw.f32',
                '-af', 'highpass=f=85,afftdn=nf=-32:nr=10,equalizer=f=250:t=q:w=1.2:g=-2,'
                       'equalizer=f=3500:t=q:w=1.0:g=2,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,'
                       'loudnorm=I=-17:TP=-2:LRA=7',
                '-ar', str(SR), '-f', 'f32le', W + 'voice_clean.f32'], check=True)
voice = np.fromfile(W + 'voice_clean.f32', np.float32)[:N]
voice = np.pad(voice, (0, N - len(voice)))

# ---------- MUSIC ----------
def env_adsr(n, a, r):
    e = np.ones(n, np.float32); A = min(int(a * SR), n // 2); R = min(int(r * SR), n // 2)
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x).astype(np.float32)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x).astype(np.float32)
def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x).astype(np.float32)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
t_all = np.arange(N) / SR

def pad_voice(freq, n, bright=10):
    t = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for det in (-0.07, 0.0, 0.08):
        f = freq * 2 ** (det / 12); ph = rng.uniform(0, 2 * np.pi)
        for k in range(1, bright + 1):
            if f * k > 9000: break
            y += (np.sin(2 * np.pi * f * k * t + ph * k) / k ** 1.25).astype(np.float32)
    return y / 3

BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT
# A minor progression, two bars each: Am9, Fmaj7, C(add9)/E, G6sus
CHORDS = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 69], [52, 55, 60, 62, 67], [55, 59, 62, 64, 69]]
ROOTS = [45, 41, 40, 43]
CH_LEN = 2 * BAR
padL = np.zeros(N, np.float32); padR = np.zeros(N, np.float32)
bass = np.zeros(N, np.float32); arp = np.zeros(N, np.float32); arpR = np.zeros(N, np.float32)
c = 0; t0 = 0.0
while t0 < TL['total']:
    ch = CHORDS[c % 4]; root = ROOTS[c % 4]
    a = int(t0 * SR); n = min(int((CH_LEN + 1.5) * SR), N - a)
    e = env_adsr(n, 1.2, 1.6)
    for i, m in enumerate(ch):
        v = pad_voice(hz(m), n) * e * 0.06
        pan = 0.3 + 0.4 * (i / (len(ch) - 1))
        padL[a:a + n] += v * (1 - pan); padR[a:a + n] += v * pan
    tb = np.arange(n) / SR
    bass[a:a + n] += (np.sin(2 * np.pi * hz(root - 12 + 12) * tb) * env_adsr(n, 0.4, 1.2) * 0.10).astype(np.float32)
    # 8th-note pluck arpeggio
    pattern = [0, 2, 1, 3, 4, 3, 1, 2]
    for s in range(16):
        ts = t0 + s * BEAT / 2
        if ts >= TL['total']: break
        m = ch[pattern[s % 8]] + 12
        k = int(ts * SR); L = min(int(0.9 * SR), N - k); tt = np.arange(L) / SR
        f = hz(m)
        note = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * np.sin(2 * np.pi * 3 * f * tt))
        note *= np.exp(-tt * 5.5) * np.minimum(1, tt / 0.004)
        vel = 0.05 * (1.0 if s % 2 == 0 else 0.7)
        pan = 0.5 + 0.35 * np.sin(s * 0.9)
        arp[k:k + L] += (note * vel * (1 - pan)).astype(np.float32); arpR[k:k + L] += (note * vel * pan).astype(np.float32)
    t0 += CH_LEN; c += 1

padL, padR = lp(padL, 2400), lp(padR, 2400)
arp, arpR = lp(arp, 5000), lp(arpR, 5000)
bass = lp(bass, 220)

# reverb (exponential noise IR)
ir_n = int(2.8 * SR); tir = np.arange(ir_n) / SR
irL = (rng.standard_normal(ir_n) * np.exp(-tir * 2.4)).astype(np.float32); irR = (rng.standard_normal(ir_n) * np.exp(-tir * 2.4)).astype(np.float32)
irL, irR = lp(irL, 6000) * 0.02, lp(irR, 6000) * 0.02
def verb(x, ir): return fftconvolve(x, ir)[:N].astype(np.float32)

# Section automation for arp / music intensity (output time)
ev = TL['ev']
def ramp_curve(points):
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    return np.interp(t_all, xs, ys).astype(np.float32)
T = TL['total']
arp_gain = ramp_curve([(0, 0.0), (7.3, 0.0), (7.7, 1.0), (15.0, 1.0), (15.6, 0.55), (56.8, 0.55), (57.2, 0.9), (T - 3.2, 0.7), (T, 0)])
pad_gain = ramp_curve([(0, 0.0), (0.6, 0.7), (7.4, 0.8), (7.7, 1.0), (15.2, 1.0), (16.0, 0.8), (57.0, 0.85), (57.4, 1.0), (T - 3.5, 1.0), (T, 0)])
bass_gain = ramp_curve([(0, 0), (7.6, 0), (7.7, 1), (T - 3, 1), (T, 0)])

mL = padL * pad_gain + arp * arp_gain + bass * bass_gain
mR = padR * pad_gain + arpR * arp_gain + bass * bass_gain
wetL = verb(padL * pad_gain + arp * arp_gain, irL); wetR = verb(padR * pad_gain + arpR * arp_gain, irR)
mL = mL + wetL * 0.9; mR = mR + wetR * 0.9

# ---------- SFX ----------
sfxL = np.zeros(N, np.float32); sfxR = np.zeros(N, np.float32)
def add(buf, x, t):
    k = int(t * SR); L = min(len(x), N - k)
    if L > 0 and k >= 0: buf[k:k + L] += x[:L]

def whoosh(dur=0.9, lo=300, hi=4000, gain=0.12):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    # four bands crossfaded to simulate a sweep
    t = np.linspace(0, 1, n); y = np.zeros(n, np.float32)
    bands = np.geomspace(lo, hi, 5)
    for i in range(4):
        b = bp(x, bands[i], bands[i + 1]); centre = (i + 0.5) / 4
        y += b * np.exp(-((t - centre) ** 2) / 0.04)
    e = np.sin(np.pi * t) ** 2
    return (y * e * gain).astype(np.float32)

def impact(gain=0.5):
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    nz = lp(rng.standard_normal(n).astype(np.float32), 900) * np.exp(-t * 12) * 0.6
    return ((boom + nz) * gain).astype(np.float32)

def riser(dur=1.4, gain=0.10):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    rev = verb(np.pad(hp(x, 1500) * np.exp(-np.arange(n) / SR * 3), (0, 0)), irL)[:n] if False else hp(x, 1200)
    e = (np.linspace(0, 1, n) ** 3)
    return (rev * e * gain).astype(np.float32)

def tick(gain=0.10):
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 90) * gain).astype(np.float32)

def pop(gain=0.09, f=880):
    n = int(0.25 * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 22) * gain).astype(np.float32)

# title: riser into impact
r = riser(1.3, 0.07); add(sfxL, r, ev['title']['t0'] - 1.3); add(sfxR, r, ev['title']['t0'] - 1.3)
im = impact(0.45); add(sfxL, im, ev['title']['t0']); add(sfxR, im, ev['title']['t0'])
for key in ['web1', 'map', 'jobs', 'web2', 'end']:
    w = whoosh(0.8, gain=0.10); tt = ev[key]['t0'] - 0.35
    add(sfxL, w * 0.8, tt); add(sfxR, w, tt + 0.01)
for key in ['map', 'jobs', 'web2', 'dci']:
    w = whoosh(0.6, 500, 5000, 0.05); add(sfxL, w, ev[key]['t1'] - 0.3); add(sfxR, w * 0.8, ev[key]['t1'] - 0.3)
add(sfxL, pop(0.08, 660), ev['hook']['t0']); add(sfxR, pop(0.08, 660), ev['hook']['t0'])
for i, k in enumerate(ev['roles']['k']):
    p = pop(0.06, [784, 880, 988, 1175][i]); add(sfxL, p, k); add(sfxR, p, k)
for key in ['bina', 'jaga', 'urus']:
    p = tick(0.07); add(sfxL, p, ev['map'][key]); add(sfxR, p, ev['map'][key])
for key in ['n37', 'n9']:
    p = pop(0.07, 1046); add(sfxL, p, ev['jobs'][key] + 0.9); add(sfxR, p, ev['jobs'][key] + 0.9)
for key in ['dci', 'suppliers']:
    p = pop(0.05, 880); add(sfxL, p, ev[key]['t0']); add(sfxR, p, ev[key]['t0'])
im2 = impact(0.25); add(sfxL, im2, ev['end']['t0']); add(sfxR, im2, ev['end']['t0'])
sfxL += verb(sfxL, irL) * 0.4; sfxR += verb(sfxR, irR) * 0.4

# ---------- DUCKING ----------
venv = np.abs(voice)
win = int(0.05 * SR)
venv = np.convolve(venv, np.ones(win) / win, 'same')
active = (venv > 0.01).astype(np.float32)
# attack fast, release slow
sm = np.zeros_like(active); g = 0.0
a_c, r_c = np.exp(-1 / (0.06 * SR)), np.exp(-1 / (0.6 * SR))
for i in range(0, N, 48):  # control-rate smoothing
    tgt = active[i]; coef = a_c ** 48 if tgt > g else r_c ** 48
    g = tgt + (g - tgt) * coef; sm[i:i + 48] = g
duck = (1.0 - 0.72 * sm).astype(np.float32)
boost = ramp_curve([(0, 1), (7.5, 1), (7.7, 2.0), (15.0, 2.0), (15.4, 1), (56.9, 1), (57.3, 2.0), (T, 2.0)])
duck = duck * boost
MUS = 0.55
L = voice + (mL * duck) * MUS + sfxL
R = voice + (mR * duck) * MUS + sfxR
mix = np.stack([L, R], 1)
mix /= max(1.0, np.abs(mix).max() / 0.95)
mix.astype(np.float32).tofile(W + 'mix.f32')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', W + 'mix.f32',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9', '-ar', str(SR), '-c:a', 'pcm_s16le', W + 'mix.wav'], check=True)
# stems for the editor
np.stack([mL * duck * MUS, mR * duck * MUS], 1).astype(np.float32).tofile(W + 'music.f32')
print('done', N / SR)
