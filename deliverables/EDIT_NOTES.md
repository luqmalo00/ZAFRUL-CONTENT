# Edit notes: Google US$15B Malaysia explainer

**Source:** `C0019.MP4`: 59.8 s, 1080p50, single camera, lavalier audio, speech in Malay.
**Output:** `google-malaysia-us15b-explainer.mp4`: 65.4 s, 1920×1080, 25 fps, H.264 + AAC, −16 LUFS. Malay subtitles are burned in.

## Full transcript (verbatim, source timecodes)
```
00.9  Google nak labur 15 bilion USD di Malaysia. Bagus ya.
05.9  Tapi kerja untuk rakyat kita ada tak?
09.2  Sebab data center ini bukan sekadar bangunan penuh komputer.
12.0  Nak bina, nak jaga, nak urus — semuanya perlukan tenaga kerja.
16.3  Jurutera, juruteknik, kontraktor, orang logistik.
20.6  Google jangka pelaburan terbaru ini akan menyokong lebih 37 ribu pekerjaan setahun semasa pembinaan.
27.6  Bila beroperasi nanti lebih 9 ribu pekerjaan setahun.
32.0  Ini kerja yang diwujudkan oleh ekosistem Google. Bukan semuanya dengan Google.
37.2  Bagi saya, ukuran kejayaan bukan berapa bilion pelaburan diumumkan.
42.7  [Tapi berapa rakyat — eh —]   ← false start, removed
47.0  Tapi berapa ramai rakyat Malaysia dapat kerja yang bagus,
50.7  dan berapa banyak syarikat tempatan dapat peluang.
53.8  Itu yang kita kena pastikan.
```

## Editorial decisions
- **The speaker's order is kept.** The clip already runs hook → explanation → numbers → thesis → call to action, so reordering it would weaken it.
- **One removal:** the false start "Tapi berapa rakyat… eh" (42.3–46.9 s). The restarted sentence follows "pelaburan diumumkan" directly, so the meaning is unchanged.
- **Tightened pauses** at 19.8 s, 31.6 s and 53.4 s. Every cut lands in measured silence.
- **Jump cuts** are hidden by changing the framing at each cut (wide / medium / speaker-right / speaker-left / close) or by cutting under a full-screen graphic.
- **No words were added, re-timed or reordered** within a sentence.

## Structure (output timecodes)
| Time | Section | Visual |
|---|---|---|
| 0:00–0:07.6 | Opening hook | Speaker wide; animated "US$15 BILION" counter; "KERJA UNTUK RAKYAT?" |
| 0:07.6–0:11.0 | Title | Full-screen title card with impact hit |
| 0:11.0–0:15.2 | Context | Browser view of Google's official press release, headline highlighted |
| 0:15.2–0:25.9 | Workforce | Speaker medium → campus map (Elmina, Selangor, N. Sembilan) with BINA / JAGA / URUS → role list |
| 0:25.9–0:37.0 | The numbers | Speaker → infographic: 37,000+ (construction) vs 9,000+ (operations), bars to scale, 6,000 / US$1.1B / 45% |
| 0:37.0–0:42.0 | Ecosystem | Press release paragraph with highlights: specialists, contractors and local suppliers, shops and restaurants |
| 0:42.0–0:47.2 | Thesis | Speaker framed right; "bukan berapa bilion" typography with strike-through |
| 0:47.2–0:53.7 | What to ensure | Speaker framed left; cards for Data Center Institutes (TVET) and 80+ Malaysian suppliers |
| 0:53.7–0:57.0 | Closing line | Close shot, subtitle only: "Itu yang kita kena pastikan." |
| 0:57.0–1:05.4 | End | Closing quote in the speaker's own words → sources card → fade out |

## Fast-paced version (`google-malaysia-us15b-explainer-fast.mp4`, 53.4 s)
- **Same content, same order, same graphics and sources.** Only the pace changes.
- **Pauses:** every pause of 0.25 s or longer is cut down to 0.15 s. Shorter pauses are left alone so no word is clipped, and the false start is removed as before.
- **18 speaker shots instead of 7.** The framing punches in and out on alternate phrases, and consecutive shots always differ by at least 8% zoom so the cuts read as deliberate.
- **Title:** a 1.4 s stinger after "…ada tak?", replacing the 3.4 s title card. The press-release shot now plays under "Bagus, ya." instead of in silence.
- **Animations:** title, browser and end-card animations run about 2× faster.
- **Music:** a 120 BPM version of the score with kick, clap and 16th-note hats. A light groove plays from the first frame and the full beat drops at the title.
- **Subtitles:** `subtitles_fast_ms.srt` and `subtitles_fast_en.srt`.

## Portrait version (`google-malaysia-us15b-explainer-fast-portrait.mp4`, 1080×1920, 53.4 s)
- **Edit:** the same as the fast-paced cut, with the same audio and subtitles (`subtitles_fast_*.srt`).
- **Stacked layout:** the speaker fills the top 1220 px at about 1.13–1.3× scale, so it stays close to native resolution. A full-bleed 9:16 crop would have needed about 1.78× upscaling.
- **Bottom panel:** carries the chapter label, the panel graphics (US$15B counter, "KERJA UNTUK RAKYAT?", role chips, the quote, and the TVET and supplier cards) and large subtitles.
- **Full-screen graphics:** title, press release, map, job numbers, ecosystem, end card and sources are re-laid out vertically.

## Audio clarity pass (both versions)
- **Noise:** the dialogue goes through the DeepFilterNet3 speech-enhancement model, with noise reduction capped at 24 dB so the voice still sounds natural. Background hum and room noise drop by about 22 dB, and the voice itself changes by about 1 dB.
- **EQ for a chest-mounted lav:**
  - double high-pass at 70–90 Hz
  - −3 dB at 180 Hz and −3.5 dB at 380 Hz to remove boom and boxiness
  - +5 dB at 3 kHz and +2 dB at 5.5 kHz for presence
  - +3 dB high shelf at 8 kHz for air
- **Dynamics:** de-esser, 3.5:1 compression and a limiter.
- **Result:**
  - The presence band (1–4 kHz) is now about 10 dB below the low-mids, compared with about 17 dB before.
  - The music ducks about 15 dB under speech (previously about 11 dB), so it sits roughly 25 dB below the voice.

## Look and sound
- **Grade:** gentle S-curve, slightly warm highlights, saturation +6%, soft vignette. Skin tones are kept natural.
- **Typography:** Inter / Inter Tight (UI and numbers), Instrument Serif (quotes), JetBrains Mono (URLs).
- **Colour:** dark navy surfaces, with Google's four brand colours used only as accents.
- **Voice:** see "Audio clarity pass" above.
- **Music:** an original score synthesised for this project (A-minor ambient pad, pluck arpeggio, sub). It is royalty-free with no licence risk. It ducks about 11 dB under speech and lifts in the title and end sections.
- **Sound design:** riser and impact on the title, whooshes on graphic transitions, soft pops on data reveals.

## Not included
- **Stock B-roll** (data-centre interiors) and **press imagery:** no licensed library was reachable from the editing environment. Approved Google press B-roll can go over 0:15–0:18 or 0:37–0:42 if you have it.
- **Name/title lower third:** not added, because the speaker's preferred name and title weren't given. It is easy to add.

## Reproducing or re-editing
All project files are in `project/`. Run `timeline.py` (edit list, subtitles, cue times) → `audio_build.py` → `node render.js full frames 0 N` → `composite.py full frames out.mp4`.
