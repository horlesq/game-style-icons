#!/usr/bin/env python3
"""Generates every icon in icons/<style>/<icon>.svg, a sprite per style in sprites/, and preview.html.

Each icon is one of 12 base glyphs (drawn on a 24-unit grid as stroke paths, see GLYPHS) rendered by one of
20 style functions (see STYLES), on a 64x64 canvas. Minecraft uses hand-drawn 16x16 pixel versions (PIXELS).
Run: python3 gen.py
"""
import math, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- glyphs (24x24, stroke paths)
# (path data, kind): 1 closed (a style may fill it), 0 open line, 2 inner detail on top of a filled shape
GLYPHS = {
    'home': [('M3.5 11.2 12 4l8.5 7.2', 0), ('M5.8 9.6V20h12.4V9.6', 0), ('M10 20v-5.2h4V20', 0)],
    'search': [('M10.5 4.5a6 6 0 1 0 0 12a6 6 0 1 0 0-12Z', 1), ('M15 15l5 5', 0)],
    'settings': [('M12 8.6a3.4 3.4 0 1 0 0 6.8a3.4 3.4 0 1 0 0-6.8Z', 1)]
                + [(f'M{12 + 6.2 * math.cos(a):.2f} {12 + 6.2 * math.sin(a):.2f}L{12 + 8.6 * math.cos(a):.2f} {12 + 8.6 * math.sin(a):.2f}', 0) for a in [i * math.pi / 4 for i in range(8)]]
                + [('M12 5.8a6.2 6.2 0 1 0 0 12.4a6.2 6.2 0 1 0 0-12.4Z', 0)],
    'user': [('M12 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8Z', 1), ('M4.5 20.5c0-4 3.4-6.6 7.5-6.6s7.5 2.6 7.5 6.6Z', 1)],
    'heart': [('M12 20c-6.8-4.6-9-8.4-9-11.4C3 5.9 5.1 4 7.6 4c1.9 0 3.4 1.1 4.4 2.7C13 5.1 14.5 4 16.4 4C18.9 4 21 5.9 21 8.6c0 3-2.2 6.8-9 11.4Z', 1)],
    'shield': [('M12 3l7.8 3v5.2c0 4.7-3.2 8.3-7.8 9.8c-4.6-1.5-7.8-5.1-7.8-9.8V6Z', 1), ('M12 7.5v9.5', 2)],
    'star': [('M12 3.2l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 17l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8Z', 1)],
    'map-pin': [('M12 21s-6.8-6.2-6.8-11.2a6.8 6.8 0 0 1 13.6 0C18.8 14.8 12 21 12 21Z', 1), ('M12 7.3a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5Z', 2)],
    'bag': [('M5 9.5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2V19a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2Z', 1), ('M9 7.5V6.3a3 3 0 0 1 6 0v1.2', 0), ('M8.5 13.5h7', 2)],
    'coin': [('M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16Z', 1), ('M12 6.8a5.2 5.2 0 1 0 0 10.4a5.2 5.2 0 1 0 0-10.4Z', 2), ('M12 9.6v4.8', 2)],
    'mail': [('M3.5 7.5a1.5 1.5 0 0 1 1.5-1.5h14a1.5 1.5 0 0 1 1.5 1.5v9a1.5 1.5 0 0 1-1.5 1.5H5a1.5 1.5 0 0 1-1.5-1.5Z', 1), ('M4 7l8 6 8-6', 2)],
    'lock': [('M5.5 12.5a1.8 1.8 0 0 1 1.8-1.8h9.4a1.8 1.8 0 0 1 1.8 1.8v6.7a1.8 1.8 0 0 1-1.8 1.8H7.3a1.8 1.8 0 0 1-1.8-1.8Z', 1), ('M8.3 10.7V8a3.7 3.7 0 0 1 7.4 0v2.7', 0), ('M12 14.6v2.6', 2)],
}
ICONS = list(GLYPHS)

