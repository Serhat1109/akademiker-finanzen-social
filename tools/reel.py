"""Erzeugt aus einem Post-Datensatz ein Reel (1080 x 1920, MP4, ohne Musik).

Aufruf: python3 tools/reel.py posts_2026_11 alle-privathaftpflicht [ausgabeordner]
Ablauf: Einstieg (Frage) -> Seite 2 mit nacheinander eingeblendeten Punkten
-> Seite 3 ebenso -> Abschluss mit "Beratung kostenfrei" und Hinweis.
"""
import base64, importlib, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
sys.path.insert(0, str(here))
POSTS = importlib.import_module(sys.argv[1]).POSTS
post = next(p for p in POSTS if p["slug"] == sys.argv[2])
outdir = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else here.parent / post["date"][:7])
outdir.mkdir(parents=True, exist_ok=True)
logo = base64.b64encode((here / "logo.png").read_bytes()).decode()

CSS = """
@font-face{font-family:Lora;src:url(file:///usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf);font-weight:400 700}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Inter,sans-serif;position:relative;overflow:hidden;background:#1E3A5F;color:#F6F1E6}
body.light{background:#F5F1E6;color:#2A3A52}
.tag{position:absolute;top:260px;left:100px;border:2px solid #B8924A;border-radius:40px;padding:16px 26px;font-size:28px;font-weight:600;letter-spacing:4px;color:#DDBF85}
.light .tag{color:#7D5A1C}
h1{font-family:Lora;font-weight:600;line-height:1.08}
em{font-style:normal;color:#DDBF85}
.light em{color:#7D5A1C}
.light h1{color:#1E3A5F}
.hook{position:absolute;top:400px;left:100px;right:90px;font-size:108px}
.rule{position:absolute;left:100px;width:140px;height:7px;background:#B8924A;border-radius:4px}
.sub{position:absolute;left:100px;right:110px;font-size:44px;line-height:1.45;color:#E4DED2}
.h2{position:absolute;top:400px;left:100px;right:90px;font-size:80px}
.list{position:absolute;top:680px;left:100px;right:100px}
.item{display:flex;gap:32px;align-items:flex-start;margin-bottom:72px}
.item.off{visibility:hidden}
.badge{flex:none;width:72px;height:72px;border-radius:50%;font-family:Lora;font-size:36px;font-weight:600;display:flex;align-items:center;justify-content:center;background:#B8924A;color:#1E3A5F}
.light .badge{background:#1E3A5F;color:#F6F1E6}
.item b{display:block;font-size:62px;font-weight:700;line-height:1.2;padding-top:6px}
.item p{font-size:36px;line-height:1.4;margin-top:10px;color:#E4DED2}
.light .item p{color:#2A3A52}
.logo{position:absolute;top:1560px;left:0;right:0;text-align:center}
.logo img{height:80px}
.cta{position:absolute;top:760px;left:100px;right:100px;background:#1E3A5F;border-radius:28px;padding:56px 50px;text-align:center}
.cta span{display:block;font-family:Lora;font-size:72px;font-weight:600;color:#F6F1E6}
.cta i{display:block;font-style:normal;color:#DDBF85;font-size:46px;font-weight:600;margin-top:18px}
.dis{position:absolute;top:1180px;left:100px;right:100px;text-align:center;font-size:30px;line-height:1.45;color:#6B7486}
"""
LOGO = f'<div class="logo"><img src="data:image/png;base64,{logo}"></div>'

def page(body, cls=""):
    return f"<html><head><meta charset=utf-8><style>{CSS}</style></head><body class='{cls}'>{body}</body></html>"

def items(rows, shown):
    return "".join(f'<div class="item{"" if i < shown else " off"}"><div class="badge">{i+1}</div><div><b>{t}</b></div></div>'
                   for i, (t, d) in enumerate(rows))

frames = []  # (html, seconds)
frames.append((page(f'<span class="tag">{post["tag"]}</span><h1 class="hook">{post.get("reel_hook", post["story"])}</h1>'
                    f'<div class="rule" id="r"></div><p class="sub" id="s">{post["sub"]}</p>{LOGO}'), 3.0))
for key_t, key_i, cls in (("t2", "i2", ""), ("t3", "i3", "light")):
    rows = post[key_i]
    for n in range(1, len(rows) + 1):
        hold = 2.4 if n == len(rows) else 1.2
        frames.append((page(f'<span class="tag">{post["tag"]}</span><h1 class="h2">{post[key_t]}</h1><div class="list">{items(rows, n)}</div>{LOGO if cls=="" else ""}', cls), hold))
frames.append((page(f'<div class="cta"><span>Beratung kostenfrei</span><i>Link in der Bio</i></div><p class="dis">{post["dis"]}</p>', "light"), 3.0))

tmp = pathlib.Path(tempfile.mkdtemp())
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for i, (html, _) in enumerate(frames):
        pg.set_content(html); pg.wait_for_timeout(200)
        # Untertitel und Linie unter die Einstiegsfrage setzen, Schrift ggf. verkleinern
        pg.evaluate("""() => { const h=document.querySelector('.hook'); if(!h) return;
          for (let s=108; s>=70; s-=4){ h.style.fontSize=s+'px'; if (h.getBoundingClientRect().bottom < 1050) break; }
          const y=h.getBoundingClientRect().bottom; document.getElementById('r').style.top=(y+60)+'px';
          document.getElementById('s').style.top=(y+120)+'px'; }""")
        over = pg.evaluate("() => { const l=document.querySelector('.list'); return l ? l.lastElementChild.getBoundingClientRect().bottom : 0 }")
        if over > 1520: print(f"WARNUNG: Bild {i} Liste reicht bis {over:.0f}px")
        pg.screenshot(path=str(tmp / f"f{i:02d}.png"))
    b.close()

# Bilder mit kurzen Überblendungen zu einem Video zusammensetzen (30 fps, H.264, stumme Tonspur für Kompatibilität)
fade = 0.25
inputs, filt, last, offset = [], [], "0:v", 0.0
for i, (_, sec) in enumerate(frames):
    inputs += ["-loop", "1", "-t", f"{sec + fade:.2f}", "-i", str(tmp / f"f{i:02d}.png")]
for i in range(1, len(frames)):
    offset += frames[i - 1][1]
    filt.append(f"[{last}][{i}:v]xfade=transition=fade:duration={fade}:offset={offset:.2f}[v{i}]")
    last = f"v{i}"
total = sum(s for _, s in frames) + fade
out = outdir / f"reel-{post['slug']}.mp4"
cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
       "-filter_complex", ";".join(filt) + f";[{last}]format=yuv420p,fps=30[out]",
       "-map", "[out]", "-map", f"{len(frames)}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
       "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(out)]
subprocess.run(cmd, check=True)
# Vorschaubild = Einstiegsbild
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "f00.png"), "-q:v", "3", str(outdir / f"reel-{post['slug']}-cover.jpg")], check=True)
print(out, f"{total:.1f}s")
