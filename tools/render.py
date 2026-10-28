import base64, pathlib, sys
from playwright.sync_api import sync_playwright
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import importlib; POSTS = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "posts_2026_11").POSTS

here = pathlib.Path(__file__).parent
out = here / "out"; out.mkdir(exist_ok=True)
logo = base64.b64encode((here / "logo.png").read_bytes()).decode()

CSS = """
@font-face{font-family:Lora;src:url(file:///usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf);font-weight:400 700}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;font-family:Inter,sans-serif;position:relative;overflow:hidden}
.dark{background:#1E3A5F;color:#F6F1E6}
.light{background:#F5F1E6;color:#2A3A52}
.top{position:absolute;top:100px;left:100px;right:100px;display:flex;justify-content:space-between;align-items:center}
.tag{border:2px solid #B8924A;border-radius:40px;padding:14px 24px;font-size:24px;font-weight:600;letter-spacing:3.5px}
.dark .tag,.dark .num{color:#DDBF85}
.light .tag,.light .num{color:#7D5A1C}
.num{font-size:26px;font-weight:600;letter-spacing:2px}
h1{font-family:Lora;font-weight:600}
.dark em{font-style:normal;color:#DDBF85}
.light em{font-style:normal;color:#7D5A1C}
.light h1{color:#1E3A5F}
.foot{position:absolute;left:100px;right:100px;bottom:85px;border-top:2px solid #4E647B;padding-top:40px;display:flex;justify-content:space-between;align-items:center}
.foot img{height:80px;margin:-5px 0 -5px -5px}
.swipe{color:#DDBF85;font-size:30px;font-weight:600}
.hero{position:absolute;top:240px;left:100px;right:90px}
.hero h1{line-height:1.08}
.rule{width:120px;height:6px;background:#B8924A;border-radius:3px;margin:56px 0 48px}
.hero p{font-size:36px;line-height:1.5;color:#E4DED2;margin-right:20px}
.list{position:absolute;left:100px;right:100px;top:335px}
.item{display:flex;gap:28px;margin-bottom:38px}
.badge{flex:none;width:56px;height:56px;border-radius:50%;font-family:Lora;font-size:28px;font-weight:600;display:flex;align-items:center;justify-content:center}
.dark .badge{background:#B8924A;color:#1E3A5F}
.light .badge{background:#1E3A5F;color:#F6F1E6}
.item b{display:block;font-size:34px;font-weight:700;margin-bottom:8px;line-height:1.2}
.item p{font-size:31px;line-height:1.45}
.dark .item p{color:#E4DED2}
.cta{position:absolute;left:100px;right:100px;bottom:165px;background:#1E3A5F;border-radius:22px;padding:34px 40px;display:flex;justify-content:space-between;align-items:center}
.cta span{font-family:Lora;font-size:40px;font-weight:600;color:#F6F1E6}
.cta i{font-style:normal;color:#DDBF85;font-size:28px;font-weight:600}
.dis{position:absolute;left:100px;right:100px;bottom:80px;font-size:21px;color:#6B7486;line-height:1.4}
/* story */
.stag{position:absolute;top:250px;left:100px;border:2px solid #B8924A;border-radius:40px;padding:16px 26px;font-size:28px;font-weight:600;letter-spacing:4px;color:#DDBF85}
.sh{position:absolute;top:360px;left:100px;right:80px;line-height:1.05}
.card{position:absolute;top:640px;left:220px;width:640px;transform:rotate(-3deg);border:3px solid #8A8C88;border-radius:30px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,.35)}
.card img{display:block;width:100%}
.ssub{position:absolute;top:1475px;left:0;right:0;text-align:center;font-size:38px;line-height:1.45}
.ssub b{color:#DDBF85}
.slogo{position:absolute;top:1640px;left:0;right:0;text-align:center}
.slogo img{height:76px}
"""
FOOT = f'<div class="foot"><img src="data:image/png;base64,{logo}"><span class="swipe">Wischen →</span></div>'

def items(rows):
    return "".join(f'<div class="item"><div class="badge">{i}</div><div><b>{t}</b><p>{d}</p></div></div>' for i, (t, d) in enumerate(rows, 1))

