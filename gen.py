#!/usr/bin/env python3
"""Generates the package: React components in src/, SVG-string functions in src/html/, the <game-icon> web component
(src/element.js), plain SVGs in svg/, and preview.html.

Icons are bare glyphs (no tile, no frame): each style gets its look from the glyph itself (outlines, offset
shadows, glitch copies, glows drawn as soft wide strokes, pixel art). Base glyphs and the Minecraft pixel items
live in glyphs.py. Run: python3 gen.py
"""
import json, math, os, re, shutil
from glyphs import GLYPHS, PIXELS
import pixelize

# Minecraft: material colour per icon for the generated pixel items (the hand-drawn ones in PIXELS keep their own)
M = {'iron': '#a7adb5', 'stone': '#8d8d8d', 'gold': '#f2b81b', 'wood': '#a0703f', 'leather': '#9a5a2c', 'paper': '#ece4cc',
     'redstone': '#d0301f', 'emerald': '#2fbf5b', 'lapis': '#3463cf', 'diamond': '#4fe0dc', 'amethyst': '#a65be0',
     'orange': '#f07c1c', 'bone': '#e8e2d0', 'obsidian': '#4a4160', 'snow': '#f4f7fa', 'pink': '#ef7fb0'}
MATERIAL = {
    'menu': 'stone', 'close': 'redstone', 'arrow-left': 'stone', 'arrow-right': 'stone', 'arrow-up': 'stone', 'arrow-down': 'stone',
    'chevron-down': 'stone', 'more': 'stone', 'external-link': 'lapis', 'plus': 'emerald', 'minus': 'redstone', 'check': 'emerald',
    'edit': 'wood', 'trash': 'iron', 'download': 'emerald', 'upload': 'lapis', 'share': 'diamond', 'copy': 'paper', 'refresh': 'emerald',
    'filter': 'iron', 'link': 'iron', 'unlock': 'gold', 'logout': 'wood', 'info': 'lapis', 'warning': 'gold', 'help': 'lapis',
    'bell': 'gold', 'eye': 'snow', 'eye-off': 'snow', 'check-circle': 'emerald', 'play': 'emerald', 'pause': 'iron', 'skip': 'iron',
    'volume': 'iron', 'mute': 'redstone', 'music': 'lapis', 'image': 'diamond', 'camera': 'stone', 'video': 'stone', 'chat': 'paper',
    'phone': 'stone', 'users': 'lapis', 'send': 'diamond', 'calendar': 'paper', 'clock': 'gold', 'globe': 'lapis', 'cart': 'iron',
    'gift': 'redstone', 'tag': 'gold', 'wallet': 'leather', 'card': 'lapis', 'file': 'paper', 'folder': 'gold', 'bookmark': 'redstone',
    'chart': 'emerald', 'cloud': 'snow', 'sun': 'gold', 'moon': 'paper', 'wifi': 'lapis', 'flag': 'redstone', 'sword': 'diamond',
    'axe': 'iron', 'bow': 'wood', 'potion': 'amethyst', 'trophy': 'gold', 'medal': 'gold', 'crown': 'gold', 'gamepad': 'obsidian',
    'skull': 'bone', 'chest': 'wood', 'key': 'gold', 'scroll': 'paper', 'map': 'paper', 'compass': 'iron', 'bomb': 'obsidian',
    'gem': 'diamond', 'dice': 'snow', 'target': 'redstone', 'fire': 'orange', 'zap': 'gold', 'ghost': 'snow', 'rocket': 'iron',
    'hourglass': 'gold', 'puzzle': 'emerald', 'magic': 'amethyst', 'level-up': 'emerald', 'health': 'redstone', 'save': 'lapis',
}

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = list(GLYPHS)
VIEWBOX = '-1 -1 26 26'


# ---------------------------------------------------------------- drawing helpers
def P(parts, stroke, w, fill=None, fo=1, detail=None, cap='round', join='round', op=None, tr=None):
    """Stroke every part; fill closed parts (kind 1) when fill is given; inner details (kind 2) use `detail`."""
    out = []
    for d, kind in parts:
        f = fill if (kind == 1 and fill) else 'none'
        fop = f' fill-opacity="{fo}"' if f != 'none' and fo != 1 else ''
        st = detail if (kind == 2 and detail) else stroke
        out.append(f'<path d="{d}" fill="{f}"{fop} stroke="{st}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="{join}"/>')
    g = ''.join(out)
    attrs = (f' opacity="{op}"' if op is not None else '') + (f' transform="{tr}"' if tr else '')
    return f'<g{attrs}>{g}</g>' if attrs else g


def glow(parts, color, w, strength=1):
    """A soft halo without SVG filters: two wide, faint strokes under the glyph."""
    return P(parts, color, w * 3.4, op=round(.08 * strength, 3)) + P(parts, color, w * 2.1, op=round(.18 * strength, 3))


def rim(parts, color, w, op=.85):
    """A thin dark edge under a light line: almost invisible on dark backgrounds, gives contrast on light ones."""
    return P(parts, color, w + 1.3, op=op)


def tilt(inner, deg):
    return f'<g transform="rotate({deg} 12 12)">{inner}</g>'


def nodet(parts):
    return [p for p in parts if p[1] != 2]


def det(parts):
    return [p for p in parts if p[1] == 2]


def grad(key, stops, x1, y1, x2, y2):
    s = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<defs><linearGradient id="__ID__-{key}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="userSpaceOnUse">{s}</linearGradient></defs>'


def bevel(parts, color, dx, dy, w, key, op=1):
    """Paints the band of the shape that is left when the shape is moved by (dx, dy): a light edge on the
    top-left for dx, dy > 0, a shaded edge on the bottom-right for dx, dy < 0. Follows every glyph exactly."""
    m = (f'<mask id="__ID__-{key}" maskUnits="userSpaceOnUse" x="-1" y="-1" width="26" height="26">'
         f'{P(parts, "#fff", w, fill="#fff")}{P(parts, "#000", w, fill="#000", tr=f"translate({dx} {dy})")}</mask>')
    return m + f'<rect x="-1" y="-1" width="26" height="26" fill="{color}" fill-opacity="{op}" mask="url(#__ID__-{key})"/>'


def runs(rows, pal):
    """Pixel rows (palette letters, '.' empty) as horizontal runs of 1-unit rects."""
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == '.':
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == ch:
                run += 1
            rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{pal[ch]}"/>')
            x += run
    return f'<g shape-rendering="crispEdges">{"".join(rects)}</g>'


def flat_pixels(B, D, key):
    """Solid pixels (body minus details) get key(x, y); empty pixels touching them become a dark 'k' outline."""
    n = len(B)
    solid = lambda x, y: 0 <= x < n and 0 <= y < n and B[y][x] and not D[y][x]
    return [''.join(key(x, y) if solid(x, y) else ('k' if any(solid(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)) else '.')
                    for x in range(n)) for y in range(n)]


def star(cx, cy, r, fill, stroke):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * .45
        pts.append(f'{cx + rr * math.cos(a):.2f} {cy + rr * math.sin(a):.2f}')
    return f'<path d="M{"L".join(pts)}Z" fill="{fill}" stroke="{stroke}" stroke-width=".6" stroke-linejoin="round"/>'