# ---------------------------------------------------------------- Minecraft: 16x16 pixel items
# k outline, a base, b light, c shade, w shine, d detail
PIXELS = {
    'home': ({'k': '#2b1a0c', 'a': '#9c6a3a', 'b': '#c08a52', 'c': '#6e4826', 'd': '#7b7b7b', 'w': '#a9a9a9'}, [
        "................",
        ".......kk.......",
        "......kddk......",
        ".....kdwwdk.....",
        "....kdwwwwdk....",
        "...kdwwwwwwdk...",
        "..kdddddddddck..",
        ".kkkkkkkkkkkkkk.",
        "..kbaaaaaaaaack.",
        "..kbakkkaaaaack.",
        "..kbakwkaakkkck.",
        "..kbakkkaakcack.",
        "..kbaaaaaakcack.",
        "..kbaaaaaakcack.",
        "..kccccccckcack.",
        "..kkkkkkkkkkkkk.",
    ]),
    'search': ({'k': '#1d1d1d', 'a': '#9fd6f2', 'b': '#e6f7ff', 'c': '#5a9ec2', 'd': '#6b4a2b', 'w': '#ffffff'}, [
        "................",
        "....kkkkk.......",
        "...kbbaaak......",
        "..kbwaaaaak.....",
        ".kbwaaaaaaak....",
        ".kbaaaaaaack....",
        ".kaaaaaaaack....",
        ".kaaaaaaacck....",
        ".kaaaaaaacck....",
        "..kaaaaccck.....",
        "...kcccckkdk....",
        "....kkkk.kddk...",
        ".........kddk...",
        "..........kddk..",
        "...........kddk.",
        "............kk..",
    ]),
    'settings': ({'k': '#232323', 'a': '#8a8a8a', 'b': '#bdbdbd', 'c': '#5b5b5b', 'd': '#a82020', 'w': '#ff5a5a'}, [
        "................",
        "......kkkk......",
        "..kk..kbak..kk..",
        ".kbak.kbak.kack.",
        ".kbaakkbaakaack.",
        "..kbaaaaaaaack..",
        "kkkbaakkkkaacckk",
        "kbbaak.dd.kaaack",
        "kbaaak.dw.kaacck",
        "kkkaaakkkkaaackk",
        "..kaaaaaaaaack..",
        ".kaackaaaakcack.",
        ".kacck.kack.kck.",
        "..kk..kcck..kk..",
        "......kkkk......",
        "................",
    ]),
    'user': ({'k': '#2a1a10', 'a': '#c8956b', 'b': '#e2b58e', 'c': '#9c6c47', 'd': '#3c63a8', 'w': '#ffffff'}, [
        "................",
        ".....kkkkkk.....",
        "....kbbaaaak....",
        "....kbaaaaak....",
        "....kawkawak....",
        "....kaaaaacck...",
        "....kaackaack...",
        ".....kaaaack....",
        "......kkkk......",
        "...kkkddddkkk...",
        "..kddddddddddk..",
        ".kddddddddddddk.",
        ".kddddddddddddk.",
        ".kddkddddddkddk.",
        ".kddkddddddkddk.",
        ".kkkkkkkkkkkkkk.",
    ]),
    'heart': ({'k': '#4a0000', 'a': '#d4202a', 'b': '#ff6b6b', 'c': '#8f0f17', 'w': '#ffffff'}, [
        "................",
        "..kkkk....kkkk..",
        ".kwbaak..kaaack.",
        "kbbaaaakkaaaaack",
        "kbaaaaaaaaaaaack",
        "kbaaaaaaaaaaacck",
        "kaaaaaaaaaaaacck",
        ".kaaaaaaaaaacck.",
        "..kaaaaaaaacck..",
        "...kaaaaaacck...",
        "....kaaaacck....",
        ".....kaacck.....",
        "......kcck......",
        ".......kk.......",
        "................",
        "................",
    ]),
    'shield': ({'k': '#1f1f1f', 'a': '#9a9a9a', 'b': '#d6d6d6', 'c': '#626262', 'd': '#3a5ec4', 'w': '#ffffff'}, [
        "................",
        ".kkkkkkkkkkkkkk.",
        ".kwbbaaddaaaack.",
        ".kbbaaaddaaaack.",
        ".kbaaaaddaaaack.",
        ".kbaaaaddaaaack.",
        ".kddddddddddddk.",
        ".kddddddddddddk.",
        ".kbaaaaddaaaack.",
        ".kaaaaaddaaacck.",
        "..kaaaaddaaacck.",
        "..kaaaaddaaack..",
        "...kaaaddaacck..",
        "....kaaddacck...",
        ".....kkddkkk....",
        ".......kk.......",
    ]),
    'star': ({'k': '#5a3d00', 'a': '#ffd21f', 'b': '#fff3a0', 'c': '#c98e00', 'w': '#ffffff'}, [
        "................",
        ".......kk.......",
        "......kbak......",
        "......kbak......",
        ".....kbwaak.....",
        "kkkkkkbaaackkkkk",
        "kbbbbbbaaaaaaack",
        ".kbbaaaaaaaaack.",
        "..kbaaaaaaaack..",
        "...kaaaaaaaak...",
        "...kaaaaaaack...",
        "..kaaaacaaaack..",
        "..kaaacckaaack..",
        ".kaacck..kcaack.",
        ".kcck......kcck.",
        ".kk..........kk.",
    ]),
    'map-pin': ({'k': '#3a0606', 'a': '#d23a2a', 'b': '#ff7a5c', 'c': '#8e1e14', 'w': '#ffffff', 'd': '#f4e6c8'}, [
        "................",
        ".....kkkkkk.....",
        "....kbbaaaak....",
        "...kbwaaaaack...",
        "..kbaaakkaaack..",
        "..kbaakddkaack..",
        "..kaaakddkacck..",
        "..kaaaakkaacck..",
        "...kaaaaaacck...",
        "...kaaaaaacck...",
        "....kaaaacck....",
        "....kaaaacck....",
        ".....kaacck.....",
        ".....kaacck.....",
        "......kcck......",
        ".......kk.......",
    ]),
    'bag': ({'k': '#2b1608', 'a': '#9a5a2c', 'b': '#c7834a', 'c': '#673915', 'd': '#e0c050', 'w': '#ffffff'}, [
        "................",
        "......kkkk......",
        ".....kc..ck.....",
        ".....kc..ck.....",
        "...kkkkkkkkkk...",
        "..kbbaaaaaaack..",
        "..kbwaaaaaaack..",
        "..kbaaaaaaaack..",
        "..kkkkkddkkkkk..",
        "..kbaaakdkaaak..",
        "..kbaaaaaaaack..",
        "..kbaaaaaaacck..",
        "..kaaaaaaaacck..",
        "..kcccccccccck..",
        "...kkkkkkkkkk...",
        "................",
    ]),
    'coin': ({'k': '#4d3300', 'a': '#f2b81b', 'b': '#ffe27a', 'c': '#b37a00', 'w': '#ffffff', 'd': '#d99a00'}, [
        "................",
        ".....kkkkkk.....",
        "...kkbbbaaakk...",
        "..kbwbaaaaaack..",
        "..kbbddddddack..",
        ".kbbdaaaaaadcck.",
        ".kbadaakkaadcck.",
        ".kbadaakkaadcck.",
        ".kaadaakkaadcck.",
        ".kaadaakkaadcck.",
        ".kaadaaaaaadcck.",
        "..kaaddddddcck..",
        "..kaaaaaacccck..",
        "...kkaacccckk...",
        ".....kkkkkk.....",
        "................",
    ]),
    'mail': ({'k': '#2e2a22', 'a': '#efe6cf', 'b': '#ffffff', 'c': '#bfb393', 'd': '#c0392b', 'w': '#ffffff'}, [
        "................",
        "................",
        "................",
        ".kkkkkkkkkkkkkk.",
        ".kckbbbbbbbbkck.",
        ".kackbbbbbbkcak.",
        ".kaackbbbbkcaak.",
        ".kaaackbbkcaaak.",
        ".kaaaakddkaaaak.",
        ".kaaakkddkkaaak.",
        ".kaakaaaaaakaak.",
        ".kakaaaaaaaakak.",
        ".kkcccccccccckk.",
        ".kkkkkkkkkkkkkk.",
        "................",
        "................",
    ]),
    'lock': ({'k': '#1f1f1f', 'a': '#d9a400', 'b': '#ffd75a', 'c': '#9a7200', 'd': '#a8a8a8', 'w': '#ffffff'}, [
        "................",
        "......kkkk......",
        ".....kddddk.....",
        "....kdkkkkdk....",
        "....kdk..kdk....",
        "....kdk..kdk....",
        "....kdk..kdk....",
        "..kkkkkkkkkkkk..",
        "..kbbaaaaaaack..",
        "..kbaaakkaaack..",
        "..kbaaakkaaack..",
        "..kbaaakkaaack..",
        "..kaaaaaaaacck..",
        "..kcccccccccck..",
        "..kkkkkkkkkkkk..",
        "................",
    ]),
}
for _n, (_p, _rows) in PIXELS.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), (_n, [len(r) for r in _rows])