def top(tag, n):
    return f'<div class="top"><span class="tag">{tag}</span><span class="num">{n} / 3</span></div>'

# Fit hero headline: largest size (<=92px) where headline is at most 4 lines and hero bottom stays above the footer
FIT1 = """() => { const h=document.querySelector('.hero h1'); const hero=document.querySelector('.hero');
 for (let s=92; s>=60; s-=2){ h.style.fontSize=s+'px'; const lines=Math.round(h.offsetHeight/(s*1.08));
   if (lines<=4 && hero.getBoundingClientRect().bottom < 1080) return s; } return -1; }"""
FIT_STORY = """() => { const h=document.querySelector('.sh');
 for (let s=100; s>=60; s-=2){ h.style.fontSize=s+'px'; if (h.getBoundingClientRect().bottom < 600) return s; } return -1; }"""
CHECK = """(limit) => { const l=document.querySelector('.list'); const r=l.lastElementChild.getBoundingClientRect(); return [Math.round(r.bottom), limit]; }"""

issues = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    def shot(html, name, h=1350):
        pg.set_viewport_size({"width": 1080, "height": h})
        pg.set_content(f"<html><head><meta charset=utf-8><style>{CSS}body{{height:{h}px}}</style></head>{html}</html>")
        pg.wait_for_timeout(250)
    for post in POSTS:
        s, m = post["slug"], post["date"][:7]
        (out / m).mkdir(exist_ok=True)
        # slide 1
        shot(f'<body class="dark">{top(post["tag"],1)}<div class="hero"><h1>{post["title"]}</h1><div class="rule"></div><p>{post["sub"]}</p></div>{FOOT}</body>', s)
        size = pg.evaluate(FIT1)
        if size < 0: issues.append(f"{s}-1 headline does not fit")
        pg.screenshot(path=str(out / m / f"{s}-1.png"))
        # slides 2, 3
        shot(f'<body class="dark">{top(post["tag"],2)}<h1 style="position:absolute;top:220px;left:100px;font-size:62px">{post["t2"]}</h1><div class="list">{items(post["i2"])}</div>{FOOT}</body>', s)
        bot, lim = pg.evaluate(CHECK, 1120)
        if bot > lim: issues.append(f"{s}-2 list bottom {bot} > {lim}")
        pg.screenshot(path=str(out / m / f"{s}-2.png"))
        shot(f'<body class="light">{top(post["tag"],3)}<h1 style="position:absolute;top:220px;left:100px;font-size:62px">{post["t3"]}</h1><div class="list">{items(post["i3"])}</div><div class="cta"><span>Beratung kostenfrei</span><i>Link in der Bio</i></div><p class="dis">{post["dis"]}</p></body>', s)
        bot, lim = pg.evaluate(CHECK, 1040)
        if bot > lim: issues.append(f"{s}-3 list bottom {bot} > {lim}")
        pg.screenshot(path=str(out / m / f"{s}-3.png"))
        for i in (1, 2, 3):
            Image.open(out / m / f"{s}-{i}.png").convert("RGB").save(out / m / f"{s}-{i}.jpg", quality=92)
        # story
        card = base64.b64encode((out / m / f"{s}-1.jpg").read_bytes()).decode()
        shot(f'<body class="dark"><span class="stag">NEUER POST</span><h1 class="sh">{post["story"]}</h1><div class="card"><img src="data:image/jpeg;base64,{card}"></div><p class="ssub">{post["story_sub"]}<br><b>Jetzt im Feed ansehen</b></p><div class="slogo"><img src="data:image/png;base64,{logo}"></div></body>', s, 1920)
        if pg.evaluate(FIT_STORY) < 0: issues.append(f"{s} story headline does not fit")
        pg.screenshot(path=str(out / m / f"story-{s}.png"))
        Image.open(out / m / f"story-{s}.png").convert("RGB").save(out / m / f"story-{s}.jpg", quality=92)
    b.close()
for f in out.rglob("*.png"): f.unlink()
print("ISSUES:", issues or "none")