def rng(seed):
    """Small deterministic generator, so the random-looking bits (speckles, fragments) never change between builds."""
    x = (seed * 2654435761 + 12345) & 0xffffffff
    while True:
        x = (1103515245 * x + 12345) & 0x7fffffff
        yield x / 0x7fffffff


# ---------------------------------------------------------------- styles (each returns markup on the 24-unit grid)
def cyberpunk(parts, i):
    return (glow(parts, '#fcee0a', 1.6, .8) + rim(parts, '#14141c', 1.6, .7)
            + P(parts, '#00f0ff', 1.5, op=.85, tr='translate(-.75 0)') + P(parts, '#ff003c', 1.5, op=.75, tr='translate(.75 0)')
            + P(parts, '#fcee0a', 1.6, fill='#fcee0a', fo=.14))


def borderlands(parts, i):
    hue = ['#ffd23f', '#ff8c3a', '#5fd0ff', '#a6d85c'][i % 4]
    return (P(parts, '#151515', 3.4, fill='#151515', tr='translate(.9 .9)')
            + P(parts, '#151515', 3.4) + P(parts, hue, 1.7, fill=hue, detail='#151515'))


def gta(parts, i):
    return (P(parts, '#000', 3.6, fill='#000', op=.35, tr='translate(.7 .8)')
            + P(parts, '#000', 3.4) + P(parts, '#ffffff', 1.9, fill='#ffffff', detail='#000'))


def minecraft(name):
    pal, rows = PIXELS[name] if name in PIXELS else pixelize.item(GLYPHS[name], M[MATERIAL[name]])
    return runs(rows, pal)


def fallout(parts, i):
    return glow(parts, '#2bff7a', 1.6) + rim(parts, '#03200d', 1.6) + P(parts, '#2bff7a', 1.6, fill='#2bff7a', fo=.14)


def zelda(parts, i):
    return glow(parts, '#3fd8f2', 1.2, .9) + rim(parts, '#0b2430', 1.2) + P(parts, '#5ae6ff', 1.2, fill='#5ae6ff', fo=.1) + '<circle cx="21" cy="3" r="1" fill="#ff8a1f"/>'


def halo(parts, i):
    return glow(parts, '#5fc8ff', 1.6) + rim(parts, '#06202f', 1.6) + P(parts, '#a9e8ff', 1.6, fill='#5fc8ff', fo=.2, cap='square', join='miter')


def persona(parts, i):
    return tilt(P(parts, '#e60012', 3.4, fill='#e60012', tr='translate(1 1)', join='miter')
                + P(parts, '#000', 3.6, join='miter') + P(parts, '#ffffff', 2, fill='#ffffff', detail='#000', join='miter'), -8)


def hollow_knight(parts, i):
    return glow(parts, '#dfe7f0', 1.35, .6) + rim(parts, '#141821', 1.35, .95) + P(parts, '#eef2f7', 1.35, fill='#eef2f7', fo=.08)


def hades(parts, i):
    return glow(parts, '#c9302c', 1.7, .9) + P(parts, '#2a0606', 3.2) + P(parts, '#f0c96a', 1.7, fill='#c9302c', fo=.9)


def portal(parts, i):
    return (P(parts, 'currentColor', 1.7, detail='#2aa7ff')
            + '<ellipse cx="3" cy="3.2" rx="1.3" ry=".7" fill="none" stroke="#ff9a00" stroke-width=".9"/>'
            + '<ellipse cx="21" cy="20.8" rx="1.3" ry=".7" fill="none" stroke="#2aa7ff" stroke-width=".9"/>')


def mass_effect(parts, i):
    return glow(parts, '#ff8a2a', 1.5) + rim(parts, '#2a1404', 1.5) + P(parts, '#ffab5e', 1.5, fill='#ff8a2a', fo=.16)


def doom(parts, i):
    return (P(parts, '#140300', 3.4, join='miter') + P(parts, '#ff4a1c', 1.9, fill='#ff4a1c', detail='#140300', join='miter')
            + P([p for p in parts if p[1] == 1], '#ffb08a', .5, op=.6, tr='translate(-.35 -.35)'))


def splatoon(parts, i):
    ink = ['#e8188c', '#bce61b', '#ff7a00', '#3d5cff', '#1ee6c4', '#a63dff'][i % 6]
    return (P(parts, '#20112e', 3.4) + P(parts, ink, 1.9, fill=ink, detail='#20112e')
            + f'<circle cx="20.2" cy="4.2" r="1.3" fill="{ink}"/><circle cx="3.6" cy="20.6" r=".9" fill="{ink}"/>')


def animal_crossing(parts, i):
    return P(parts, '#7a5634', 2.1, fill='#f3c86b') + '<path d="M18.6 2.2c2.6 0 3.6 1 3.6 3.6-2.6 0-3.6-1-3.6-3.6Z" fill="#7cc46b"/>'


def hotline(parts, i):
    grad = ('<defs><linearGradient id="__ID__-g" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#ff2a6d"/><stop offset="1" stop-color="#05d9e8"/></linearGradient></defs>')
    return (grad + glow(parts, '#ff2a6d', 1.9, .8) + P(parts, '#05d9e8', 1.5, op=.4, tr='translate(.9 .4)') + rim(parts, '#1a0630', 1.9, .8)
            + P(parts, 'url(#__ID__-g)', 1.9, fill='#ff2a6d', fo=.12))


def mirrors_edge(parts, i):
    rest, last = (parts[:-1], parts[-1:]) if len(parts) > 1 else (parts, [])
    return P(rest, 'currentColor', 1.5, detail='#e1251b') + P(last, '#e1251b', 1.8) + ('' if last else '<rect x="19.5" y="1.5" width="3" height="3" fill="#e1251b"/>')


def diablo(parts, i):
    return glow(parts, '#b01414', 1.7, 1.1) + P(parts, '#000', 3.2) + P(parts, '#e9c27a', 1.7, fill='#8e1414', fo=.9)


def pacman(parts, i):
    mask = (f'<mask id="__ID__-m" maskUnits="userSpaceOnUse" x="-1" y="-1" width="26" height="26">'
            f'{P(parts, "#fff", 3)}{P(parts, "#000", 1)}</mask>')
    return f'{mask}<rect x="-1" y="-1" width="26" height="26" fill="#2b2bff" mask="url(#__ID__-m)"/>'


def overwatch(parts, i):
    return P(parts, '#2b3a4f', 3.2, op=.9) + P(parts, '#ffffff', 1.9, fill='#f99e1a', fo=.95)


def super_mario(parts, i):
    nd = nodet(parts)
    return (grad('r', [(0, '#ff6a5c'), (1, '#c8101e')], 0, 4, 0, 20) + P(parts, '#141414', 3.6)
            + P(nd, 'url(#__ID__-r)', 2, fill='url(#__ID__-r)') + bevel(nd, '#ffffff', .8, .8, 2, 'h', .5) + P(det(parts), '#ffd23a', 2))


