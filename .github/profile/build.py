"""Build apratxxm profile README panels (SVG) from GitHub data."""
import base64, hashlib, io, json, os, re, urllib.request, datetime as dt
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.environ.get("OUT_DIR", os.path.join(ROOT, "..", "..", "assets"))
os.makedirs(OUT, exist_ok=True)
QUERY = 'query{user(login:"apratxxm"){name bio location createdAt followers{totalCount} repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){totalCount nodes{name description stargazerCount isFork primaryLanguage{name color} languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}} bg:repository(name:"branchglance"){releases(first:1,orderBy:{field:CREATED_AT,direction:DESC}){nodes{tagName isPrerelease}}} contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}'

def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN")
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": QUERY}).encode(),
                                 headers={"Authorization": "bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise SystemExit("GraphQL error: %s" % body["errors"])
    return body["data"]["user"]

U = fetch()
_rel = (U.get("bg") or {}).get("releases", {}).get("nodes") or []
BG_TAG = (_rel[0]["tagName"] + (" alpha" if _rel[0]["isPrerelease"] or _rel[0]["tagName"].startswith("v0.") else "")) if _rel else "alpha"
C = U["contributionsCollection"]
DAYS = [d for w in C["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
WEEKS = C["contributionCalendar"]["weeks"]
REPOS = {r["name"]: r for r in U["repositories"]["nodes"]}

# ---------- palette ----------
BG = "#0b0f17"; CARD = "#111823"; LINE = "#1f2937"; INK = "#e6edf3"; DIM = "#8b949e"; FAINT = "#4b5563"
GREEN = "#4ade80"; PHOS = "#86efac"; PHOS_DIM = "#2f6b45"; CYAN = "#22d3ee"; GOLD = "#facc15"; AMBER = "#f59e0b"
WOOD = "#6b4428"; WOOD_D = "#4a2e1a"; WOOD_L = "#8a5a35"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

# ---------- 5x7 pixel font ----------
G = {
"A":"01110 10001 10001 11111 10001 10001 10001","B":"11110 10001 10001 11110 10001 10001 11110",
"C":"01110 10001 10000 10000 10000 10001 01110","D":"11110 10001 10001 10001 10001 10001 11110",
"E":"11111 10000 10000 11110 10000 10000 11111","F":"11111 10000 10000 11110 10000 10000 10000",
"G":"01110 10001 10000 10111 10001 10001 01111","H":"10001 10001 10001 11111 10001 10001 10001",
"I":"01110 00100 00100 00100 00100 00100 01110","J":"00111 00010 00010 00010 00010 10010 01100",
"K":"10001 10010 10100 11000 10100 10010 10001","L":"10000 10000 10000 10000 10000 10000 11111",
"M":"10001 11011 10101 10101 10001 10001 10001","N":"10001 10001 11001 10101 10011 10001 10001",
"O":"01110 10001 10001 10001 10001 10001 01110","P":"11110 10001 10001 11110 10000 10000 10000",
"Q":"01110 10001 10001 10001 10101 10010 01101","R":"11110 10001 10001 11110 10100 10010 10001",
"S":"01111 10000 10000 01110 00001 00001 11110","T":"11111 00100 00100 00100 00100 00100 00100",
"U":"10001 10001 10001 10001 10001 10001 01110","V":"10001 10001 10001 10001 10001 01010 00100",
"W":"10001 10001 10001 10101 10101 10101 01010","X":"10001 10001 01010 00100 01010 10001 10001",
"Y":"10001 10001 01010 00100 00100 00100 00100","Z":"11111 00001 00010 00100 01000 10000 11111",
"0":"01110 10011 10101 10101 10101 11001 01110","1":"00100 01100 00100 00100 00100 00100 01110",
"2":"01110 10001 00001 00010 00100 01000 11111","3":"11110 00001 00001 01110 00001 00001 11110",
"4":"00010 00110 01010 10010 11111 00010 00010","5":"11111 10000 11110 00001 00001 10001 01110",
"6":"00110 01000 10000 11110 10001 10001 01110","7":"11111 00001 00010 00100 01000 01000 01000",
"8":"01110 10001 10001 01110 10001 10001 01110","9":"01110 10001 10001 01111 00001 00010 01100",
" ":"00000 00000 00000 00000 00000 00000 00000",">":"11000 01100 00110 00011 00110 01100 11000",
".":"00000 00000 00000 00000 00000 01100 01100","%":"11001 11010 00010 00100 01000 01011 10011",
"-":"00000 00000 00000 01110 00000 00000 00000","/":"00001 00010 00010 00100 01000 01000 10000",
"·":"00000 00000 00000 00100 00000 00000 00000",":":"00000 01100 01100 00000 01100 01100 00000",
"@":"01110 10001 10111 10101 10111 10000 01110","+":"00000 00100 00100 11111 00100 00100 00000",
"'":"00100 00100 01000 00000 00000 00000 00000","→":"00000 00100 00010 11111 00010 00100 00000",
",":"00000 00000 00000 00000 00110 00100 01000","*":"00000 10101 01110 11111 01110 10101 00000","_":"00000 00000 00000 00000 00000 00000 11111","$":"00100 01111 10100 01110 00101 11110 00100",
}

def pw(s, px):  # pixel text width
    return len(s) * 6 * px - px

def ptext(s, x, y, px, fill, extra=""):
    d = []
    for i, ch in enumerate(s.upper()):
        rows = G.get(ch, G[" "]).split()
        for r, row in enumerate(rows):
            c = 0
            while c < 5:
                if row[c] == "1":
                    run = 1
                    while c + run < 5 and row[c + run] == "1":
                        run += 1
                    d.append(f"M{x + (i*6 + c)*px} {y + r*px}h{run*px}v{px}h-{run*px}z")
                    c += run
                else:
                    c += 1
    return f'<path d="{"".join(d)}" fill="{fill}" shape-rendering="crispEdges" {extra}/>'

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def wrap(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + (1 if cur else 0) > n:
            out.append(cur); cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return out + ([cur] if cur else [])

def svg(w, h, body, label, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}"><style>.s{{font-family:{SANS}}}.m{{font-family:{MONO}}}{style}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>{body}</svg>\n')

def save(name, s):
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(s)

def card(w, h, fill=CARD):
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{fill}" stroke="{LINE}"/>'

def kfmt(n):
    return f"{n/1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)

# ---------- stats ----------
counts = [d["contributionCount"] for d in DAYS]
today = DAYS[-1]
best = cur = run = 0
for c in counts:
    run = run + 1 if c else 0
    best = max(best, run)
i = len(counts) - 1
if counts[i] == 0:
    i -= 1
while i >= 0 and counts[i]:
    cur += 1; i -= 1
_lang = {}
for _r in REPOS.values():
    if _r["isFork"]:
        continue
    for _e in _r["languages"]["edges"]:
        _n = _e["node"]["name"]; _c, _sz = _lang.get(_n, (_e["node"]["color"] or "#8b949e", 0))
        _lang[_n] = (_c, _sz + _e["size"])
_tot = sum(v[1] for v in _lang.values()) or 1
LANG_PILLS = [(f"{n} {max(1, round(sz * 100 / _tot))}%", c) for n, (c, sz) in sorted(_lang.items(), key=lambda kv: -kv[1][1])[:4]]
TOTAL = C["contributionCalendar"]["totalContributions"]
COMMITS = C["totalCommitContributions"]; PRS = C["totalPullRequestContributions"]
STARS = sum(r["stargazerCount"] for r in REPOS.values() if not r["isFork"])
NREPOS = sum(1 for r in REPOS.values() if not r["isFork"] and r["name"] != "apratxxm")
ACTIVE = sum(1 for c in counts if c)
BUSIEST = max(counts)
LAST30 = sum(counts[-30:])
STAMP = dt.date.fromisoformat(today["date"]).strftime("%b %d, %Y")

# ================= 1. HERO: pixel room + Legion monitor =================
def sig_path_d(grid, ox, oy, cell):
    d = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == "1":
                k = c
                while k < len(row) and row[k] == "1":
                    k += 1
                d.append(f"M{ox+c*cell:g} {oy+r*cell:g}h{(k-c)*cell:g}v{cell:g}h-{(k-c)*cell:g}z")
                c = k
            else:
                c += 1
    return "".join(d)

def hero():
    W, H, RH = 840, 580, 400
    FLOOR = 346
    b = [f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
         f'<filter id="ng" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>'
         f'<filter id="rgb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>'
         f'<linearGradient id="gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".05"/><stop offset=".4" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
         f'<g clip-path="url(#c)">']
    # wall
    b.append(f'<rect width="{W}" height="{RH}" fill="#1b2233"/>')
    b += [f'<rect x="{x}" y="0" width="22" height="{FLOOR}" fill="#1f2740"/>' for x in range(0, W, 44)]
    # small window, left
    wx, wy, ww, wh = 56, 86, 112, 96
    b.append(f'<rect x="{wx-6}" y="{wy-6}" width="{ww+12}" height="{wh+12}" fill="#111622"/><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="#24304d"/>')
    for x, y in [(66, 96), (140, 100), (152, 150), (84, 160), (118, 132)]:
        b.append(f'<rect x="{x}" y="{y}" width="2" height="2" fill="#c7d2fe"/>')
    b.append(f'<rect x="134" y="104" width="14" height="14" fill="#fef3c7"/><rect x="139" y="104" width="9" height="9" fill="#24304d"/>')
    b.append(f'<rect x="{wx+ww//2-2}" y="{wy}" width="4" height="{wh}" fill="#111622"/><rect x="{wx}" y="{wy+wh//2-2}" width="{ww}" height="4" fill="#111622"/>')
    b.append(f'<rect x="{wx-14}" y="{wy+wh+6}" width="{ww+28}" height="8" fill="{WOOD_L}"/><rect x="{wx-14}" y="{wy+wh+14}" width="{ww+28}" height="3" fill="{WOOD_D}"/>')
    # plant on the sill
    py = wy + wh + 6
    b.append(f'<rect x="66" y="{py-18}" width="20" height="18" fill="#b45f3c"/><rect x="64" y="{py-20}" width="24" height="4" fill="#c2703f"/>')
    b.append(f'<rect x="74" y="{py-44}" width="4" height="24" fill="#22c55e"/><rect x="78" y="{py-38}" width="10" height="4" fill="#22c55e"/><rect x="64" y="{py-32}" width="10" height="4" fill="#16a34a"/><rect x="78" y="{py-48}" width="8" height="4" fill="#16a34a"/>')
    # pixel neon signature
    mode = os.environ.get("SIGN", "neon")
    sig_px = os.path.join(SRC, "signature_px.txt")
    if mode == "neon" and os.path.exists(sig_px):
        grid = open(sig_px).read().split()
        cell = 2.5; gw_ = len(grid[0]) * cell
        ox, oy = 420 - gw_ / 2, 4
        d = sig_path_d(grid, ox, oy, cell)
        steps = 24
        vals = ";".join(str(round((gw_ + 8) * i / steps)) for i in range(steps + 1))
        b.append(f'<clipPath id="wr"><rect x="{ox-4:g}" y="0" width="{gw_+8:g}" height="{RH}"><animate attributeName="width" values="{vals}" dur="2.4s" begin="0s" fill="freeze" calcMode="discrete"/></rect></clipPath>')
        b.append(f'<g clip-path="url(#wr)" class="nf"><path d="{d}" fill="#8f7ff0" filter="url(#ng)" opacity=".9"/><path d="{d}" fill="#D9D2FF" shape-rendering="crispEdges"/></g>')
    else:
        name = "APRATIM PANDEY"; px = 3; nw = pw(name, px); nx = 420 - nw // 2
        b.append(f'<rect x="{nx-16}" y="30" width="{nw+32}" height="41" fill="#111622"/><rect x="{nx-12}" y="34" width="{nw+24}" height="33" fill="#f5ecd7"/>')
        b.append(ptext(name, nx, 40, px, "#1b2233"))
    # clock, poster, bookshelf (right wall)
    b.append('<rect x="726" y="40" width="44" height="44" rx="22" fill="#111622"/><rect x="730" y="44" width="36" height="36" rx="18" fill="#f5ecd7"/>')
    b.append('<rect x="747" y="50" width="3" height="13" fill="#1b2233"/><rect x="747" y="61" width="11" height="3" fill="#1b2233"/>')
    b.append('<rect x="604" y="58" width="52" height="56" fill="#111622"/><rect x="608" y="62" width="44" height="48" fill="#0B0B0D"/>')
    mark = ["PPPPPPPP...", "PPPPPPPP...", "...........", "LLLLLLLLLLL", "LLLLLLLLLLL", "LL.PPPPPPPP", "LL..PPPPPPP", "...........", "PPPPPPPPP..", "PPPPPPP...."]
    for rr, row in enumerate(mark):
        for cc, ch in enumerate(row):
            if ch != ".":
                b.append(f'<rect x="{610+cc*4}" y="{66+rr*4}" width="4" height="4" fill="{"#B9ADF5" if ch == "L" else "#F2F0EA"}"/>')
    books = [("#3572A5", 46, 18), ("#3572A5", 40, 14), ("#f1e05a", 34, 12), ("#3178c6", 38, 12), ("#e34c26", 30, 11), ("#663399", 36, 11), ("#F05138", 28, 10)]
    x = 664
    for col, h, w in books:
        b.append(f'<rect x="{x}" y="{156-h}" width="{w}" height="{h}" fill="{col}"/><rect x="{x}" y="{156-h+6}" width="{w}" height="3" fill="#000" fill-opacity=".25"/>')
        x += w + 3
    b.append(f'<rect x="{x+6}" y="140" width="16" height="8" fill="{GOLD}"/><rect x="{x+10}" y="148" width="8" height="4" fill="#ca8a04"/><rect x="{x+6}" y="152" width="16" height="4" fill="#ca8a04"/>')
    b.append(f'<rect x="652" y="156" width="160" height="8" fill="{WOOD_L}"/><rect x="652" y="164" width="160" height="3" fill="{WOOD_D}"/>')
    # floor: two plank lanes
    b.append(f'<rect y="{FLOOR}" width="{W}" height="{RH-FLOOR}" fill="#3a2618"/>')
    b += [f'<rect x="0" y="{y}" width="{W}" height="3" fill="#2b1b11"/>' for y in (FLOOR, FLOOR + 27)]
    b += [f'<rect x="{x}" y="{y}" width="3" height="24" fill="#2b1b11"/>' for y, xs in ((FLOOR + 3, (140, 420, 700)), (FLOOR + 30, (280, 560))) for x in xs]
    # floor lamp
    b.append(f'<rect x="196" y="150" width="40" height="20" fill="#fcd34d"/><rect x="214" y="170" width="4" height="{FLOOR-176}" fill="#475569"/><rect x="202" y="{FLOOR-6}" width="28" height="6" fill="#475569"/>')
    # desk
    DY = 302
    b.append(f'<rect x="250" y="{DY}" width="530" height="9" fill="{WOOD_L}"/><rect x="250" y="{DY+9}" width="530" height="4" fill="{WOOD_D}"/>')
    b += [f'<rect x="{x}" y="{DY+13}" width="9" height="{FLOOR-DY-13}" fill="{WOOD_D}"/>' for x in (262, 762)]
    # Legion monitor: RGB rear glow, thin bezel, chin, slim neck, wide base
    mx, my, mw, mh = 270, 120, 300, 162
    b.append(f'<rect x="{mx+20}" y="{my+20}" width="{mw-40}" height="{mh-30}" rx="20" fill="#8f7ff0" opacity=".55" filter="url(#rgb)" class="rgb"/>')
    b.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="4" fill="#0b0b0f" stroke="#26262e" stroke-width="2"/>')
    sx, sy, sw, sh = mx + 5, my + 5, mw - 10, mh - 20
    b.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="#0d1117"/>')
    b.append(ptext("LEGION", mx + mw // 2 - pw("LEGION", 1) // 2, my + mh - 11, 1, "#4b4b57"))
    # stand
    b.append(f'<rect x="{mx+mw//2-9}" y="{my+mh}" width="18" height="{DY-my-mh-4}" fill="#2a2a33"/><rect x="{mx+mw//2-3}" y="{my+mh+6}" width="6" height="10" fill="#0b0b0f"/>')
    b.append(f'<path d="M{mx+mw//2-58} {DY}L{mx+mw//2-46} {DY-5}H{mx+mw//2+46}L{mx+mw//2+58} {DY}Z" fill="#1c1c22"/>')
    # monitor screen: stats
    b.append(ptext("> STATS", sx + 14, sy + 12, 2, GREEN))
    b.append(f'<rect x="{sx+sw-46}" y="{sy+15}" width="6" height="6" fill="#ef4444" class="bl"/>')
    b.append(ptext("LIVE", sx + sw - 36, sy + 14, 1, "#fca5a5"))
    rows = [("CONTRIB", f"{TOTAL:,}"), ("REPOS", str(NREPOS)), ("STARS", str(STARS)), ("BEST RUN", f"{best}D")]
    for k, (lab, val) in enumerate(rows):
        cx = sx + 14 + (k % 2) * (sw // 2); cy = sy + 40 + (k // 2) * 48
        b.append(ptext(lab, cx, cy, 2, DIM))
        b.append(ptext(val, cx, cy + 20, 3, INK))
    b.append(f'<rect x="{sx+sw//2-6}" y="{sy+40}" width="2" height="90" fill="#1f2937"/>')
    b.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#gloss)"/>')
    # mug on desk
    b.append(f'<rect x="566" y="{DY-16}" width="14" height="16" fill="#e5e7eb"/><rect x="580" y="{DY-12}" width="4" height="8" fill="none" stroke="#e5e7eb" stroke-width="2"/>')
    b.append(f'<g class="st"><rect x="570" y="{DY-26}" width="2" height="7" fill="#e5e7eb" fill-opacity=".5"/><rect x="575" y="{DY-30}" width="2" height="8" fill="#e5e7eb" fill-opacity=".5"/></g>')
    # laptop: Claude Code terminal with the Branchglance widget pinned on top
    lx, ly, lw, lh = 614, 198, 150, 94
    b.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="4" fill="#18181b" stroke="#3f3f46" stroke-width="2"/>')
    b.append(f'<rect x="{lx-14}" y="{DY-5}" width="{lw+28}" height="5" fill="#52525b"/><rect x="{lx+lw//2-14}" y="{DY-5}" width="28" height="2" fill="#71717a"/>')
    tx_, ty_, tw_, th_ = lx + 4, ly + 4, lw - 8, lh - 8
    b.append(f'<rect x="{tx_}" y="{ty_}" width="{tw_}" height="{th_}" fill="#141413"/>')
    CL = "#D97757"
    b.append(f'<rect x="{tx_+4}" y="{ty_+5}" width="84" height="18" fill="none" stroke="{CL}" stroke-width="1.5"/>')
    b.append(ptext("* CLAUDE CODE", tx_ + 9, ty_ + 11, 1, CL))
    for k, wdt in enumerate((80, 60, 72, 44)):
        b.append(f'<rect x="{tx_+6}" y="{ty_+30+k*8}" width="{wdt}" height="3" fill="#57534e"/>')
    b.append(f'<rect x="{tx_+4}" y="{ty_+th_-16}" width="{tw_-8}" height="12" fill="none" stroke="#57534e"/>')
    b.append(ptext(">", tx_ + 8, ty_ + th_ - 13, 1, "#a8a29e"))
    b.append(f'<rect x="{tx_+16}" y="{ty_+th_-13}" width="4" height="7" fill="#e7e5e4" class="bl"/>')
    gx_, gy_ = tx_ + tw_ - 46, ty_ + 4
    b.append(f'<rect x="{gx_}" y="{gy_}" width="44" height="40" rx="2" fill="#0B0B0D" stroke="#B9ADF5" stroke-opacity=".7"/>')
    b.append(f'<rect x="{gx_+4}" y="{gy_+4}" width="18" height="2" fill="#6366f1"/><rect x="{gx_+27}" y="{gy_+4}" width="12" height="2" fill="#f97316"/>')
    for k, (dot, bar) in enumerate(((GREEN, 26), (AMBER, 18), (GREEN, 28), ("#818cf8", 22))):
        yy = gy_ + 10 + k * 7
        b.append(f'<rect x="{gx_+4}" y="{yy}" width="3" height="3" fill="{dot}" class="{"bl" if dot == AMBER else ""}"/><rect x="{gx_+10}" y="{yy}" width="{bar}" height="3" fill="#3f3f46"/>')
    # sleeping dog
    dx, dy = 668, FLOOR
    DOG, EAR, BELLY = "#b7793f", "#6b3f1d", "#f3e2c7"
    b.append(f'<rect x="{dx}" y="{dy-18}" width="50" height="18" fill="{DOG}"/><rect x="{dx+6}" y="{dy-6}" width="34" height="6" fill="{BELLY}"/>')
    b.append(f'<rect x="{dx+46}" y="{dy-22}" width="22" height="18" fill="{DOG}"/><rect x="{dx+64}" y="{dy-14}" width="8" height="8" fill="{BELLY}"/><rect x="{dx+70}" y="{dy-12}" width="3" height="3" fill="#1c1917"/>')
    b.append(f'<rect x="{dx+48}" y="{dy-22}" width="7" height="16" fill="{EAR}"/><rect x="{dx+58}" y="{dy-15}" width="5" height="2" fill="#1c1917"/>')
    b.append(f'<rect x="{dx-10}" y="{dy-16}" width="12" height="4" fill="{DOG}" class="tw"/><rect x="{dx+8}" y="{dy-3}" width="10" height="3" fill="{DOG}"/><rect x="{dx+36}" y="{dy-3}" width="10" height="3" fill="{DOG}"/>')
    b.append(f'<g class="zz">{ptext("Z", dx+70, dy-44, 2, "#94a3b8")}{ptext("Z", dx+84, dy-56, 1, "#94a3b8")}</g>')
    # ---- guide strip ----
    b.append(f'<rect y="{RH}" width="{W}" height="{H-RH}" fill="{CARD}"/><rect y="{RH}" width="{W}" height="2" fill="#2b1b11"/>')
    b.append(ptext("> NOW SHOWING", 32, RH + 32, 2, GREEN))
    chip = "OPEN TO AI/ML + SWE ROLES"; cw_ = pw(chip, 2) + 40
    cx_ = W - 32 - cw_
    b.append(f'<rect x="{cx_}" y="{RH+24}" width="{cw_}" height="30" rx="4" fill="#0c1a12" stroke="{GREEN}" stroke-opacity=".5"/>')
    b.append(f'<rect x="{cx_+12}" y="{RH+36}" width="6" height="6" fill="{GREEN}" class="bl"/>')
    b.append(ptext(chip, cx_ + 28, RH + 32, 2, PHOS))
    for j, l in enumerate(["I build tools for AI coding agents and work on", "retrieval, evaluation and project memory."]):
        b.append(f'<text x="32" y="{RH+90+j*30}" class="s" font-size="22" font-weight="600" letter-spacing="-.3" fill="{INK}">{esc(l)}</text>')
    b.append(f'<text x="32" y="{RH+152}" class="m" font-size="12" fill="{DIM}">India · CS @ Manipal Jaipur ’27</text>')
    b.append(f'<text x="{W-32}" y="{RH+152}" text-anchor="end" class="m" font-size="11" fill="{FAINT}">updated {STAMP}</text>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{LINE}"/>')
    style = ("@keyframes bl{50%{opacity:.15}}.bl{animation:bl 1.2s steps(1) infinite}"
             "@keyframes zz{0%{transform:translate(0,6px);opacity:0}40%{opacity:1}100%{transform:translate(6px,-8px);opacity:0}}.zz{animation:zz 3s ease-in-out infinite}"
             "@keyframes st{0%{transform:translateY(4px);opacity:0}50%{opacity:1}100%{transform:translateY(-6px);opacity:0}}.st{animation:st 2.4s ease-in-out infinite}"
             "@keyframes tw{50%{transform:translateY(-2px)}}.tw{animation:tw 1.6s steps(1) infinite}"
             "@keyframes rgb{0%,100%{fill:#8f7ff0}33%{fill:#22d3ee}66%{fill:#f472b6}}.rgb{animation:rgb 9s linear infinite}"
             "@keyframes nf{0%,91%,93%,95%,100%{opacity:1}92%,94%{opacity:.55}}.nf{animation:nf 6s 3s infinite}")
    save("hero.svg", svg(W, H, "".join(b), f"Apratim Pandey. I build tools for AI coding agents and work on retrieval, evaluation and project memory. Pixel room with a Legion monitor showing GitHub stats: {TOTAL:,} contributions, {NREPOS} repos, {STARS} stars, best run {best} days.", style))


# ================= 3. SIGNAL RUN =================
def signal():
    W, H = 840, 338
    b = [card(W, H, "#070a12")]
    b.append(ptext("> FLIGHT PATH", 32, 32, 2, GREEN))
    b.append(f'<text x="{32+pw("> FLIGHT PATH",2)+14}" y="45" class="m" font-size="11" fill="{DIM}">last 12 months</text>')
    b.append(f'<text x="{W-32}" y="45" text-anchor="end" class="m" font-size="12" font-weight="700" fill="{GOLD}">HI-SCORE {TOTAL:,}</text>')
    lv = {"NONE": "#111827", "FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32", "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}
    nweeks = len(WEEKS)
    cs = 12; gap = (W - 64 - nweeks * cs) / (nweeks - 1)
    gx, gy = 32, 70
    gw = nweeks * (cs + gap) - gap
    run_s = 7.0
    cells = []
    for wi, w in enumerate(WEEKS):
        for d in w["contributionDays"]:
            r = dt.date.fromisoformat(d["date"]).isoweekday() % 7
            x = gx + wi * (cs + gap); y = gy + r * (cs + gap)
            col = lv[d["contributionLevel"]]
            if d["contributionLevel"] != "NONE":
                delay = run_s * (x - gx) / gw
                cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cs}" height="{cs}" rx="2" fill="{col}" class="e" style="animation-delay:{delay:.2f}s"/>')
            else:
                cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cs}" height="{cs}" rx="2" fill="{col}"/>')
    b += cells
    # ship
    ship = ('<path d="M0 0h6v3h6v3h6v6h-6v3h-6v3H0v-3h3v-3H0V3h3V0z" fill="' + CYAN + '"/>'
            '<path d="M9 6h6v6H9z" fill="#e0f2fe"/><path d="M-6 6h6v6h-6z" fill="' + AMBER + '" class="fl"/>')
    b.append(f'<g class="ship" style="transform:translate({gx-24}px,{gy+3*(cs+gap)-3:.1f}px)">{ship}</g>')
    # stat tiles
    tiles = [("ACTIVE DAYS", str(ACTIVE)), ("BEST RUN", f"{best} DAYS"), ("BUSIEST DAY", str(BUSIEST)), ("LAST 30 DAYS", str(LAST30))]
    tw = (W - 64 - 3 * 14) / 4
    for k, (lab, val) in enumerate(tiles):
        x = 32 + k * (tw + 14)
        b.append(f'<rect x="{x:.1f}" y="194" width="{tw:.1f}" height="64" rx="8" fill="#0d1220" stroke="#1e293b"/>')
        b.append(f'<text x="{x+14:.1f}" y="216" class="m" font-size="10" letter-spacing="1.6" fill="{DIM}">{lab}</text>')
        b.append(ptext(val, x + 14, 228, 3, INK))
    # power-ups
    b.append(f'<text x="32" y="299" class="m" font-size="11" fill="{DIM}">POWER-UPS</text>')
    pills = LANG_PILLS
    x = 112
    for name, col in pills:
        w = 30 + len(name) * 7.4
        b.append(f'<rect x="{x:.1f}" y="282" width="{w:.1f}" height="24" rx="12" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".7"/>')
        b.append(f'<rect x="{x+11:.1f}" y="291" width="6" height="6" fill="{col}"/>')
        b.append(f'<text x="{x+24:.1f}" y="298" class="m" font-size="12" fill="{INK}">{name}</text>')
        x += w + 10
    style = (f"@keyframes fly{{from{{transform:translate({gx-24}px,{gy+3*(cs+gap)-3:.1f}px)}}to{{transform:translate({gx+gw+6:.1f}px,{gy+3*(cs+gap)-3:.1f}px)}}}}"
             f".ship{{animation:fly {run_s}s linear infinite}}"
             f"@keyframes eat{{0%{{opacity:1}}1%{{opacity:.15}}9%{{opacity:.15}}16%,100%{{opacity:1}}}}.e{{animation:eat {run_s}s linear infinite}}"
             "@keyframes fl{50%{opacity:.3}}.fl{animation:fl .2s steps(1) infinite}")
    save("signal.svg", svg(W, H, "".join(b), f"Signal run: {TOTAL} contributions in the last year, current streak {cur} days, best run {best} days, {PRS} pull requests.", style))

# ================= 4. section headers =================
def header(name, label):
    W, H = 840, 64
    t = "> " + label
    b = [ptext(t, 2, 30, 3, GREEN)]
    x0 = 2 + pw(t, 3) + 20
    b.append(f'<line x1="{x0}" y1="40.5" x2="{W-2}" y2="40.5" stroke="#30363d" stroke-dasharray="4 5"/>')
    save(name, svg(W, H, "".join(b), label.title()))

# ================= 5. project cards =================
IDENT_COLORS = [("#1e3a5f", "#60a5fa"), ("#14382a", "#4ade80"), ("#3b2a0f", "#fbbf24"), ("#2e1f4f", "#a78bfa"), ("#3b1420", "#fb7185")]

def identicon(seed, x, y, size, k):
    h = hashlib.md5(seed.encode()).digest()
    bg, fg = IDENT_COLORS[k % len(IDENT_COLORS)]
    cell = size // 7
    out = [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="8" fill="{bg}"/>']
    for r in range(5):
        for c in range(3):
            if (h[r * 3 + c] >> 1) & 1:
                for cc in {c, 4 - c}:
                    out.append(f'<rect x="{x + cell*(cc+1)}" y="{y + cell*(r+1)}" width="{cell}" height="{cell}" fill="{fg}"/>')
    return "".join(out)

LANG_COL = {"Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a"}

def pcard(fname, repo, title, desc, k, right=False):
    W, H = 412, 132
    r = REPOS[repo]; lang = (r["primaryLanguage"] or {}).get("name", "")
    b = [card(W, H), identicon(repo, 24, 24, 84, k)]
    b.append(f'<text x="128" y="46" class="s" font-size="17" font-weight="700" fill="{INK}">{esc(title)}</text>')
    for j, l in enumerate(wrap(desc, 40)[:2]):
        b.append(f'<text x="128" y="{70+j*19}" class="s" font-size="13" fill="{DIM}">{esc(l)}</text>')
    if r["stargazerCount"]:
        b.append(ptext("* " + str(r["stargazerCount"]), 128, 96, 2, GREEN))
    if lang:
        b.append(f'<text x="{W-24}" y="108" text-anchor="end" class="m" font-size="11" fill="{DIM}">{lang}</text>')
    ox = 8 if right else 0
    save(fname, svg(420, H + 16, f'<g transform="translate({ox},0)">' + "".join(b) + "</g>", f"{title}: {desc}"))

LAV = "#B9ADF5"; PAPER = "#F2F0EA"

def brand_inner(path):
    t = open(os.path.join(SRC, path), encoding="utf-8").read()
    return t

def icon_tile(x, y, size):
    t = brand_inner("icon-tile.svg")
    inner = t[t.index(">", t.index("<svg")) + 1: t.rindex("</svg>")]
    inner = re.sub(r"<title>.*?</title>", "", inner)
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 196.4694 196.4694">{inner}</svg>'

def wordmark(x, y, h):
    t = brand_inner("wordmark.svg")
    path = re.search(r"<path .*?/>", t, re.S).group(0)
    w = h * 1609 / 228
    return f'<svg x="{x}" y="{y}" width="{w:.1f}" height="{h}" viewBox="0 0 1609 228">{path}</svg>', w

def shot(fname, w, h, crop_h_ratio):
    live = {"widget.png": "docs/images/widget.png", "insights.png": "docs/images/insights.png"}.get(fname)
    im = None
    if live:
        try:
            with urllib.request.urlopen("https://raw.githubusercontent.com/apratxxm/branchglance/master/" + live, timeout=30) as resp:
                im = Image.open(io.BytesIO(resp.read())).convert("RGB")
        except Exception as exc:
            print("screenshot fallback:", fname, exc)
    if im is None:
        im = Image.open(os.path.join(SRC, fname)).convert("RGB")
    ch = int(im.width * crop_h_ratio)
    im = im.crop((0, 0, im.width, min(ch, im.height))).resize((w * 2, h * 2), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def featured():
    W = 840
    r = REPOS["branchglance"]
    b = []
    b.append(ptext("> BUILDING NOW", 32, 32, 2, GREEN))
    bx = 32 + pw("> BUILDING NOW", 2) + 12
    bw = len(BG_TAG) * 6.7 + 16
    b.append(f'<rect x="{bx}" y="29" width="{bw:.1f}" height="20" rx="4" fill="{LAV}" fill-opacity=".1" stroke="{LAV}" stroke-opacity=".6"/><text x="{bx+bw/2:.1f}" y="43" text-anchor="middle" class="m" font-size="11" fill="{LAV}">{esc(BG_TAG)}</text>')
    meta = "Python · JavaScript · Swift"
    b.append(f'<text x="{W-32}" y="45" text-anchor="end" class="m" font-size="11" fill="{DIM}">{meta}</text>')
    mx = W - 32 - len(meta) * 6.6
    st = "* " + str(r["stargazerCount"])
    b.append(ptext(st, mx - 16 - pw(st, 2), 33, 2, GREEN))
    # brand lockup
    b.append(icon_tile(32, 72, 64))
    wm, ww = wordmark(112, 78, 34)
    b.append(wm)
    b.append(f'<text x="113" y="132" class="m" font-size="11" letter-spacing="1.4" fill="{LAV}">LIVE AGENT VISIBILITY · WINDOWS + MACOS</text>')
    desc = "An always-on-top widget for Codex and Claude Code: every agent in one tree, which ones need you, and how much usage limit is left."
    for j, l in enumerate(wrap(desc, 48)):
        b.append(f'<text x="456" y="{94+j*22}" class="s" font-size="14" fill="#c9d1d9">{esc(l)}</text>')
    # screenshots
    iw, ih, iy = 380, 285, 168
    shots = [("widget.png", "agent tree"), ("insights.png", "insights")]
    for k, (f, cap) in enumerate(shots):
        ix = 32 + k * (iw + 16)
        a = shot(f, iw, ih, ih / iw)
        b.append(f'<rect x="{ix-1}" y="{iy-1}" width="{iw+2}" height="{ih+2}" rx="9" fill="{LINE}"/>')
        b.append(f'<clipPath id="ic{k}"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="8"/></clipPath>')
        b.append(f'<image x="{ix}" y="{iy}" width="{iw}" height="{ih}" preserveAspectRatio="xMidYMin slice" href="data:image/jpeg;base64,{a}" clip-path="url(#ic{k})"/>')
    H = iy + ih + 32
    save("branchglance.svg", svg(W, H, card(W, H) + "".join(b), "Building now: Branchglance, live agent visibility for Codex and Claude Code. Screenshots of the agent tree and insights views."))

# ================= 6. experience HUD =================
def experience():
    W, H = 840, 210
    b = [card(W, H)]
    b.append(ptext("> HDFC LIFE", 32, 32, 2, GREEN))
    b.append(f'<text x="{32+pw("> HDFC LIFE",2)+14}" y="45" class="m" font-size="11" fill="{DIM}">generative ai intern</text>')
    b.append(f'<text x="32" y="82" class="s" font-size="15" fill="#c9d1d9">Fine-tuned Sentence-BERT for dense intent retrieval.</text>')
    hud = [("44%", "71%", "TOP-1 ACCURACY"), ("", "96.8%", "TOP-3 ACCURACY"), ("0.17", "0.84", "RAREST-CLASS F1")]
    cw = (W - 64) / 3
    for k, (a, z, lab) in enumerate(hud):
        x = 32 + k * cw + (16 if k else 0)
        if k:
            b.append(f'<line x1="{x-16:.1f}" y1="110" x2="{x-16:.1f}" y2="178" stroke="{LINE}"/>')
        BOT = 146; zp = 5 if len(z) < 4 else 4
        if a:
            b.append(ptext(a, x, BOT - 21, 3, FAINT))
            ax = x + pw(a, 3) + 10
            b.append(ptext("→", ax, BOT - 21, 3, FAINT))
            b.append(ptext(z, ax + pw("→", 3) + 10, BOT - 7 * zp, zp, INK))
        else:
            b.append(ptext(z, x, BOT - 7 * zp, zp, INK))
        b.append(ptext(lab, x, 164, 2, DIM))
    save("experience.svg", svg(W, H, "".join(b), "HDFC Life, Generative AI intern: Top-1 accuracy 44% to 71%, Top-3 96.8%, rarest-class F1 0.17 to 0.84."))

def link_badge(fname, label, logo, w):
    H = 40
    b = [f'<rect x=".5" y=".5" width="{w-1}" height="{H-1}" rx="8" fill="{CARD}" stroke="{LINE}"/>', logo]
    b.append(f'<text x="44" y="25" class="s" font-size="14" font-weight="600" fill="{INK}">{esc(label)}</text>')
    save(fname, svg(w, H, "".join(b), label))

def badges():
    link_badge("l-branchglance.svg", "Branchglance " + BG_TAG, icon_tile(12, 9, 22), 226)
    li = (f'<rect x="12" y="9" width="22" height="22" rx="4" fill="#0A66C2"/>'
          f'<rect x="16" y="17" width="3" height="10" fill="#fff"/><rect x="16" y="12.5" width="3" height="3" fill="#fff"/>'
          f'<path d="M21 17h3v1.4c.6-1 1.6-1.6 3-1.6 2.2 0 3 1.4 3 3.6V27h-3v-5.8c0-1.2-.4-1.8-1.4-1.8s-1.6.7-1.6 1.9V27h-3z" fill="#fff"/>')
    link_badge("l-linkedin.svg", "LinkedIn", li, 118)
    em = (f'<rect x="12" y="12" width="22" height="16" rx="2" fill="none" stroke="{GREEN}" stroke-width="2"/>'
          f'<path d="M13 13l10 8 10-8" fill="none" stroke="{GREEN}" stroke-width="2"/>')
    link_badge("l-email.svg", "Email", em, 98)

hero(); signal(); featured(); experience(); badges()

def bust_cache():
    """Version each README image by content hash so browsers and GitHub fetch changed panels."""
    readme = os.path.join(ROOT, "..", "..", "README.md")
    if not os.path.exists(readme):
        return
    text = open(readme, encoding="utf-8").read()
    def repl(m):
        name = m.group(1)
        f = os.path.join(OUT, name)
        if not os.path.exists(f):
            return m.group(0)
        v = hashlib.sha1(open(f, "rb").read()).hexdigest()[:8]
        return f'src="assets/{name}?v={v}"'
    new = re.sub(r'src="assets/([\w.-]+\.svg)(?:\?v=[0-9a-f]+)?"', repl, text)
    if new != text:
        open(readme, "w", encoding="utf-8", newline=chr(10)).write(new)

header("h-projects.svg", "PROJECTS"); header("h-experience.svg", "EXPERIENCE")
pcard("p-demistifi.svg", "de-mistifi", "de-mistifi", "Turns long chat exports into a record of what got decided, what broke, and why.", 1)
pcard("p-visotonics.svg", "visotonics3d", "visotonics3d", "Scroll-driven WebGL site for a vision-AI industrial inspection company.", 3, True)
pcard("p-smartalexa.svg", "smartalexa", "smartalexa", "Local-first voice assistant that runs on my own machine.", 2)
pcard("p-jobangel.svg", "jobangel", "jobangel", "Finds startups and drafts personalised internship outreach with RAG.", 4, True)
print("ok", TOTAL, COMMITS, PRS, cur, best, STARS, NREPOS)
bust_cache()
