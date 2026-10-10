#!/usr/bin/env python3
"""Generates the package: React components in src/, plain SVGs in svg/, and preview.html.

Icons are bare glyphs (no tile, no frame): each style gets its look from the glyph itself (outlines, offset
shadows, glitch copies, glows drawn as soft wide strokes, pixel art). Base glyphs and the Minecraft pixel items
live in glyphs.py. Run: python3 gen.py
"""
import json, os, re, shutil
from glyphs import GLYPHS, PIXELS

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
    pal, rows = PIXELS[name]
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < 16:
            ch = row[x]
            if ch == '.':
                x += 1
                continue
            run = 1
            while x + run < 16 and row[x + run] == ch:
                run += 1
            rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{pal[ch]}"/>')
            x += run
    return f'<g shape-rendering="crispEdges">{"".join(rects)}</g>'


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


# (folder and import path, component prefix, inspired by, look, function)
STYLES = [
    ('cyberpunk', 'Cyberpunk', 'Cyberpunk 2077', 'Neon yellow with a cyan/red glitch split', cyberpunk),
    ('borderlands', 'Borderlands', 'Borderlands', 'Cel-shaded: heavy black ink outline, flat colour, comic drop shadow', borderlands),
    ('gta', 'Gta', 'Grand Theft Auto', 'Radar blip: white glyph, black outline, soft shadow', gta),
    ('minecraft', 'Minecraft', 'Minecraft', '16x16 pixel items', None),
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
]


def pascal(s):
    return ''.join(w.capitalize() for w in re.split(r'[-_ ]', s))


def body(slug, fn, name, i):
    return minecraft(name) if slug == 'minecraft' else fn(GLYPHS[name], i)


def viewbox(slug):
    return '0 0 16 16' if slug == 'minecraft' else VIEWBOX


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


def build():
    for d in ('src', 'svg', 'icons', 'sprites'):
        shutil.rmtree(os.path.join(HERE, d), ignore_errors=True)
    os.makedirs(os.path.join(HERE, 'src'))
    open(os.path.join(HERE, 'src', '_base.js'), 'w').write(BASE_JS)
    open(os.path.join(HERE, 'src', '_base.d.ts'), 'w').write(BASE_DTS)
    index_js, index_dts, manifest = [], [], []
    for slug, prefix, title, desc, fn in STYLES:
        os.makedirs(os.path.join(HERE, 'svg', slug))
        js = ["import { createIcon } from './_base.js';", '']
        dts = ["import type { GameIcon } from './_base.js';", '']
        for i, name in enumerate(ICONS):
            mk = body(slug, fn, name, i)
            comp = prefix + pascal(name)
            js.append(f"export const {comp} = /*#__PURE__*/ createIcon('{comp}', '{viewbox(slug)}', {json.dumps(mk)});")
            dts.append(f'export declare const {comp}: GameIcon;')
            static = mk.replace('__ID__', f'gsi-{slug}-{name}')
            label = name.replace('-', ' ')
            open(os.path.join(HERE, 'svg', slug, f'{name}.svg'), 'w').write(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="{viewbox(slug)}" fill="none" role="img" aria-label="{label}"><title>{label}</title>{static}</svg>\n')
        open(os.path.join(HERE, 'src', f'{slug}.js'), 'w').write('\n'.join(js) + '\n')
        open(os.path.join(HERE, 'src', f'{slug}.d.ts'), 'w').write('\n'.join(dts) + '\n')
        index_js.append(f"export * from './{slug}.js';")
        index_dts.append(f"export * from './{slug}.js';")
        manifest.append({'style': slug, 'prefix': prefix, 'inspiredBy': title, 'look': desc, 'icons': [prefix + pascal(n) for n in ICONS]})
    index_dts.insert(0, "export type { GameIcon, GameIconProps } from './_base.js';")
    open(os.path.join(HERE, 'src', 'index.js'), 'w').write('\n'.join(index_js) + '\n')
    open(os.path.join(HERE, 'src', 'index.d.ts'), 'w').write('\n'.join(index_dts) + '\n')
    open(os.path.join(HERE, 'icons.json'), 'w').write(json.dumps(manifest, indent=1) + '\n')
    preview()
    print(len(STYLES), 'styles x', len(ICONS), 'icons =', len(STYLES) * len(ICONS), 'components')


def preview():
    rows = []
    for slug, prefix, title, desc, _ in STYLES:
        # inline SVG so icons that use currentColor follow each row's text colour
        svgs = {n: open(os.path.join(HERE, 'svg', slug, f'{n}.svg')).read().replace('width="24" height="24"', 'width="40" height="40"') for n in ICONS}
        cells = ''.join(f'<figure>{svgs[n]}<figcaption>{prefix}{pascal(n)}</figcaption></figure>' for n in ICONS)
        rows.append(f'<section><h2>{title} <code>{slug}</code></h2><p>{desc}</p><div class="row dark">{cells}</div><div class="row light">{cells}</div></section>')
    open(os.path.join(HERE, 'preview.html'), 'w').write(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Game Style Icons</title><style>
body{{margin:0;background:#16181c;color:#e9ebee;font:15px/1.5 system-ui,sans-serif}} main{{max-width:1180px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:28px;margin:0 0 4px}} header p{{color:#8d939b;margin:0 0 24px;max-width:72ch}}
section{{padding:16px 0;border-top:1px solid #262a30}} h2{{font-size:17px;margin:0}} code{{font-size:12px;color:#8d939b;margin-left:6px}} section>p{{color:#8d939b;margin:2px 0 10px;font-size:14px}}
.row{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:4px;padding:12px 8px;border-radius:10px}}
.dark{{background:#0d0f12}} .light{{background:#f4f4f2;color:#1b1d21;margin-top:6px}}
figure{{margin:0;text-align:center}} figure svg{{display:block;margin:0 auto}} figcaption{{font-size:9.5px;opacity:.6;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
</style></head><body><main><header><h1>Game Style Icons</h1>
<p>{len(ICONS)} icons in {len(STYLES)} styles inspired by video games, as React components and plain SVGs, shown on dark and light. Original artwork, no logos or characters; not affiliated with any game or publisher.</p></header>
{"".join(rows)}</main></body></html>
''')


if __name__ == '__main__':
    build()