def sonic(parts, i):
    nd = nodet(parts)
    lines = '<path d="M-.6 7.6h3.6M-.9 11.6h3M-.3 15.6h3.3" stroke="#59c2ff" stroke-width="1.1" stroke-linecap="round"/>'
    return lines + (f'<g transform="translate(2.6 0) skewX(-10)">{P(parts, "#0a1c56", 3.4)}{P(nd, "#1f63e6", 2, fill="#1f63e6")}'
                    f'{bevel(nd, "#8fd3ff", .7, .7, 2, "h", .8)}{P(det(parts), "#ffffff", 2)}</g>')


def pokemon(parts, i):
    rows = pixelize.shaded(*pixelize.grid(parts, 16, 1))
    pal = {'a': '#8bac0f', 'b': '#a9c934', 'c': '#306230', 'k': '#0f380f'}
    lcd = ('<defs><pattern id="__ID__-p" width="1" height="1" patternUnits="userSpaceOnUse"><rect x=".08" y=".08" width=".84" height=".84" fill="#fff"/></pattern></defs>'
           '<mask id="__ID__-m" maskUnits="userSpaceOnUse" x="0" y="0" width="16" height="16"><rect width="16" height="16" fill="url(#__ID__-p)"/></mask>')
    return lcd + f'<g mask="url(#__ID__-m)">{runs(rows, pal)}</g>'


TETRO = ['#00d8f0', '#f6d800', '#a74dff', '#28d94a', '#ff3b3b', '#3a6bff', '#ff9a1f']


def tetris(parts, i):
    B, D = pixelize.grid(parts, 12, 0, .45, .35)
    rows = [''.join('a' if B[y][x] and not D[y][x] else '.' for x in range(12)) for y in range(12)]
    c = TETRO[i % len(TETRO)]
    block = (f'<defs><pattern id="__ID__-b" width="1" height="1" patternUnits="userSpaceOnUse"><rect width="1" height="1" fill="{c}"/>'
             '<path d="M0 0H1L.8 .2H.2V.8L0 1Z" fill="#fff" fill-opacity=".55"/><path d="M1 1H0L.2 .8H.8V.2L1 0Z" fill="#000" fill-opacity=".4"/>'
             '<rect x=".03" y=".03" width=".94" height=".94" fill="none" stroke="#000" stroke-opacity=".35" stroke-width=".06"/></pattern></defs>')
    return block + runs(rows, {'a': 'url(#__ID__-b)'})


def space_invaders(parts, i):
    n = 13
    B, D = pixelize.grid(parts, n, 1)
    rows = flat_pixels(B, D, lambda x, y: 'r' if y < 3 else ('g' if y >= n - 3 else 'w'))
    return runs(rows, {'r': '#ff4b5c', 'w': '#f2f2f2', 'g': '#3cff5f', 'k': '#0c0c16'})


def undertale(parts, i):
    B, D = pixelize.grid(parts, 16, 1)
    soul = ICONS[i] in ('heart', 'health')
    rows = flat_pixels(B, D, lambda x, y: 'r' if soul else 'w')
    return runs(rows, {'w': '#ffffff', 'r': '#ff1414', 'k': '#000000'})


def asteroids(parts, i):
    v = [(pixelize.polyline(d), k) for d, k in parts]
    return glow(v, '#cfe2ff', 1.1, 1.4) + rim(v, '#05070d', 1.1, .8) + P(v, '#f5f9ff', 1.1, join='miter')


def kirby(parts, i):
    nd = nodet(parts)
    return (P(nd, '#a8285e', 4) + P(nd, '#ff9cc6', 2.5, fill='#ff9cc6') + bevel(nd, '#ffe6f0', .7, .7, 2.5, 'h', .9)
            + P(det(parts), '#a8285e', 1.7) + star(21, 3, 2, '#ffd84a', '#8a5a00'))


def final_fantasy(parts, i):
    return (grad('b', [(0, '#7096f0'), (1, '#141c66')], 0, 3, 0, 21) + P(parts, '#090c2e', 3.3)
            + P(parts, '#f2f5ff', 1.7, fill='url(#__ID__-b)', detail='#f2f5ff'))


CREW = ['#d61a1a', '#1d3fe0', '#14913a', '#f05bc0', '#f5820f', '#f2e94a', '#38e8d0', '#7a3bd0', '#7e5226', '#5be34a']


def among_us(parts, i):
    c = CREW[i % len(CREW)]; nd = nodet(parts)
    return (P(parts, '#000', 3.9) + P(nd, c, 2.1, fill=c) + bevel(nd, pixelize._mix(c, '#000000', .4), -1.2, -.6, 2.1, 's')
            + P(det(parts), '#9fd6e8', 2.1) + bevel(det(parts), '#ffffff', .5, .5, 2.1, 'v', .9))


def okami(parts, i):
    w = [(pixelize.wobble(d, .16, i + 5), k) for d, k in parts]
    return (P(parts, '#f4ecd6', 4.8, fill='#f4ecd6', op=.92) + '<rect x="19.9" y="19.7" width="3" height="3" rx=".5" fill="#c8281e"/>'
            + P(w, '#16120e', 3, fill='#16120e', fo=.1, op=.22) + P(w, '#16120e', 1.9) + P(parts, '#16120e', 1, op=.8, tr='translate(.4 -.35)'))


def cuphead(parts, i):
    w = [(pixelize.wobble(d, .3, i), k) for d, k in parts]
    return (P(w, '#5a3b22', 2.6, fill='#5a3b22', op=.35, tr='translate(.8 .9)') + P(w, '#f6ecd2', 4.4)
            + P(w, '#1b1410', 2.3, fill='#f6ecd2', detail='#d22b1f'))


def limbo(parts, i):
    nd = nodet(parts)
    return (P(parts, '#d9dde0', 7.4, op=.1) + P(parts, '#d9dde0', 4.6, op=.24)
            + P(nd, '#0a0a0a', 2.2, fill='#0a0a0a') + P(det(parts), '#f4f4f4', 1.3))


def monument_valley(parts, i):
    nd = nodet(parts)
    side = f'<defs><g id="__ID__-s">{P(nd, "#5e3f8c", 1.8, fill="#5e3f8c")}</g></defs>'
    side += ''.join(f'<use href="#__ID__-s" transform="translate({k * .3:.1f} {k * .3:.1f})"/>' for k in range(6, 0, -1))
    return side + P(parts, '#ff8b78', 1.8, fill='#ffd4c3', detail='#5f4590')


def obra_dinn(parts, i):
    dots = ('<defs><pattern id="__ID__-d" width="2" height="2" patternUnits="userSpaceOnUse"><g shape-rendering="crispEdges" fill="#e8e3c4">'
            '<rect width="1" height="1"/><rect x="1" y="1" width="1" height="1"/></g></pattern></defs>')
    return dots + rim(parts, '#26261e', 1.4, .9) + P(parts, '#e8e3c4', 1.4, fill='url(#__ID__-d)', detail='#e8e3c4')


def firewatch(parts, i):
    return (grad('f', [(0, '#ffbe45'), (.5, '#f2703a'), (1, '#9a2a56')], 0, 3, 0, 21)
            + P(parts, 'url(#__ID__-f)', 1.9, fill='url(#__ID__-f)', detail='#3d1230'))


