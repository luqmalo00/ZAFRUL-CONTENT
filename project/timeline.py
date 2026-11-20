"""Master edit timeline: EDL (source cuts), inserts, subtitles, graphic events.
All output times are in seconds on a 25 fps grid."""
import json

FPS = 25
def fr(t): return round(t * FPS) / FPS

# kind: 'a' = speaker footage (src in/out), 'ins' = full-screen insert (no source)
# zoom: (start, end) scale of speaker framing; cx, cy: source-pixel centre of crop
EDL = [
    dict(id='S1', kind='a', src=(0.95, 8.62),  zoom=(1.00, 1.07), cx=975, cy=520),
    dict(id='TITLE', kind='ins', dur=3.40),
    dict(id='WEB1', kind='ins', dur=4.20),
    dict(id='S2', kind='a', src=(9.10, 19.80), zoom=(1.16, 1.21), cx=985, cy=470),
    dict(id='S3', kind='a', src=(20.50, 31.55), zoom=(1.00, 1.03), cx=975, cy=520),
    dict(id='S4', kind='a', src=(31.85, 36.80), zoom=(1.00, 1.00), cx=975, cy=520),
    dict(id='S5', kind='a', src=(37.12, 42.42), zoom=(1.30, 1.34), cx=760, cy=420),
    dict(id='S6', kind='a', src=(46.92, 53.40), zoom=(1.18, 1.20), cx=1120, cy=500),
    dict(id='S7', kind='a', src=(53.70, 57.00), zoom=(1.36, 1.40), cx=985, cy=410),
    dict(id='END', kind='ins', dur=8.40),
]

t = 0.0
for e in EDL:
    if e['kind'] == 'a':
        e['src'] = (fr(e['src'][0]), fr(e['src'][1]))
        d = e['src'][1] - e['src'][0]
    else:
        d = fr(e['dur'])
    e['out'] = (fr(t), fr(t + d))
    t += d
TOTAL = fr(t)

def map_src(s):
    for e in EDL:
        if e['kind'] == 'a' and e['src'][0] - 1e-6 <= s <= e['src'][1] + 1e-6:
            return fr(e['out'][0] + s - e['src'][0])
    raise ValueError(s)

# Subtitles (verbatim Malay; English translation) keyed by SOURCE time ranges
SUBS = [
    (1.05, 4.30,  "Google nak labur 15 bilion USD di Malaysia.", "Google wants to invest 15 billion USD in Malaysia."),
    (4.36, 5.85,  "Bagus, ya.", "That's good."),
    (5.88, 8.55,  "Tapi kerja untuk rakyat kita, ada tak?", "But are there jobs for our people?"),
    (9.20, 12.00, "Sebab data center ini bukan sekadar bangunan penuh komputer.", "Because a data centre isn't just a building full of computers."),
    (12.00, 14.30, "Nak bina, nak jaga, nak urus —", "Building it, maintaining it, managing it —"),
    (14.32, 16.20, "semuanya perlukan tenaga kerja.", "all of it needs a workforce."),
    (16.35, 19.75, "Jurutera, juruteknik, kontraktor, orang logistik.", "Engineers, technicians, contractors, logistics people."),
    (20.60, 22.22, "Google jangka pelaburan terbaru ini", "Google expects this latest investment"),
    (22.24, 27.00, "akan menyokong lebih 37 ribu pekerjaan setahun semasa pembinaan.", "to support more than 37,000 jobs a year during construction."),
    (27.62, 31.30, "Bila beroperasi nanti, lebih 9 ribu pekerjaan setahun.", "Once operational, more than 9,000 jobs a year."),
    (31.97, 34.70, "Ini kerja yang diwujudkan oleh ekosistem Google,", "These are jobs created by Google's ecosystem —"),
    (35.33, 36.75, "bukan semuanya dengan Google.", "not all of them with Google itself."),
    (37.21, 38.92, "Bagi saya, ukuran kejayaan", "For me, the measure of success"),
    (38.96, 42.40, "bukan berapa bilion pelaburan diumumkan,", "isn't how many billions in investment are announced,"),
    (47.00, 50.40, "tapi berapa ramai rakyat Malaysia dapat kerja yang bagus,", "but how many Malaysians get good jobs,"),
    (50.70, 53.30, "dan berapa banyak syarikat tempatan dapat peluang.", "and how many local companies get opportunities."),
    (53.75, 56.20, "Itu yang kita kena pastikan.", "That is what we must make sure of."),
]
subs = [dict(t0=map_src(a), t1=map_src(b), ms=m, en=en) for a, b, m, en in SUBS]

seg = {e['id']: e['out'] for e in EDL}
# Graphic events (output time). Word anchors mapped from source time.
W = map_src
EV = dict(
    hook=dict(t0=W(1.6), t1=seg['S1'][0] + 3.30, count_at=W(2.06)),
    question=dict(t0=W(6.0), t1=seg['S1'][1]),
    title=dict(t0=seg['TITLE'][0], t1=seg['TITLE'][1]),
    web1=dict(t0=seg['WEB1'][0], t1=seg['WEB1'][1]),
    map=dict(t0=W(11.95), t1=W(16.20), bina=W(12.45), jaga=W(13.20), urus=W(13.90), tenaga=W(14.40)),
    roles=dict(t0=W(16.30), t1=seg['S2'][1], k=[W(16.45), W(17.10), W(18.05), W(19.05)]),
    jobs=dict(t0=W(22.10), t1=seg['S3'][1], n37=W(23.05), pembinaan=W(25.95), n9=W(28.80)),
    web2=dict(t0=seg['S4'][0], t1=seg['S4'][1], hl=W(33.40)),
    quote=dict(t0=W(37.60), t1=seg['S5'][1], bukan=W(38.96)),
    dci=dict(t0=W(47.40), t1=W(50.55)),
    suppliers=dict(t0=W(50.75), t1=seg['S6'][1]),
    end=dict(t0=seg['END'][0], t1=seg['END'][1], sources=seg['END'][0] + 4.0),
)

out = dict(fps=FPS, total=TOTAL, edl=EDL, subs=subs, ev=EV)
json.dump(out, open('/tmp/claude-0/work/timeline.json', 'w'), indent=1)
if __name__ == '__main__':
    for e in EDL: print(e['id'], e.get('src'), e['out'])
    print('TOTAL', TOTAL)
    for k, v in EV.items(): print(k, v)
