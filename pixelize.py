"""16x16 pixel items from the vector glyphs, shaded like Minecraft items (pure Python, no dependencies).

The glyph's paths are flattened and rasterised at 8x supersampling: closed parts are filled, open lines are drawn
thick, inner details thin. Then every pixel gets a role: outline around the shape, light edge at the top-left,
shade at the bottom-right, base colour inside, dark inner details. Colours come from a material per icon.
"""
import math, re

S = 8            # supersampling per pixel
N = 16 * S
SCALE = 14 / 18  # glyph area 3..21 (18 units) -> 14 px, leaving 1 px for the outline
NUM = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.\d*|\.\d+|\d+)(?:e-?\d+)?')


def _arc(x1, y1, rx, ry, phi, fa, fs, x2, y2, n=24):
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(phi); cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx *= math.sqrt(lam); ry *= math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0, num / den)) * (-1 if fa == fs else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = cp * cxp - sp * cyp + (x1 + x2) / 2, sp * cxp + cp * cyp + (y1 + y2) / 2
    ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0: dt -= 2 * math.pi
    if fs and dt < 0: dt += 2 * math.pi
    return [(cx + rx * math.cos(t1 + dt * k / n) * cp - ry * math.sin(t1 + dt * k / n) * sp,
             cy + rx * math.cos(t1 + dt * k / n) * sp + ry * math.sin(t1 + dt * k / n) * cp) for k in range(1, n + 1)]


def flatten(d):
    """SVG path data -> list of (points, closed) subpaths."""
    toks = NUM.findall(d); i = 0; cmd = None
    subs, pts = [], []
    x = y = sx = sy = 0.0; lc = None  # last control point for S/T
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.match(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
        rel = cmd.islower(); C = cmd.upper()
        if C == 'Z':
            if pts: subs.append((pts, True)); pts = []
            x, y = sx, sy; lc = None
            continue
        ox, oy = (x, y) if rel else (0, 0)
        if C == 'M':
            if pts: subs.append((pts, False))
            x, y = ox + num(), oy + num(); sx, sy = x, y; pts = [(x, y)]; lc = None
            cmd = 'l' if rel else 'L'
        elif C == 'L':
            x, y = ox + num(), oy + num(); pts.append((x, y)); lc = None
        elif C == 'H':
            x = ox + num() if rel else num(); pts.append((x, y)); lc = None
        elif C == 'V':
            y = oy + num() if rel else num(); pts.append((x, y)); lc = None
        elif C in 'CS':
            if C == 'C':
                c1 = (ox + num(), oy + num())
            else:
                c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            c2 = (ox + num(), oy + num()); e = (ox + num(), oy + num())
            for k in range(1, 17):
                t = k / 16; u = 1 - t
                pts.append((u ** 3 * x + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * e[0],
                            u ** 3 * y + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * e[1]))
            x, y = e; lc = c2
        elif C in 'QT':
            c1 = (ox + num(), oy + num()) if C == 'Q' else ((2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y))
            e = (ox + num(), oy + num())
            for k in range(1, 13):
                t = k / 12; u = 1 - t
                pts.append((u * u * x + 2 * u * t * c1[0] + t * t * e[0], u * u * y + 2 * u * t * c1[1] + t * t * e[1]))
            x, y = e; lc = c1
        elif C == 'A':
            rx, ry, ph, fa, fs = num(), num(), num(), num(), num()
            ex, ey = ox + num(), oy + num()
            pts.extend(_arc(x, y, rx, ry, ph, int(fa), int(fs), ex, ey)); x, y = ex, ey; lc = None
    if pts: subs.append((pts, False))
    return subs


def _to_grid(p):
    return (((p[0] - 3) * SCALE + 1) * S, ((p[1] - 3) * SCALE + 1) * S)


def _fill(grid, poly):
    poly = [_to_grid(p) for p in poly]
    n = len(poly)
    for row in range(N):
        yc = row + .5; xs = []
        for k in range(n):
            (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for col in range(max(0, int(math.ceil(a - .5))), min(N, int(math.floor(b - .5)) + 1)):
                grid[row][col] ^= 1


def _stroke(grid, pts, w):
    r = w * SCALE * S / 2
    g = [_to_grid(p) for p in pts]
    if len(g) == 1: g = g * 2
    for (x1, y1), (x2, y2) in zip(g, g[1:]):
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy or 1e-9
        for row in range(max(0, int(min(y1, y2) - r)), min(N, int(max(y1, y2) + r) + 1)):
            for col in range(max(0, int(min(x1, x2) - r)), min(N, int(max(x1, x2) + r) + 1)):
                px, py = col + .5, row + .5
                t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
                if (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2 <= r * r:
                    grid[row][col] = 1


def _coverage(grid):
    return [[sum(grid[py * S + a][px * S + b] for a in range(S) for b in range(S)) / (S * S) for px in range(16)] for py in range(16)]


def masks(parts):
    body = [[0] * N for _ in range(N)]; detail = [[0] * N for _ in range(N)]
    for d, kind in parts:
        for pts, closed in flatten(d):
            if kind == 1:
                tmp = [[0] * N for _ in range(N)]
                _fill(tmp, pts)
                for r in range(N):
                    for c in range(N):
                        body[r][c] |= tmp[r][c]
            elif kind == 0:
                _stroke(body, pts + ([pts[0]] if closed else []), 2.5)
            else:
                _stroke(detail, pts + ([pts[0]] if closed else []), 1.5)
    b = [[v >= .42 for v in row] for row in _coverage(body)]
    dd = [[v >= .3 for v in row] for row in _coverage(detail)]
    return b, dd


def _mix(h, t, f):
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(t[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * f):02x}' for x, y in zip(a, b))


def item(parts, base):
    """16 rows of palette letters plus the palette, in the format of the hand-drawn PIXELS."""
    B, D = masks(parts)
    inb = lambda x, y: 0 <= x < 16 and 0 <= y < 16 and B[y][x]
    rows = []
    for y in range(16):
        row = ''
        for x in range(16):
            if B[y][x]:
                if D[y][x]: ch = 'k'
                elif not inb(x, y - 1) or not inb(x - 1, y): ch = 'b'
                elif not inb(x, y + 1) or not inb(x + 1, y): ch = 'c'
                else: ch = 'a'
            elif any(inb(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                ch = 'k'
            else:
                ch = '.'
            row += ch
        rows.append(row)
    pal = {'a': base, 'b': _mix(base, '#ffffff', .38), 'c': _mix(base, '#000000', .3), 'k': _mix(base, '#000000', .74)}
    return pal, rows