# ---------------------------------------------------------------- helpers
def paths(parts, stroke, w, fill=None, fill_op=1, cap='round', join='round', extra='', detail=None):
    """detail: colour for inner details (kind 2), for styles whose fill would hide them."""
    out = []
    for d, kind in parts:
        f = fill if (kind == 1 and fill) else 'none'
        fo = f' fill-opacity="{fill_op}"' if f != 'none' and fill_op != 1 else ''
        st = detail if (kind == 2 and detail) else stroke
        out.append(f'<path d="{d}" fill="{f}"{fo} stroke="{st}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="{join}"{extra}/>')
    return ''.join(out)


def place(inner, scale=1.5, dx=0, dy=0, rot=0):
    o = 32 - 12 * scale
    r = f' rotate({rot} 12 12)' if rot else ''
    return f'<g transform="translate({o + dx:.2f} {o + dy:.2f}) scale({scale}){r}">{inner}</g>'


def glow(uid, std=1.2):
    return (f'<filter id="{uid}-glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="{std}" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def blob(cx, cy, r, wobble, n, seed):
    """Closed irregular shape (hand-drawn look) as a smooth path."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + wobble * math.sin(seed * 1.7 + i * 2.3) * math.cos(seed + i * 1.1))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f'M{(pts[0][0] + pts[-1][0]) / 2:.2f} {(pts[0][1] + pts[-1][1]) / 2:.2f}'
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        d += f'Q{p[0]:.2f} {p[1]:.2f} {(p[0] + q[0]) / 2:.2f} {(p[1] + q[1]) / 2:.2f}'
    return d + 'Z'


def polygon(cx, cy, r, n, rot=0):
    return ' '.join(f'{cx + r * math.cos(rot + 2 * math.pi * i / n):.2f},{cy + r * math.sin(rot + 2 * math.pi * i / n):.2f}' for i in range(n))

# ---------------------------------------------------------------- styles
def cyberpunk(parts, uid, i):
    frame = '<path d="M8 4H46L60 18V56L56 60H18L4 46V8Z" fill="#0b0b14"/><path d="M8 4H46L60 18V56L56 60H18L4 46V8Z" fill="none" stroke="#fcee0a" stroke-width="1.2" stroke-opacity=".55"/>'
    ticks = '<path d="M47 55h2v2h-2zM51 55h1v2h-1zM53.5 55h2.5v2h-2.5z" fill="#fcee0a" fill-opacity=".8"/><path d="M8 11V8h3" fill="none" stroke="#00f0ff" stroke-width="1.2"/>'
    g = (place(paths(parts, '#00f0ff', 1.6), dx=-1.2) .replace('<g ', '<g opacity=".75" ')
         + place(paths(parts, '#ff003c', 1.6), dx=1.2).replace('<g ', '<g opacity=".7" ')
         + place(paths(parts, '#fcee0a', 1.6, fill='#fcee0a', fill_op=.12)))
    return f'<defs>{glow(uid, .6)}</defs>{frame}{ticks}<g filter="url(#{uid}-glow)">{g}</g>'


def borderlands(parts, uid, i):
    hue = ['#e9573f', '#f6a623', '#3fa9e9', '#8bc34a'][i % 4]
    bg = f'<path d="{blob(32, 32, 27, .045, 14, i + 2)}" fill="{hue}" stroke="#151515" stroke-width="3"/>'
    hatch = ''.join(f'<path d="M{40 + k * 3.2} {9 + k * .4}l6 6" stroke="#151515" stroke-width="1.3" stroke-linecap="round" opacity=".55"/>' for k in range(4))
    g = place(paths(parts, '#151515', 3.6) + paths(parts, '#ffe08a', 1.8, fill='#ffe08a', detail='#151515'))
    return f'{bg}{hatch}{g}'


def gta(parts, uid, i):
    bg = '<circle cx="32" cy="32" r="28" fill="#0d0d0d" fill-opacity=".72"/><circle cx="32" cy="32" r="28" fill="none" stroke="#6ab04c" stroke-width="2" stroke-dasharray="132 44" transform="rotate(-90 32 32)"/>'
    shadow = place(paths(parts, '#000', 3.8, fill='#000'), dx=1.4, dy=1.6).replace('<g ', '<g opacity=".45" ')
    g = place(paths(parts, '#000', 3.6) + paths(parts, '#ffffff', 2, fill='#ffffff', detail='#000'))
    return f'{bg}{shadow}{g}'


def minecraft(parts, uid, i, name=None):
    pal, rows = PIXELS[name]
    px = 3
    slot = ('<rect x="2" y="2" width="60" height="60" fill="#8b8b8b"/><path d="M2 62V2h60" fill="none" stroke="#373737" stroke-width="3"/>'
            '<path d="M2 62h60V2" fill="none" stroke="#ffffff" stroke-width="3"/>')
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < 16:
            ch = row[x]
            if ch == '.': x += 1; continue
            run = 1
            while x + run < 16 and row[x + run] == ch: run += 1
            rects.append(f'<rect x="{8 + x * px}" y="{8 + y * px}" width="{run * px}" height="{px}" fill="{pal[ch]}"/>')
            x += run
    return f'{slot}<g shape-rendering="crispEdges">{"".join(rects)}</g>'


def fallout(parts, uid, i):
    defs = (f'<defs>{glow(uid, 1)}<pattern id="{uid}-scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1.2" fill="#18ff6d" fill-opacity=".07"/></pattern>'
            f'<radialGradient id="{uid}-crt"><stop offset="0" stop-color="#0c2a14"/><stop offset="1" stop-color="#03100a"/></radialGradient></defs>')
    bg = f'<rect x="3" y="3" width="58" height="58" rx="10" fill="url(#{uid}-crt)"/><rect x="3" y="3" width="58" height="58" rx="10" fill="url(#{uid}-scan)"/><rect x="3" y="3" width="58" height="58" rx="10" fill="none" stroke="#18ff6d" stroke-opacity=".35" stroke-width="1"/>'
    g = place(paths(parts, '#2bff7a', 1.7, fill='#2bff7a', fill_op=.14))
    return f'{defs}{bg}<g filter="url(#{uid}-glow)">{g}</g>'


def zelda(parts, uid, i):
    bg = ('<rect x="4" y="4" width="56" height="56" rx="12" fill="#0e1c26"/><rect x="4" y="4" width="56" height="56" rx="12" fill="none" stroke="#3fd8f2" stroke-opacity=".5" stroke-width="1"/>'
          '<circle cx="32" cy="32" r="23" fill="none" stroke="#3fd8f2" stroke-opacity=".25" stroke-width=".8" stroke-dasharray="2 3"/>'
          '<circle cx="51" cy="13" r="1.6" fill="#ff8a1f"/><circle cx="13" cy="51" r="1" fill="#3fd8f2" fill-opacity=".7"/><circle cx="17" cy="51" r="1" fill="#3fd8f2" fill-opacity=".4"/>')
    g = place(paths(parts, '#5ae6ff', 1.25, fill='#5ae6ff', fill_op=.1))
    return f'<defs>{glow(uid, .9)}</defs>{bg}<g filter="url(#{uid}-glow)">{g}</g>'


def halo(parts, uid, i):
    hexp = polygon(32, 32, 28, 6, math.pi / 6)
    bg = (f'<polygon points="{hexp}" fill="#06131d" fill-opacity=".92"/><polygon points="{hexp}" fill="none" stroke="#5fc8ff" stroke-width="1.2" stroke-opacity=".7"/>'
          '<path d="M10 22V17l5-3M54 42v5l-5 3" fill="none" stroke="#9fe3ff" stroke-width="2" stroke-linecap="square"/>')
    g = place(paths(parts, '#a9e8ff', 1.6, fill='#5fc8ff', fill_op=.18))
    return f'<defs>{glow(uid, 1.1)}</defs>{bg}<g filter="url(#{uid}-glow)">{g}</g>'


def persona5(parts, uid, i):
    spikes = []
    for k in range(18):
        a = 2 * math.pi * k / 18 + .2
        r = 29 if k % 2 == 0 else 20 + 3 * math.sin(k * 1.9 + i)
        spikes.append(f'{32 + r * math.cos(a):.2f},{32 + r * math.sin(a):.2f}')
    bg = (f'<polygon points="{" ".join(spikes)}" fill="#e60012" stroke="#000" stroke-width="2.5" stroke-linejoin="miter"/>'
          '<path d="M14 44l36-18 2 6-36 18Z" fill="#000"/>')
    g = place(paths(parts, '#000', 4.4, join='miter') + paths(parts, '#ffffff', 2.4, fill='#ffffff', join='miter', detail='#000'), rot=-9)
    return f'{bg}{g}'


def hollow_knight(parts, uid, i):
    bg = ('<circle cx="32" cy="28" r="24" fill="#0c0f17"/><circle cx="32" cy="28" r="24" fill="none" stroke="#d9e1ea" stroke-opacity=".35" stroke-width=".8"/>'
          '<path d="M16 58c4-4 9-4 12-.5M48 58c-4-4-9-4-12-.5" fill="none" stroke="#d9e1ea" stroke-width="1.1" stroke-linecap="round"/>'
          '<path d="M28 57.5q4 3.5 8 0" fill="none" stroke="#d9e1ea" stroke-width="1.1" stroke-linecap="round"/><circle cx="32" cy="62" r="1.1" fill="#d9e1ea"/>'
          '<circle cx="15" cy="57" r=".9" fill="#d9e1ea"/><circle cx="49" cy="57" r=".9" fill="#d9e1ea"/>')
    g = place(paths(parts, '#f2f5f9', 1.45, fill='#f2f5f9', fill_op=.08), scale=1.32, dy=-4)
    return f'<defs>{glow(uid, .7)}</defs>{bg}<g filter="url(#{uid}-glow)">{g}</g>'


def hades(parts, uid, i):
    ticks = ''.join(f'<path d="M{32 + 27.5 * math.cos(a):.2f} {32 + 27.5 * math.sin(a):.2f}L{32 + 30.5 * math.cos(a):.2f} {32 + 30.5 * math.sin(a):.2f}" stroke="#d8a94b" stroke-width="1.6"/>' for a in [k * math.pi / 4 + math.pi / 8 for k in range(8)])
    defs = f'<defs><radialGradient id="{uid}-r"><stop offset="0" stop-color="#7a1414"/><stop offset=".75" stop-color="#2a0505"/><stop offset="1" stop-color="#120202"/></radialGradient></defs>'
    bg = f'<circle cx="32" cy="32" r="27" fill="url(#{uid}-r)"/><circle cx="32" cy="32" r="27" fill="none" stroke="#d8a94b" stroke-width="1.6"/><circle cx="32" cy="32" r="23.5" fill="none" stroke="#d8a94b" stroke-width=".7" stroke-opacity=".7"/>{ticks}'
    g = place(paths(parts, '#2a0606', 3.4) + paths(parts, '#f0c96a', 1.7, fill='#c9302c', fill_op=.85))
    return f'{defs}{bg}{g}'


def portal(parts, uid, i):
    bg = ('<rect x="4" y="4" width="56" height="56" rx="6" fill="#f3f5f7"/><rect x="4" y="4" width="56" height="56" rx="6" fill="none" stroke="#c9ced3" stroke-width="1.2"/>'
          '<path d="M4 16H60" stroke="#e1e5e9" stroke-width="1"/>'
          '<ellipse cx="12" cy="10" rx="3.2" ry="1.8" fill="none" stroke="#ff9a00" stroke-width="1.6"/><ellipse cx="52" cy="54" rx="3.2" ry="1.8" fill="none" stroke="#2aa7ff" stroke-width="1.6"/>')
    g = place(paths(parts, '#2b2f33', 1.9), scale=1.4, dy=2)
    return f'{bg}{g}'


def mass_effect(parts, uid, i):
    bg = ('<circle cx="32" cy="32" r="28" fill="#0a0d12"/>'
          '<circle cx="32" cy="32" r="27" fill="none" stroke="#ff8a2a" stroke-width="1.4" stroke-dasharray="30 6 4 6" stroke-opacity=".8"/>'
          '<circle cx="32" cy="32" r="23" fill="none" stroke="#ff8a2a" stroke-width=".6" stroke-opacity=".45"/>')
    g = place(paths(parts, '#ffab5e', 1.5, fill='#ff8a2a', fill_op=.16))
    return f'<defs>{glow(uid, 1.2)}</defs>{bg}<g filter="url(#{uid}-glow)">{g}</g>'


def doom(parts, uid, i):
    defs = f'<defs><linearGradient id="{uid}-m" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b6e72"/><stop offset=".5" stop-color="#3b3d40"/><stop offset="1" stop-color="#1f2022"/></linearGradient></defs>'
    plate = '<path d="M12 3H52L61 12V52L52 61H12L3 52V12Z" fill="url(#U-m)" stroke="#111" stroke-width="2"/>'.replace('U', uid)
    rivets = ''.join(f'<circle cx="{x}" cy="{y}" r="1.5" fill="#9a9da1" stroke="#111" stroke-width=".6"/>' for x, y in [(11, 11), (53, 11), (11, 53), (53, 53)])
    g = place(paths(parts, '#140300', 3.8, join='miter') + paths(parts, '#ff4a1c', 2.1, fill='#ff4a1c', join='miter', detail='#140300'))
    return f'{defs}{plate}{rivets}{g}'


def splatoon(parts, uid, i):
    ink = ['#e8188c', '#bce61b', '#ff7a00', '#3d5cff', '#1ee6c4', '#a63dff'][i % 6]
    drips = f'<path d="M24 52q1 9 3 0M38 50q1.5 11 3.5 0" fill="{ink}"/>'
    bg = f'<path d="{blob(32, 30, 25, .14, 16, i * 3 + 1)}" fill="{ink}"/>{drips}<circle cx="54" cy="12" r="3" fill="{ink}"/><circle cx="10" cy="48" r="2.2" fill="{ink}"/>'
    g = place(paths(parts, '#20112e', 3.8) + paths(parts, '#ffffff', 2.2, fill='#ffffff', detail='#20112e'), dy=-1)
    return f'{bg}{g}'


def animal_crossing(parts, uid, i):
    bg = ('<rect x="5" y="5" width="54" height="54" rx="18" fill="#fbf6e6" stroke="#7cc46b" stroke-width="3"/>'
          '<path d="M46 9c6 0 9 3 9 9-6 0-9-3-9-9Z" fill="#7cc46b"/><path d="M46 9l5 5" stroke="#5aa34b" stroke-width="1"/>')
    g = place(paths(parts, '#7a5634', 2.3, fill='#f3c86b'), scale=1.42, dy=1)
    return f'{bg}{g}'


def hotline(parts, uid, i):
    defs = (f'<defs>{glow(uid, 1.3)}<linearGradient id="{uid}-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff2a6d"/><stop offset="1" stop-color="#05d9e8"/></linearGradient></defs>')
    lines = ''.join(f'<rect x="3" y="{y}" width="58" height=".8" fill="#ff2a6d" fill-opacity=".12"/>' for y in range(8, 60, 5))
    bg = f'<rect x="3" y="3" width="58" height="58" rx="4" fill="#1a0630"/>{lines}<rect x="3" y="3" width="58" height="58" rx="4" fill="none" stroke="#ff2a6d" stroke-width="1" stroke-opacity=".6"/>'
    ghost = place(paths(parts, '#05d9e8', 1.6), dx=1.6, dy=.6).replace('<g ', '<g opacity=".32" ')
    g = place(paths(parts, f'url(#{uid}-g)', 2.1, fill='#ff2a6d', fill_op=.12))
    return f'{defs}{bg}{ghost}<g filter="url(#{uid}-glow)">{g}</g>'


def mirrors_edge(parts, uid, i):
    bg = '<rect x="4" y="4" width="56" height="56" fill="#fafafa" stroke="#e3e3e3" stroke-width="1"/><path d="M42 4H60V22Z" fill="#e1251b"/>'
    rest, last = parts[:-1] or parts, parts[-1:] if len(parts) > 1 else []
    g = place(paths(rest, '#121212', 1.6) + paths(last, '#e1251b', 2))
    return f'{bg}{g}'


def diablo(parts, uid, i):
    spikes = ''.join(f'<polygon points="{32 + 31 * math.cos(a):.2f},{32 + 31 * math.sin(a):.2f} {32 + 26 * math.cos(a - .12):.2f},{32 + 26 * math.sin(a - .12):.2f} {32 + 26 * math.cos(a + .12):.2f},{32 + 26 * math.sin(a + .12):.2f}" fill="#c99a4a"/>' for a in [k * math.pi / 4 for k in range(8)])
    defs = f'<defs><radialGradient id="{uid}-r"><stop offset="0" stop-color="#5a0808"/><stop offset="1" stop-color="#0b0000"/></radialGradient></defs>'
    bg = f'{spikes}<circle cx="32" cy="32" r="26" fill="url(#{uid}-r)" stroke="#c99a4a" stroke-width="2"/><circle cx="32" cy="32" r="22.5" fill="none" stroke="#6e5226" stroke-width="1"/>'
    g = place(paths(parts, '#000', 3.6) + paths(parts, '#e9c27a', 1.9, fill='#8e1414', fill_op=.85), scale=1.35)
    return f'{defs}{bg}{g}'


def pacman(parts, uid, i):
    bg = '<rect x="3" y="3" width="58" height="58" rx="8" fill="#000"/>'
    pellets = ''.join(f'<rect x="{x}" y="57" width="2.4" height="2.4" fill="#ffb897"/>' for x in (17, 25, 33, 41)) + '<circle cx="51" cy="58.2" r="2.6" fill="#ffb897"/>'
    g = place(paths(parts, '#2121ff', 3.2) + paths(parts, '#000', 1.1), scale=1.42, dy=-2)
    return f'{bg}{g}{pellets}'


def overwatch(parts, uid, i):
    bg = ('<path d="M14 6H58L50 58H6Z" fill="#2b3a4f"/><path d="M14 6H58L57 12H13Z" fill="#f99e1a"/>'
          '<path d="M6 58H50L50.6 54H6.6Z" fill="#ffffff" fill-opacity=".25"/>')
    g = place(paths(parts, '#ffffff', 2.2, fill='#f99e1a', fill_op=.9), dy=2)
    return f'{bg}{g}'


STYLES = [
    ('cyberpunk-2077', 'Cyberpunk 2077', 'Neon yellow on black, chamfered frame, chromatic glitch split', cyberpunk),
    ('borderlands', 'Borderlands', 'Cel-shaded: heavy black ink outlines, hand-drawn blobs, hatching', borderlands),
    ('gta', 'Grand Theft Auto', 'Radar blips: white glyphs with black outline on a dark minimap disc', gta),
    ('minecraft', 'Minecraft', '16x16 pixel items in an inventory slot', minecraft),
    ('fallout', 'Fallout', 'Monochrome green CRT terminal with scanlines and phosphor glow', fallout),
    ('zelda-botw', 'Zelda: Breath of the Wild', 'Slate tablet UI: thin cyan lines, dotted rings, one orange spark', zelda),
    ('halo', 'Halo', 'Hexagonal HUD frame, cyan glow, corner brackets', halo),
    ('persona-5', 'Persona 5', 'Red burst, black slash, tilted white cut-out glyph', persona5),
    ('hollow-knight', 'Hollow Knight', 'Pale ink on deep night, thin ring and curled ornament', hollow_knight),
    ('hades', 'Hades', 'Boon medallion: blood-red core, gold rings and rays', hades),
    ('portal', 'Portal', 'Clean test-chamber tile, dark linework, orange and blue rings', portal),
    ('mass-effect', 'Mass Effect', 'Orange holographic omni-tool rings and glow', mass_effect),
    ('doom', 'Doom', 'Riveted gunmetal plate, hellfire-orange glyph with hard outline', doom),
    ('splatoon', 'Splatoon', 'Neon ink splats with drips, white glyph, rotating ink colours', splatoon),
    ('animal-crossing', 'Animal Crossing', 'Soft cream card, leaf-green border, warm brown rounded lines', animal_crossing),
    ('hotline-miami', 'Hotline Miami', 'Synthwave: magenta-to-cyan glow, VHS lines, ghost offset', hotline),
    ('mirrors-edge', "Mirror's Edge", 'White minimal, black line glyph, runner-vision red highlight', mirrors_edge),
    ('diablo', 'Diablo', 'Gothic medallion: gold spikes and ring, bone glyph over blood red', diablo),
    ('pac-man', 'Pac-Man', 'Arcade maze: double blue walls on black, pellets', pacman),
    ('overwatch', 'Overwatch', 'Slanted slate card, orange stripe, bold white glyph', overwatch),
]


def build():
    for d in ('icons', 'sprites'):
        shutil.rmtree(os.path.join(HERE, d), ignore_errors=True)
        os.makedirs(os.path.join(HERE, d))
    for slug, title, desc, fn in STYLES:
        os.makedirs(os.path.join(HERE, 'icons', slug))
        symbols = []
        for i, name in enumerate(ICONS):
            uid = f'{slug}-{name}'
            body = fn(GLYPHS[name], uid, i, name=name) if fn is minecraft else fn(GLYPHS[name], uid, i)
            label = f'{name.replace("-", " ")} ({title} style)'
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" role="img" aria-label="{label}"><title>{label}</title>{body}</svg>\n'
            open(os.path.join(HERE, 'icons', slug, f'{name}.svg'), 'w').write(svg)
            symbols.append(f'<symbol id="{uid}" viewBox="0 0 64 64">{body}</symbol>')
        open(os.path.join(HERE, 'sprites', f'{slug}.svg'), 'w').write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + ''.join(symbols) + '</svg>\n')
    preview()
    print(len(STYLES), 'styles x', len(ICONS), 'icons =', len(STYLES) * len(ICONS), 'SVGs')


def preview():
    rows = []
    for slug, title, desc, _ in STYLES:
        cells = ''.join(f'<figure><img src="icons/{slug}/{n}.svg" width="64" height="64" alt="{n}"><figcaption>{n}</figcaption></figure>' for n in ICONS)
        rows.append(f'<section><h2>{title}</h2><p>{desc}</p><div class="row">{cells}</div></section>')
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Game Style Icons</title><style>
:root{{color-scheme:dark;--bg:#111317;--ink:#e9ebee;--muted:#8d939b;--rule:#22262c}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:28px;margin:0 0 4px}} header p{{color:var(--muted);margin:0 0 24px;max-width:70ch}}
section{{padding:18px 0;border-top:1px solid var(--rule)}} h2{{font-size:17px;margin:0}} section>p{{color:var(--muted);margin:2px 0 12px;font-size:14px}}
.row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:10px}}
figure{{margin:0;text-align:center}} img{{display:block;margin:0 auto}} figcaption{{font-size:11px;color:var(--muted);margin-top:4px}}
</style></head><body><main><header><h1>Game Style Icons</h1>
<p>{len(ICONS)} interface icons in {len(STYLES)} styles inspired by video games ({len(ICONS) * len(STYLES)} SVGs, 64&times;64). Original artwork, no logos or characters; not affiliated with any game or publisher.</p></header>
{"".join(rows)}</main></body></html>
'''
    open(os.path.join(HERE, 'preview.html'), 'w').write(html)


if __name__ == '__main__':
    build()