def nier(parts, i):
    return (P(parts, '#4a463b', 1.5, fill='#4a463b', fo=.6, op=.7, tr='translate(1.1 1.1)') + rim(parts, '#2b2924', 1.5, .8)
            + P(parts, '#dcd6bc', 1.5, fill='#dcd6bc', fo=.15))


def superhot(parts, i):
    facets = [(0, '#ff7d6e'), (.42, '#ff5242'), (.42, '#e2231a'), (.68, '#e2231a'), (.68, '#a40f0a'), (1, '#a40f0a')]
    return grad('s', facets, 4, 4, 20, 20) + rim(parts, '#2a0402', 1.8, .8) + P(parts, 'url(#__ID__-s)', 1.8, fill='url(#__ID__-s)', detail='#ffffff')


CRAFT = ['#ff5a5a', '#ffad2a', '#38b2ff', '#66cc44', '#a57aff', '#ff76b3']


def littlebigplanet(parts, i):
    c = CRAFT[i % len(CRAFT)]; nd = nodet(parts)
    return (P(nd, '#000', 5.4, fill='#000', op=.22, tr='translate(.5 .9)') + P(nd, '#cfcfcf', 5.5, fill='#cfcfcf') + P(nd, '#ffffff', 5, fill='#ffffff')
            + P(nd, c, 2, fill=c) + P(det(parts), '#3b2a20', 2))


def bioshock(parts, i):
    gold = [(0, '#fff0b3'), (.42, '#e3b44c'), (.5, '#8a5a17'), (.62, '#d9a843'), (1, '#f6d77a')]
    return grad('g', gold, 0, 3, 0, 21) + P(parts, '#160f04', 3.4) + P(parts, 'url(#__ID__-g)', 1.9, fill='#0f3d3b', fo=.95, detail='url(#__ID__-g)')


def witcher(parts, i):
    steel = [(0, '#ffffff'), (.45, '#c3c9d0'), (.55, '#5f666e'), (1, '#d5dadf')]
    return grad('m', steel, 0, 3, 0, 21) + rim(parts, '#0e1012', 1.4, .9) + P(parts, 'url(#__ID__-m)', 1.4, detail='#c4231d')


def elden_ring(parts, i):
    return glow(parts, '#f0c25a', 2.4, 1.1) + P(parts, '#f3d488', 2.4, fill='#f3d488', fo=.1) + P(parts, '#1d1508', .85)


def red_dead(parts, i):
    g = rng(i + 7); holes = []
    for _ in range(16):
        holes.append(f'<circle cx="{3 + next(g) * 18:.1f}" cy="{3 + next(g) * 18:.1f}" r="{.22 + next(g) * .4:.2f}"/>')
    worn = (f'<mask id="__ID__-w" maskUnits="userSpaceOnUse" x="-1" y="-1" width="26" height="26">'
            f'<rect x="-1" y="-1" width="26" height="26" fill="#fff"/><g fill="#000">{"".join(holes)}</g></mask>')
    return worn + rim(parts, '#22100a', 2, .9) + f'<g mask="url(#__ID__-w)">{P(parts, "#b8321f", 2, fill="#b8321f", detail="#22100a")}</g>'


def assassins_creed(parts, i):
    g = rng(i + 3); spots = [(-.2, 4), (22.4, 7.6), (.6, 18.2), (21.2, 21.4), (20.4, .4), (-.4, 11), (23, 14.2), (9.5, -.6)]
    frags = ''
    for k in range(5):
        x, y = spots[(i + k * 3) % len(spots)]; s = .7 + next(g) * .8
        frags += f'<rect x="{x:.1f}" y="{y:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{"#7fd0ff" if k % 2 else "#f5f8fb"}" fill-opacity=".9"/>'
    return (P(parts, '#7fd0ff', 1.4, op=.55, tr='translate(-.8 .2)') + rim(parts, '#0b1620', 1.4, .8)
            + P(parts, '#f5f8fb', 1.4, fill='#f5f8fb', fo=.1) + frags)


def disco_elysium(parts, i):
    nd = nodet(parts); w = [(pixelize.wobble(d, .25, i + 11), k) for d, k in parts]
    return (P(nd, '#e0743c', 3.4, fill='#e0743c', op=.75, tr='translate(-.7 .6)') + P(nd, '#3c9a9f', 3.4, fill='#3c9a9f', op=.7, tr='translate(.7 -.5)')
            + P(w, '#efe6d6', 2.7, op=.85) + P(w, '#1c1a19', 1.3))


RARITY = [('#e0e5ea', '#98a4b0'), ('#c5f77e', '#5cc12a'), ('#9fe6ff', '#2d9bf0'), ('#e6b0ff', '#ad40ec'), ('#ffe39a', '#f29a26')]


def fortnite(parts, i):
    light, mid = RARITY[i % len(RARITY)]; nd = nodet(parts)
    return (grad('r', [(0, light), (1, mid)], 0, 3, 0, 21) + glow(nd, mid, 2.2, 1.4) + P(parts, '#0c1030', 3.6)
            + P(nd, 'url(#__ID__-r)', 2.1, fill='url(#__ID__-r)') + P(det(parts), '#0c1030', 2.1))


def half_life(parts, i):
    return rim(parts, '#2b1a00', 1.6, .55) + P(parts, '#ffa10a', 1.6, fill='#ffa10a', fo=.5, op=.92, detail='#ffe2a3', cap='butt', join='miter')


def dead_space(parts, i):
    scan = ('<defs><pattern id="__ID__-l" width="1" height="1.6" patternUnits="userSpaceOnUse"><rect width="1" height="1" fill="#fff"/></pattern></defs>'
            '<mask id="__ID__-m" maskUnits="userSpaceOnUse" x="-1" y="-1" width="26" height="26"><rect x="-1" y="-1" width="26" height="26" fill="url(#__ID__-l)"/></mask>')
    return (scan + glow(parts, '#47b8ff', 1.5, .9) + rim(parts, '#04162a', 1.5, .7)
            + f'<g mask="url(#__ID__-m)">{P(parts, "#a6e6ff", 1.5, fill="#47b8ff", fo=.45)}</g>')


def god_of_war(parts, i):
    nd = nodet(parts); runes = det(parts)
    return (P(nd, '#f4f8f9', 2, fill='#f4f8f9', op=.8, tr='translate(.6 .6)') + P(nd, '#0f1314', 2, fill='#0f1314', tr='translate(-.6 -.6)')
            + P(nd, '#86939a', 2, fill='#6e7b80') + glow(runes, '#5fd2ff', 1.4, 1.3) + P(runes, '#a6ecff', 1.4))


RAINBOW = ['#ff4d6d', '#ff9f1c', '#ffe14d', '#4cd964', '#33b5ff', '#a66bff']


def katamari(parts, i):
    stops = []
    for k, c in enumerate(RAINBOW):
        stops += [(round(k / 6, 3), c), (round((k + 1) / 6, 3), c)]
    return grad('k', stops, 0, 3.5, 0, 20.5) + P(parts, '#2a1b3d', 3.4) + P(parts, 'url(#__ID__-k)', 1.9, fill='url(#__ID__-k)', detail='#2a1b3d')


