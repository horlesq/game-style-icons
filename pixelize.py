"""Pixel grids and polylines from the vector glyphs (pure Python, no dependencies).

The glyph's paths are flattened and rasterised at 8x supersampling: closed parts are filled, open lines are drawn
thick, inner details thin. `item` turns that into a 16x16 Minecraft-style item (outline around the shape, light edge
at the top-left, shade at the bottom-right, base colour inside, dark inner details) in a material colour.
`grid` gives the raw body/detail masks at any size for the other pixel styles; `flatten`, `polyline` and `wobble`
serve the vector styles that redraw the outlines (low-poly arcade vectors, hand-inked lines).
"""
import math, re

S = 8            # supersampling per pixel
NUM = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.\d*|\.\d+|\d+)(?:e-?\d+)?')


def _arc(x1, y1, rx, ry, phi, fa, fs, x2, y2, seg):
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
    n = seg(abs(dt)) if callable(seg) else seg
    return [(cx + rx * math.cos(t1 + dt * k / n) * cp - ry * math.sin(t1 + dt * k / n) * sp,
             cy + rx * math.cos(t1 + dt * k / n) * sp + ry * math.sin(t1 + dt * k / n) * cp) for k in range(1, n + 1)]


def flatten(d, curve=16, arc=24):
    """SVG path data -> list of (points, closed) subpaths. `curve`: segments per Bezier; `arc`: segments per arc
    (a number, or a function of the arc's sweep in radians)."""
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
            for k in range(1, curve + 1):
                t = k / curve; u = 1 - t
                pts.append((u ** 3 * x + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * e[0],
                            u ** 3 * y + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * e[1]))
            x, y = e; lc = c2
        elif C in 'QT':
            c1 = (ox + num(), oy + num()) if C == 'Q' else ((2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y))
            e = (ox + num(), oy + num())
            q = max(1, curve * 3 // 4)
            for k in range(1, q + 1):
                t = k / q; u = 1 - t
                pts.append((u * u * x + 2 * u * t * c1[0] + t * t * e[0], u * u * y + 2 * u * t * c1[1] + t * t * e[1]))
            x, y = e; lc = c1
        elif C == 'A':
            rx, ry, ph, fa, fs = num(), num(), num(), num(), num()
            ex, ey = ox + num(), oy + num()
            pts.extend(_arc(x, y, rx, ry, ph, int(fa), int(fs), ex, ey, arc)); x, y = ex, ey; lc = None
    if pts: subs.append((pts, False))
    return subs


def _f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def polyline(d, curve=3, arc=lambda sweep: max(2, round(sweep / (math.pi / 3)))):
    """The path redrawn with straight segments only: coarse curves (low-poly), arcs as hexagon pieces."""
    out = []
    for pts, closed in flatten(d, curve, arc):
        clean = [pts[0]] + [p for a, p in zip(pts, pts[1:]) if abs(p[0] - a[0]) + abs(p[1] - a[1]) > 1e-3]
        out.append('M' + 'L'.join(f'{_f(x)} {_f(y)}' for x, y in clean) + ('Z' if closed else ''))
    return ''.join(out)


def wobble(d, amp=.28, seed=0):
    """The path as a hand-inked line: densely flattened, then nudged by a slow deterministic wave."""
    out = []
    for k, (pts, closed) in enumerate(flatten(d, 10, 12)):
        dense = []
        for a, b in zip(pts, pts[1:] + ([pts[0]] if closed else [])):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / .9))
            dense += [(a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n) for j in range(n)]
        if not closed:
            dense.append(pts[-1])
        s = 0.0; prev = dense[0]; moved = []
        for x, y in dense:
            s += math.hypot(x - prev[0], y - prev[1]); prev = (x, y)
            ph = seed * 1.7 + k * 2.3
            moved.append((x + amp * math.sin(.85 * s + ph) + amp * .5 * math.sin(2.1 * s + ph * 1.3),
                          y + amp * math.cos(.7 * s + ph * .8) + amp * .5 * math.sin(1.9 * s + ph)))
        out.append('M' + 'L'.join(f'{_f(x)} {_f(y)}' for x, y in moved) + ('Z' if closed else ''))
    return ''.join(out)


class _Grid:
    def __init__(self, n, pad):
        self.n, self.N, self.pad = n, n * S, pad
        self.scale = (n - 2 * pad) / 18  # glyph area 3..21 (18 units) -> the grid minus the padding

    def to(self, p):
        return (((p[0] - 3) * self.scale + self.pad) * S, ((p[1] - 3) * self.scale + self.pad) * S)

    def blank(self):
        return [[0] * self.N for _ in range(self.N)]

    def fill(self, grid, poly):
        poly = [self.to(p) for p in poly]; n = len(poly); N = self.N
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

    def stroke(self, grid, pts, w):
        r = w * self.scale * S / 2; N = self.N
        g = [self.to(p) for p in pts]
        if len(g) == 1: g = g * 2
        for (x1, y1), (x2, y2) in zip(g, g[1:]):
            dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy or 1e-9
            for row in range(max(0, int(min(y1, y2) - r)), min(N, int(max(y1, y2) + r) + 1)):
                for col in range(max(0, int(min(x1, x2) - r)), min(N, int(max(x1, x2) + r) + 1)):
                    px, py = col + .5, row + .5
                    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
                    if (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2 <= r * r:
                        grid[row][col] = 1

    def coverage(self, grid):
        n = self.n
        return [[sum(grid[py * S + a][px * S + b] for a in range(S) for b in range(S)) / (S * S) for px in range(n)] for py in range(n)]


def grid(parts, n=16, pad=1, body_at=.42, detail_at=.3):
    """Body and detail masks (n x n booleans). `pad` pixels stay free around the glyph area for an outline."""
    G = _Grid(n, pad)
    body = G.blank(); detail = G.blank()
    for d, kind in parts:
        for pts, closed in flatten(d):
            if kind == 1:
                tmp = G.blank()
                G.fill(tmp, pts)
                for r in range(G.N):
                    for c in range(G.N):
                        body[r][c] |= tmp[r][c]
            elif kind == 0:
                G.stroke(body, pts + ([pts[0]] if closed else []), 2.5)
            else:
                G.stroke(detail, pts + ([pts[0]] if closed else []), 1.5)
    b = [[v >= body_at for v in row] for row in G.coverage(body)]
    dd = [[v >= detail_at for v in row] for row in G.coverage(detail)]
    return b, dd


def masks(parts):
    return grid(parts, 16, 1)


def _mix(h, t, f):
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(t[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * f):02x}' for x, y in zip(a, b))


def shaded(B, D):
    """Rows of roles: k outline or inner detail, b light top-left edge, c shaded bottom-right edge, a inside."""
    n = len(B)
    inb = lambda x, y: 0 <= x < n and 0 <= y < n and B[y][x]
    rows = []
    for y in range(n):
        row = ''
        for x in range(n):
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
    return rows


def item(parts, base):
    """16 rows of palette letters plus the palette, in the format of the hand-drawn PIXELS."""
    pal = {'a': base, 'b': _mix(base, '#ffffff', .38), 'c': _mix(base, '#000000', .3), 'k': _mix(base, '#000000', .74)}
    return pal, shaded(*masks(parts))
