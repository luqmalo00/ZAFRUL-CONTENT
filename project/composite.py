"""Composite: graded/reframed speaker footage + transparent motion-graphics overlay -> video.
usage: composite.py test <overlay_dir> t1 t2 ...   |   composite.py full <frames_dir> <out.mp4>"""
import sys, json, subprocess, numpy as np, cv2, os

W = '/tmp/claude-0/work/'
SRC = '/tmp/claude-0/raw/C0019.MP4'
TL = json.load(open(W + 'timeline.json'))
FPS = TL['fps']; OW, OH = 1920, 1080

# --- grade: gentle S-curve, slight warmth in highlights, +6% saturation, soft vignette
x = np.arange(256) / 255.0
s = x + 0.06 * np.sin(2 * np.pi * x) * -0.5 * (1 - x) * 2  # mild S
s = np.clip(0.985 * s + 0.008, 0, 1)
lut_r = np.clip((s + 0.008 * x) * 255, 0, 255).astype(np.uint8)
lut_g = np.clip(s * 255, 0, 255).astype(np.uint8)
lut_b = np.clip((s - 0.010 * x) * 255, 0, 255).astype(np.uint8)
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
r = np.sqrt(((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2)
VIG = (1 - 0.16 * np.clip(r - 0.55, 0, 1) ** 1.6 / 0.6)[..., None].astype(np.float32)

def grade(rgb):
    out = np.dstack([cv2.LUT(rgb[..., 0], lut_r), cv2.LUT(rgb[..., 1], lut_g), cv2.LUT(rgb[..., 2], lut_b)])
    hsv = cv2.cvtColor(out, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.06, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    return out * VIG

def reframe(rgb, zoom, cx, cy):
    if abs(zoom - 1) < 1e-4 and cx == 960 and cy == 540:
        return rgb
    hw, hh = OW / zoom / 2, OH / zoom / 2
    cx = min(max(cx, hw), OW - hw); cy = min(max(cy, hh), OH - hh)
    M = np.float32([[zoom, 0, OW / 2 - zoom * cx], [0, zoom, OH / 2 - zoom * cy]])
    out = cv2.warpAffine(rgb, M, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if zoom > 1.12:  # light unsharp mask to offset upscale softness
        bl = cv2.GaussianBlur(out, (0, 0), 1.2)
        out = cv2.addWeighted(out, 1.35, bl, -0.35, 0)
    return out

def seg_at(t):
    for e in TL['edl']:
        if e['out'][0] - 1e-6 <= t < e['out'][1] - 1e-6:
            return e
    return TL['edl'][-1]

def zoom_at(e, t):
    k = (t - e['out'][0]) / max(1e-6, e['out'][1] - e['out'][0])
    k = k * k * (3 - 2 * k)
    return e['zoom'][0] + (e['zoom'][1] - e['zoom'][0]) * k

def over(base, png_path):
    ov = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
    if ov is None:
        return base
    ov = cv2.cvtColor(ov, cv2.COLOR_BGRA2RGBA).astype(np.float32)
    a = ov[..., 3:4] / 255.0
    return base * (1 - a) + ov[..., :3] * a

def grab(src_t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{src_t:.3f}', '-i', SRC, '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(OH, OW, 3)

def base_frame(t, rgb):
    e = seg_at(t)
    if e['kind'] != 'a':
        return np.zeros((OH, OW, 3), np.float32)
    return reframe(grade(rgb), zoom_at(e, t), e['cx'], e['cy'])

if sys.argv[1] == 'test':
    d = sys.argv[2]
    for ts in sys.argv[3:]:
        t = float(ts); e = seg_at(t)
        rgb = grab(e['src'][0] + t - e['out'][0]) if e['kind'] == 'a' else None
        b = base_frame(t, rgb) if rgb is not None else np.zeros((OH, OW, 3), np.float32)
        img = over(b, f'{d}/t_{t:.2f}.png')
        cv2.imwrite(f'{d}/c_{t:.2f}.jpg', cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    sys.exit()

# ---- full render
frames_dir, out = sys.argv[2], sys.argv[3]
n = int(round(TL['total'] * FPS))
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                        '-i', W + 'mix.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                        '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
fi = 0
for e in TL['edl']:
    nf = int(round((e['out'][1] - e['out'][0]) * FPS))
    if e['kind'] == 'a':
        dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f"{e['src'][0]:.3f}", '-i', SRC, '-t', f"{nf / FPS + 0.2:.3f}",
                                '-vf', f'fps={FPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    for i in range(nf):
        t = fi / FPS
        if e['kind'] == 'a':
            buf = dec.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                rgb = last
            else:
                rgb = np.frombuffer(buf, np.uint8).reshape(OH, OW, 3); last = rgb
            b = base_frame(t, rgb)
        else:
            b = np.zeros((OH, OW, 3), np.float32)
        img = over(b, f'{frames_dir}/f_{fi:05d}.png')
        enc.stdin.write(np.clip(img + 0.5, 0, 255).astype(np.uint8).tobytes())
        fi += 1
    if e['kind'] == 'a':
        dec.stdout.close(); dec.wait()
    print(e['id'], fi, flush=True)
enc.stdin.close(); enc.wait()
print('frames', fi, 'expected', n)