# (folder and import path, component prefix, inspired by, look, function)
STYLES = [
    ('cyberpunk', 'Cyberpunk', 'Cyberpunk 2077', 'Neon yellow with a cyan/red glitch split', cyberpunk),
    ('borderlands', 'Borderlands', 'Borderlands', 'Cel-shaded: heavy black ink outline, flat colour, comic drop shadow', borderlands),
    ('gta', 'Gta', 'Grand Theft Auto', 'Radar blip: white glyph, black outline, soft shadow', gta),
    ('minecraft', 'Minecraft', 'Minecraft', 'Shaded 16×16 pixel items in material colours', None),
    ('fallout', 'Fallout', 'Fallout', 'Phosphor-green terminal line with glow', fallout),
    ('zelda', 'Zelda', 'Zelda: Breath of the Wild', 'Thin cyan slate line, soft glow, one orange spark', zelda),
    ('halo', 'Halo', 'Halo', 'Square-cut cyan HUD line with glow', halo),
    ('persona', 'Persona', 'Persona 5', 'Tilted white cut-out, black outline, red offset', persona),
    ('hollow-knight', 'HollowKnight', 'Hollow Knight', 'Pale thin ink with a faint halo', hollow_knight),
    ('hades', 'Hades', 'Hades', 'Gold line over blood red, dark outline, ember glow', hades),
    ('portal', 'Portal', 'Portal', 'Clean line in your text colour, blue details, orange and blue rings', portal),
    ('mass-effect', 'MassEffect', 'Mass Effect', 'Orange holographic line with glow', mass_effect),
    ('doom', 'Doom', 'Doom', 'Hellfire-orange solid, hard dark outline, hot edge', doom),
    ('splatoon', 'Splatoon', 'Splatoon', 'Neon ink fill, dark outline, ink droplets; colour changes per icon', splatoon),
    ('animal-crossing', 'AnimalCrossing', 'Animal Crossing', 'Warm brown rounded line, honey fill, a leaf', animal_crossing),
    ('hotline-miami', 'Hotline', 'Hotline Miami', 'Magenta-to-cyan gradient, glow and ghost offset', hotline),
    ('mirrors-edge', 'MirrorsEdge', "Mirror's Edge", 'Minimal line in your text colour with runner-vision red', mirrors_edge),
    ('diablo', 'Diablo', 'Diablo', 'Bone-gold line over blood red, black outline, red glow', diablo),
    ('pac-man', 'PacMan', 'Pac-Man', 'Arcade maze: double blue walls, hollow inside', pacman),
    ('overwatch', 'Overwatch', 'Overwatch', 'Bold white line, orange fill, slate edge', overwatch),
    ('super-mario', 'SuperMario', 'Super Mario', 'Glossy red with a thick black outline and yellow details', super_mario),
    ('sonic', 'Sonic', 'Sonic the Hedgehog', 'Cobalt blue, slanted forward, speed lines', sonic),
    ('pokemon', 'Pokemon', 'Pokémon Red and Blue', 'Game Boy pixels: four shades of green on an LCD grid', pokemon),
    ('tetris', 'Tetris', 'Tetris', 'Bevelled blocks; colour changes per icon like the pieces', tetris),
    ('space-invaders', 'SpaceInvaders', 'Space Invaders', 'Chunky 1-bit sprites under red, white and green overlay bands', space_invaders),
    ('undertale', 'Undertale', 'Undertale', 'White 1-bit pixels with a black outline; hearts in soul red', undertale),
    ('asteroids', 'Asteroids', 'Asteroids', 'Low-poly white vector line with phosphor glow', asteroids),
    ('kirby', 'Kirby', 'Kirby', 'Puffy pink with a soft highlight and a warp star', kirby),
    ('final-fantasy', 'FinalFantasy', 'Final Fantasy', 'Menu-window blue gradient with a white border', final_fantasy),
    ('among-us', 'AmongUs', 'Among Us', 'Thick black outline, crewmate colour with a back shadow, visor-blue details; colour changes per icon', among_us),
    ('okami', 'Okami', 'Ōkami', 'Sumi-e ink on rice paper with a red seal', okami),
    ('cuphead', 'Cuphead', 'Cuphead', 'Wobbly 1930s cartoon ink, cream fill, red details, sepia shadow', cuphead),
    ('limbo', 'Limbo', 'Limbo', 'Black silhouette in grey fog, glowing white eyes', limbo),
    ('monument-valley', 'MonumentValley', 'Monument Valley', 'Pastel coral face with a lavender isometric extrusion', monument_valley),
    ('obra-dinn', 'ObraDinn', 'Return of the Obra Dinn', '1-bit: cream line with a dithered fill', obra_dinn),
    ('firewatch', 'Firewatch', 'Firewatch', 'Flat sunset gradient, no outline', firewatch),
    ('nier-automata', 'Nier', 'NieR:Automata', 'Beige UI line with a dark offset shadow', nier),
    ('superhot', 'Superhot', 'Superhot', 'Faceted red glass with white details', superhot),
    ('littlebigplanet', 'LittleBigPlanet', 'LittleBigPlanet', 'Craft sticker: white border, bright fill, soft shadow; colour changes per icon', littlebigplanet),
    ('bioshock', 'Bioshock', 'BioShock', 'Art Deco brass line over deep teal', bioshock),
    ('the-witcher', 'Witcher', 'The Witcher', 'Thin brushed-steel line with blood-red details', witcher),
    ('elden-ring', 'EldenRing', 'Elden Ring', 'Double gold line with a grace glow', elden_ring),
    ('red-dead-redemption', 'RedDead', 'Red Dead Redemption', 'Worn red print, speckled like an old wanted poster', red_dead),
    ('assassins-creed', 'AssassinsCreed', "Assassin's Creed", 'Animus white with a blue echo and floating data fragments', assassins_creed),
    ('disco-elysium', 'DiscoElysium', 'Disco Elysium', 'Hand-drawn line over offset orange and teal paint', disco_elysium),
    ('fortnite', 'Fortnite', 'Fortnite', 'Bold outline, loot-rarity gradient and glow; rarity changes per icon', fortnite),
    ('half-life', 'HalfLife', 'Half-Life', 'Translucent amber HUD shapes, square cuts', half_life),
    ('dead-space', 'DeadSpace', 'Dead Space', 'Blue hologram with scanlines and glow', dead_space),
    ('god-of-war', 'GodOfWar', 'God of War', 'Carved stone with frost-blue glowing runes', god_of_war),
    ('katamari', 'Katamari', 'Katamari Damacy', 'Rainbow stripes with a dark outline', katamari),
]

# Groups for the README and the preview, in display order
CATEGORIES = [
    ('Neon and glow', ['cyberpunk', 'fallout', 'zelda', 'halo', 'mass-effect', 'hotline-miami', 'hollow-knight', 'elden-ring', 'dead-space', 'assassins-creed']),
    ('Bold cartoon', ['borderlands', 'gta', 'persona', 'splatoon', 'overwatch', 'doom', 'super-mario', 'sonic', 'kirby', 'among-us', 'fortnite', 'littlebigplanet', 'katamari', 'animal-crossing']),
    ('Pixel and arcade', ['minecraft', 'pokemon', 'tetris', 'space-invaders', 'undertale', 'pac-man', 'asteroids', 'obra-dinn']),
    ('Ink and paint', ['okami', 'cuphead', 'red-dead-redemption', 'disco-elysium', 'limbo']),
    ('Metal, stone and dark fantasy', ['hades', 'diablo', 'bioshock', 'the-witcher', 'god-of-war']),
    ('Flat and graphic', ['portal', 'mirrors-edge', 'firewatch', 'monument-valley', 'nier-automata', 'superhot', 'final-fantasy', 'half-life']),
]
CATEGORY = {slug: name for name, slugs in CATEGORIES for slug in slugs}
assert sorted(CATEGORY) == sorted(s[0] for s in STYLES), set(s[0] for s in STYLES) ^ set(CATEGORY)
VIEWBOXES = {'minecraft': '0 0 16 16', 'pokemon': '0 0 16 16', 'undertale': '0 0 16 16', 'tetris': '0 0 12 12', 'space-invaders': '0 0 13 13'}


def pascal(s):
    return ''.join(w.capitalize() for w in re.split(r'[-_ ]', s))


def body(slug, fn, name, i):
    return minecraft(name) if slug == 'minecraft' else fn(GLYPHS[name], i)


def viewbox(slug):
    return VIEWBOXES.get(slug, VIEWBOX)


# ---------------------------------------------------------------- outputs
BASE_JS = """import * as React from 'react';

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

/** Builds an icon component from static SVG markup (generated by gen.py). */
export function createIcon(name, viewBox, markup) {
  const Icon = React.forwardRef(function Icon({ size = '1em', title, children, ...props }, ref) {
    const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, '');
    let html = markup.includes('__ID__') ? markup.split('__ID__').join('gsi' + uid) : markup;
    if (title) html = '<title>' + esc(title) + '</title>' + html;
    return React.createElement('svg', {
      xmlns: 'http://www.w3.org/2000/svg', viewBox, width: size, height: size, fill: 'none',
      role: title ? 'img' : undefined, 'aria-hidden': title ? undefined : true, focusable: 'false',
      ...props, ref, dangerouslySetInnerHTML: { __html: html },
    });
  });
  Icon.displayName = name;
  return Icon;
}
"""
BASE_DTS = """import * as React from 'react';

export interface GameIconProps extends Omit<React.SVGProps<SVGSVGElement>, 'ref'> {
  /** Width and height. Default '1em', so the icon follows the font size. */
  size?: string | number;
  /** Accessible name. Without it the icon is hidden from screen readers. */
  title?: string;
}
export type GameIcon = React.ForwardRefExoticComponent<GameIconProps & React.RefAttributes<SVGSVGElement>>;
export declare function createIcon(name: string, viewBox: string, markup: string): GameIcon;
"""


# Framework-free outputs: functions that return SVG markup as a string, and the <game-icon> web component
RENDER_JS = """let n = 0;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

/** Builds a function that returns the icon as an SVG string (generated by gen.py). Every call gets its own ids. */
export function createIconString(viewBox, markup) {
  return function icon({ size = '1em', title, class: cls, attrs = {} } = {}) {
    let html = markup.includes('__ID__') ? markup.split('__ID__').join('gsi-s' + (++n).toString(36)) : markup;
    if (title) html = '<title>' + esc(title) + '</title>' + html;
    const extra = Object.entries(attrs).map(([k, v]) => ' ' + k + '="' + esc(v) + '"').join('');
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + viewBox + '" width="' + esc(size) + '" height="' + esc(size) + '" fill="none" focusable="false"'
      + (title ? ' role="img"' : ' aria-hidden="true"') + (cls ? ' class="' + esc(cls) + '"' : '') + extra + '>' + html + '</svg>';
  };
}
"""
RENDER_DTS = """export interface IconStringOptions {
  /** Width and height. Default '1em', so the icon follows the font size. */
  size?: string | number;
  /** Accessible name. Without it the icon gets aria-hidden. */
  title?: string;
  /** Class attribute for the <svg>. */
  class?: string;
  /** Any other attributes for the <svg>. */
  attrs?: Record<string, string | number>;
}
/** Returns the icon as an SVG string. */
export type IconString = (options?: IconStringOptions) => string;
export declare function createIconString(viewBox: string, markup: string): IconString;
"""
ELEMENT_JS = """// <game-icon set="cyberpunk" name="heart" size="32" label="Lives"></game-icon>
// A standard web component: works in plain HTML and in any framework. Loads one style module on first use.
const PREFIX = __PREFIX__;
const pascal = (s) => s.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join('');
const cache = new Map();
const load = (set) => {
  if (!cache.has(set)) cache.set(set, import(`./html/${set}.js`));
  return cache.get(set);
};
const Base = typeof HTMLElement === 'undefined' ? class {} : HTMLElement;

export class GameIconElement extends Base {
  static get observedAttributes() { return ['set', 'name', 'size', 'label']; }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  async render() {
    const set = this.getAttribute('set'), name = this.getAttribute('name') || '';
    const label = this.getAttribute('label');
    const raw = (this.getAttribute('size') || '1em').replace(/[^0-9a-z.%]/gi, '');
    const size = /^[0-9.]+$/.test(raw) ? raw + 'px' : raw;
    if (label) { this.setAttribute('role', 'img'); this.setAttribute('aria-label', label); this.removeAttribute('aria-hidden'); }
    else { this.removeAttribute('role'); this.removeAttribute('aria-label'); this.setAttribute('aria-hidden', 'true'); }
    const root = this.shadowRoot || this.attachShadow({ mode: 'open' });
    const ticket = (this._ticket = (this._ticket || 0) + 1);
    const css = '<style>:host{display:inline-block;width:' + size + ';height:' + size + ';line-height:0;vertical-align:-0.125em}svg{display:block;width:100%;height:100%}</style>';
    if (!Object.prototype.hasOwnProperty.call(PREFIX, set)) { root.innerHTML = css; return; }
    let mod;
    try { mod = await load(set); } catch (e) { root.innerHTML = css; return; }
    if (ticket !== this._ticket) return;
    const icon = mod[PREFIX[set] + pascal(name)];
    root.innerHTML = css + (icon ? icon({ size: '100%' }) : '');
  }
}

if (typeof customElements !== 'undefined' && !customElements.get('game-icon')) customElements.define('game-icon', GameIconElement);
"""
ELEMENT_DTS = """/** <game-icon set="cyberpunk" name="heart" size="32" label="Lives"> */
export declare class GameIconElement extends HTMLElement {}
declare global {
  interface HTMLElementTagNameMap { 'game-icon': GameIconElement; }
}
"""



def build():
    for d in ('src', 'svg', 'icons', 'sprites'):
        shutil.rmtree(os.path.join(HERE, d), ignore_errors=True)
    os.makedirs(os.path.join(HERE, 'src', 'html'))
    open(os.path.join(HERE, 'src', '_base.js'), 'w').write(BASE_JS)
    open(os.path.join(HERE, 'src', '_base.d.ts'), 'w').write(BASE_DTS)
    open(os.path.join(HERE, 'src', 'html', '_render.js'), 'w').write(RENDER_JS)
    open(os.path.join(HERE, 'src', 'html', '_render.d.ts'), 'w').write(RENDER_DTS)
    prefixes = json.dumps({slug: prefix for slug, prefix, *_ in STYLES}, separators=(',', ':'))
    open(os.path.join(HERE, 'src', 'element.js'), 'w').write(ELEMENT_JS.replace('__PREFIX__', prefixes))
    open(os.path.join(HERE, 'src', 'element.d.ts'), 'w').write(ELEMENT_DTS)
    index_js, index_dts, manifest = [], [], []
    html_index = []
    for slug, prefix, title, desc, fn in STYLES:
        os.makedirs(os.path.join(HERE, 'svg', slug))
        js = ["import { createIcon } from './_base.js';", '']
        dts = ["import type { GameIcon } from './_base.js';", "export type { GameIcon, GameIconProps } from './_base.js';", '']
        hjs = ["import { createIconString } from './_render.js';", '']
        hdts = ["import type { IconString } from './_render.js';", "export type { IconString, IconStringOptions } from './_render.js';", '']
        for i, name in enumerate(ICONS):
            mk = body(slug, fn, name, i)
            comp = prefix + pascal(name)
            js.append(f"export const {comp} = /*#__PURE__*/ createIcon('{comp}', '{viewbox(slug)}', {json.dumps(mk)});")
            dts.append(f'export declare const {comp}: GameIcon;')
            hjs.append(f"export const {comp} = /*#__PURE__*/ createIconString('{viewbox(slug)}', {json.dumps(mk)});")
            hdts.append(f'export declare const {comp}: IconString;')
            static = mk.replace('__ID__', f'gsi-{slug}-{name}')
            label = name.replace('-', ' ')
            open(os.path.join(HERE, 'svg', slug, f'{name}.svg'), 'w').write(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="{viewbox(slug)}" fill="none" role="img" aria-label="{label}"><title>{label}</title>{static}</svg>\n')
        open(os.path.join(HERE, 'src', f'{slug}.js'), 'w').write('\n'.join(js) + '\n')
        open(os.path.join(HERE, 'src', f'{slug}.d.ts'), 'w').write('\n'.join(dts) + '\n')
        open(os.path.join(HERE, 'src', 'html', f'{slug}.js'), 'w').write('\n'.join(hjs) + '\n')
        open(os.path.join(HERE, 'src', 'html', f'{slug}.d.ts'), 'w').write('\n'.join(hdts) + '\n')
        html_index.append(f"export * from './{slug}.js';")
        index_js.append(f"export * from './{slug}.js';")
        index_dts.append(f"export * from './{slug}.js';")
        manifest.append({'style': slug, 'prefix': prefix, 'inspiredBy': title, 'look': desc, 'category': CATEGORY[slug], 'icons': [prefix + pascal(n) for n in ICONS]})
    index_dts.insert(0, "export type { GameIcon, GameIconProps } from './_base.js';")
    open(os.path.join(HERE, 'src', 'index.js'), 'w').write('\n'.join(index_js) + '\n')
    open(os.path.join(HERE, 'src', 'index.d.ts'), 'w').write('\n'.join(index_dts) + '\n')
    open(os.path.join(HERE, 'src', 'html', 'index.js'), 'w').write('\n'.join(html_index) + '\n')
    open(os.path.join(HERE, 'src', 'html', 'index.d.ts'), 'w').write("export type { IconString, IconStringOptions } from './_render.js';\n" + '\n'.join(html_index) + '\n')
    open(os.path.join(HERE, 'icons.json'), 'w').write(json.dumps(manifest, indent=1) + '\n')
    preview()
    readme()
    package()
    site_data()
    print(len(STYLES), 'styles x', len(ICONS), 'icons =', len(STYLES) * len(ICONS), 'components')


ICON_GROUPS = [
    ('Basics', ICONS[:12]), ('Navigation', ICONS[12:21]), ('Actions', ICONS[21:35]), ('Status', ICONS[35:42]), ('Media', ICONS[42:51]),
    ('People and time', ICONS[51:58]), ('Shopping', ICONS[58:63]), ('Files and data', ICONS[63:68]), ('Everyday', ICONS[68:72]), ('Game', ICONS[72:]),
]
assert sum(len(g) for _, g in ICON_GROUPS) == len(ICONS)


def package():
    """Keeps package.json's exports and description in step with STYLES."""
    path = os.path.join(HERE, 'package.json'); pk = json.load(open(path))
    ex = {'.': {'types': './src/index.d.ts', 'import': './src/index.js', 'default': './src/index.js'}}
    for slug, *_ in STYLES:
        ex[f'./{slug}'] = {'types': f'./src/{slug}.d.ts', 'import': f'./src/{slug}.js', 'default': f'./src/{slug}.js'}
    ex['./html'] = {'types': './src/html/index.d.ts', 'import': './src/html/index.js', 'default': './src/html/index.js'}
    for slug, *_ in STYLES:
        ex[f'./html/{slug}'] = {'types': f'./src/html/{slug}.d.ts', 'import': f'./src/html/{slug}.js', 'default': f'./src/html/{slug}.js'}
    ex['./element'] = {'types': './src/element.d.ts', 'import': './src/element.js', 'default': './src/element.js'}
    ex['./svg/*'] = './svg/*'; ex['./icons.json'] = './icons.json'
    pk['exports'] = ex
    pk['sideEffects'] = ['./src/element.js']
    pk['peerDependenciesMeta'] = {'react': {'optional': True}}
    pk['description'] = (f'{len(ICONS)} UI and game icons in {len(STYLES)} styles inspired by video games ({len(ICONS) * len(STYLES):,} SVG icons): '
                         'React components, a <game-icon> web component for any framework, SVG strings and plain SVG files.')
    open(path, 'w').write(json.dumps(pk, indent=2, ensure_ascii=False) + '\n')


# Landing page: the spot ink each world prints the manual in (site/data.js)
INK = {
    'cyberpunk': '#f3e600', 'borderlands': '#f7a400', 'gta': '#2e8b3e', 'minecraft': '#5d9e3a', 'fallout': '#1fd65f',
    'zelda': '#1aa6c4', 'halo': '#5a7a32', 'persona': '#e60012', 'hollow-knight': '#3a4a6b', 'hades': '#b3261e',
    'portal': '#ff8a00', 'mass-effect': '#e8701a', 'doom': '#c81e0f', 'splatoon': '#e8188c', 'animal-crossing': '#7cc46b',
    'hotline-miami': '#ff2a6d', 'mirrors-edge': '#e1251b', 'diablo': '#8e1414', 'pac-man': '#2b2bff', 'overwatch': '#f99e1a',
    'super-mario': '#e52521', 'sonic': '#1f63e6', 'pokemon': '#8bac0f', 'tetris': '#00b4d8', 'space-invaders': '#3cff5f',
    'undertale': '#111111', 'asteroids': '#1b1f2a', 'kirby': '#ff8fbf', 'final-fantasy': '#2a3fa8', 'among-us': '#c51111',
    'okami': '#c8281e', 'cuphead': '#e04a2f', 'limbo': '#2b2b2b', 'monument-valley': '#ff8b78', 'obra-dinn': '#2f2f26',
    'firewatch': '#f2703a', 'nier-automata': '#c9c3a8', 'superhot': '#e2231a', 'littlebigplanet': '#c9945a', 'bioshock': '#0f3d3b',
    'the-witcher': '#50585f', 'elden-ring': '#c9a548', 'red-dead-redemption': '#b8321f', 'assassins-creed': '#3d7cc9',
    'disco-elysium': '#e0743c', 'fortnite': '#ad40ec', 'half-life': '#ff9f0a', 'dead-space': '#2f8fd8', 'god-of-war': '#7e1d1d',
    'katamari': '#ff4d6d',
}
assert sorted(INK) == sorted(s[0] for s in STYLES)


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def on_ink(h):
    """Black or white text on the ink, whichever contrasts more."""
    L = _lum(h)
    return '#ffffff' if (1.05 / (L + .05)) >= ((L + .05) / (_lum('#121212') + .05)) else '#121212'


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def print_ink(h):
    """The world's ink, nudged darker (white text) or lighter (black text) until small text on it reaches 4.6:1."""
    text = on_ink(h); ink = h
    for k in range(1, 40):
        if _contrast(ink, text) >= 4.6:
            break
        ink = pixelize._mix(h, '#000000' if text == '#ffffff' else '#ffffff', k * .02)
    return ink, text


def site_data():
    by_slug = {s[0]: s for s in STYLES}
    styles = [{'slug': slug, 'prefix': by_slug[slug][1], 'title': by_slug[slug][2], 'look': by_slug[slug][3], 'world': wi + 1, 'level': li + 1,
               'ink': print_ink(INK[slug])[0], 'onInk': print_ink(INK[slug])[1], 'inline': slug in ('portal', 'mirrors-edge')}
              for wi, (_, slugs) in enumerate(CATEGORIES) for li, slug in enumerate(slugs)]
    data = {'styles': styles, 'worlds': [name for name, _ in CATEGORIES], 'icons': ICONS,
            'groups': [[t, list(g)] for t, g in ICON_GROUPS], 'version': json.load(open(os.path.join(HERE, 'package.json')))['version']}
    os.makedirs(os.path.join(HERE, 'site'), exist_ok=True)
    open(os.path.join(HERE, 'site', 'data.js'), 'w').write('// Generated by gen.py\nexport default ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')


def readme():
    """Fills the generated parts of README.md (between the marker comments)."""
    by_slug = {s[0]: s for s in STYLES}
    tables = []
    for cat, slugs in CATEGORIES:
        rows = [f'| [`{slug}`](docs/{slug}.webp) | `{by_slug[slug][1]}…` | {by_slug[slug][2]} | {by_slug[slug][3]} |' for slug in slugs]
        tables.append(f'### {cat}\n\n| Import path (click: all {len(ICONS)}) | Prefix | Inspired by | Look |\n|---|---|---|---|\n' + '\n'.join(rows))
    icons = '\n'.join(f'- **{t}:** ' + ', '.join(f'`{pascal(n)}`' for n in g) for t, g in ICON_GROUPS)
    path = os.path.join(HERE, 'README.md'); r = open(path).read()
    for key, body in (('styles', '\n\n'.join(tables)), ('icons', icons)):
        a, b = f'<!-- {key}:start -->', f'<!-- {key}:end -->'
        r = r[:r.index(a) + len(a)] + '\n' + body + '\n' + r[r.index(b):]
    r = re.sub(r'\d+ icons in \d+ styles', f'{len(ICONS)} icons in {len(STYLES)} styles', r)
    r = re.sub(r'[\d,]+ components', f'{len(ICONS) * len(STYLES):,} components', r)
    open(path, 'w').write(r)


OVERVIEW_ICONS = ['heart', 'sword', 'potion', 'chest', 'settings', 'gamepad']


def preview():
    by_slug = {s[0]: s for s in STYLES}

    def cell(slug, n, px):
        prefix = by_slug[slug][1]
        if slug in ('portal', 'mirrors-edge'):  # currentColor only works inline, not through <img>
            svg = open(os.path.join(HERE, 'svg', slug, f'{n}.svg')).read().replace('width="24" height="24"', f'width="{px}" height="{px}"')
        else:
            svg = f'<img src="svg/{slug}/{n}.svg" width="{px}" height="{px}" alt="{n}" loading="lazy">'
        return f'<figure title="{prefix}{pascal(n)}">{svg}</figure>'

    tiles = ''.join(f'<a class="tile" href="#{slug}"><span>{by_slug[slug][2]}</span><div>{"".join(cell(slug, n, 30) for n in OVERVIEW_ICONS)}</div></a>'
                    for _, slugs in CATEGORIES for slug in slugs)
    groups = []
    for cat, slugs in CATEGORIES:
        secs = []
        for slug in slugs:
            _, prefix, title, desc, _ = by_slug[slug]
            cells = ''.join(cell(slug, n, 32) for n in ICONS)
            secs.append(f'<section id="{slug}"><h3>{title} <code>{slug}</code></h3><p>{desc}</p><div class="row dark">{cells}</div><div class="row light">{cells}</div></section>')
        groups.append(f'<h2>{cat}</h2>' + ''.join(secs))
    open(os.path.join(HERE, 'preview.html'), 'w').write(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Game Style Icons</title><style>
body{{margin:0;background:#16181c;color:#e9ebee;font:15px/1.5 system-ui,sans-serif}} main{{max-width:1180px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:28px;margin:0 0 4px}} header p{{color:#8d939b;margin:0 0 24px;max-width:72ch}}
h2{{font-size:21px;margin:40px 0 0}} section{{padding:16px 0;border-top:1px solid #262a30}} h3{{font-size:17px;margin:0}} code{{font-size:12px;color:#8d939b;margin-left:6px}} section>p{{color:#8d939b;margin:2px 0 10px;font-size:14px}}
.row{{display:grid;grid-template-columns:repeat(20,minmax(0,1fr));gap:10px 4px;padding:12px 8px;border-radius:10px}}
.dark{{background:#0d0f12}} .light{{background:#f4f4f2;color:#1b1d21;margin-top:6px}}
#overview{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;padding:12px;background:#0d0f12;border-radius:12px;border:0}}
.tile{{display:block;padding:10px 10px 12px;border-radius:8px;background:#16191e;color:inherit;text-decoration:none}} .tile:hover{{background:#1d2128}}
.tile span{{display:block;font-size:12.5px;color:#aab0b8;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tile div{{display:flex;justify-content:space-between}}
figure{{margin:0}} figure svg,figure img{{display:block;margin:0 auto}}
@media (max-width:900px){{#overview{{grid-template-columns:repeat(2,minmax(0,1fr))}}}} @media (max-width:700px){{.row{{grid-template-columns:repeat(10,minmax(0,1fr))}}}}
</style></head><body><main><header><h1>Game Style Icons</h1>
<p>{len(ICONS)} icons in {len(STYLES)} styles inspired by video games, for React, any framework (the &lt;game-icon&gt; web component) or plain SVG, shown on dark and light. Original artwork, no logos or characters; not affiliated with any game or publisher. Click a style to jump to all its icons.</p></header>
<section id="overview">{tiles}</section>
{"".join(groups)}</main></body></html>
''')


if __name__ == '__main__':
    build()
