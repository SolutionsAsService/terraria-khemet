"""psprite: a tiny pixel-art painter and the sprite recipes for tModLoader content (items, tiles, projectiles, enemies, bosses).

Everything is drawn from palettes and shapes in code, so a sprite is a recipe in a spec ("sprite": "khopesh", "palette": "gold"), not a file to paint.
Terraria textures are plain PNGs beside the class that uses them; sizes matter: a tile needs the 288 by 270 frame sheet, an enemy needs one
frame per animation step stacked vertically, a boss needs a `_Head_Boss` icon.
"""
import math
from .png import write_png

CLEAR = (0, 0, 0, 0)


def hexc(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def shade(c, d):
    return (max(0, min(255, c[0] + d)), max(0, min(255, c[1] + d)), max(0, min(255, c[2] + d)), c[3])


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(4))


PALETTES = {
    "gold": {"base": "#e0b838", "dark": "#8a6a14", "light": "#fff0a0", "deep": "#4a3408"},
    "lapis": {"base": "#2a58b0", "dark": "#142c68", "light": "#6a98e8", "deep": "#0a1638"},
    "turquoise": {"base": "#2ab0a0", "dark": "#126058", "light": "#7ae8d8", "deep": "#08302c"},
    "sand": {"base": "#d4be84", "dark": "#8e7a48", "light": "#f0e2b0", "deep": "#4a3e20"},
    "basalt": {"base": "#3a3a46", "dark": "#1a1a22", "light": "#6a6a7c", "deep": "#08080c"},
    "linen": {"base": "#d8ceac", "dark": "#a09470", "light": "#f4ecd0", "deep": "#5a5238"},
    "flame": {"base": "#ff7a30", "dark": "#a02808", "light": "#ffd070", "deep": "#481004"},
    "sun": {"base": "#f0b020", "dark": "#a05a08", "light": "#fff4b0", "deep": "#502800"},
    "duat": {"base": "#40c8e8", "dark": "#1a6080", "light": "#c0f4ff", "deep": "#082838"},
    "scarab": {"base": "#1c6a78", "dark": "#0c3a48", "light": "#5ac8c0", "deep": "#041c24"},
    "blood": {"base": "#c02830", "dark": "#701018", "light": "#ff7a70", "deep": "#38080c"},
    "wood": {"base": "#8a6a3a", "dark": "#4a3418", "light": "#b08a52", "deep": "#241808"},
    "skin": {"base": "#c88a4a", "dark": "#8a5a28", "light": "#e8b078", "deep": "#4a2c10"},
    "bone": {"base": "#e6dfc8", "dark": "#a89c80", "light": "#fffaea", "deep": "#58503c"},
}


def pal(name):
    p = PALETTES[name]
    return {k: hexc(v) for k, v in p.items()}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [CLEAR] * (w * h)

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y * self.w + x]
        return CLEAR

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c, r=0):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if r:
                self.disc(x0, y0, r, c)
            else:
                self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.3:
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, fill=True, ring=0.0):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                d = ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2
                if d <= 1.0 and (fill or d >= 1.0 - ring):
                    self.set(x, y, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % len(pts)]
                if (ya <= y + 0.5 < yb) or (yb <= y + 0.5 < ya):
                    xs.append(xa + (y + 0.5 - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1]))):
                    self.set(x, y, c)

    def outline(self, c):
        """A one-pixel outline around everything opaque."""
        src = list(self.px)
        for y in range(self.h):
            for x in range(self.w):
                if src[y * self.w + x][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.w and 0 <= ny < self.h and src[ny * self.w + nx][3] > 0:
                            self.px[y * self.w + x] = c
                            break

    def bevel(self, light, dark):
        """Light on the top-left edge of every shape, shade on the bottom-right: the pixel-art edge Terraria sprites have."""
        src = list(self.px)
        for y in range(self.h):
            for x in range(self.w):
                c = src[y * self.w + x]
                if c[3] == 0:
                    continue
                up = src[(y - 1) * self.w + x][3] if y > 0 else 0
                left = src[y * self.w + x - 1][3] if x > 0 else 0
                down = src[(y + 1) * self.w + x][3] if y < self.h - 1 else 0
                right = src[y * self.w + x + 1][3] if x < self.w - 1 else 0
                if up == 0 or left == 0:
                    self.px[y * self.w + x] = mix(c, light, 0.35)
                elif down == 0 or right == 0:
                    self.px[y * self.w + x] = mix(c, dark, 0.35)

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y * other.w + x]
                if c[3]:
                    self.set(ox + x, oy + y, c)

    def scaled(self, k):
        out = Canvas(self.w * k, self.h * k)
        for y in range(out.h):
            for x in range(out.w):
                out.px[y * out.w + x] = self.px[(y // k) * self.w + x // k]
        return out

    def save(self, path):
        write_png(path, self.w, self.h, self.px)


def sheet(frames):
    """Stack frames vertically (an NPC animation sheet)."""
    out = Canvas(frames[0].w, sum(f.h for f in frames))
    y = 0
    for f in frames:
        out.paste(f, 0, y)
        y += f.h
    return out


# ---------------------------------------------------------------- items
def item_khopesh(p, w=44, h=44):
    c = Canvas(w, h)
    pts = []
    for i in range(0, 25):                      # the blade: a sickle (a quadratic curve from the guard up and over), thick at the belly and fine at the tip
        t = i / 24
        x = (1 - t) ** 2 * 16 + 2 * (1 - t) * t * 3 + t * t * 41
        y = (1 - t) ** 2 * 25 + 2 * (1 - t) * t * -4 + t * t * 9
        pts.append((x, y, 3.4 - 2.6 * t))
    for (x, y, r) in pts:
        c.disc(x, y, r, p["light"] if r > 2.4 else p["base"])
    for (x, y, r) in pts[::2]:
        c.set(x + 1, y + 2, p["dark"])
    c.line(7, 37, 17, 27, p["wood"] if "wood" in p else shade(p["dark"], 10), 1)
    c.rect(14, 24, 20, 28, p["base"])
    c.ellipse(6, 38, 2, 2, p["base"])
    c.outline(p["deep"])
    c.bevel(p["light"], p["dark"])
    return c


def item_staff(p, orb, w=40, h=40):
    c = Canvas(w, h)
    c.line(6, 36, 28, 12, shade(p["dark"], 6), 1)
    c.line(6, 36, 28, 12, p["base"], 0)
    c.ellipse(31, 9, 6, 6, orb["base"])
    c.ellipse(31, 9, 3.5, 3.5, orb["light"])
    c.ellipse(31, 9, 6, 6, p["base"], fill=False, ring=0.4)
    for a in range(0, 360, 45):                  # rays
        c.line(31 + 7 * math.cos(math.radians(a)), 9 + 7 * math.sin(math.radians(a)), 31 + 10 * math.cos(math.radians(a)), 9 + 10 * math.sin(math.radians(a)), orb["light"])
    c.rect(18, 20, 20, 22, p["light"])
    c.outline(p["deep"])
    return c


def item_ankh(p, w=32, h=32):
    c = Canvas(w, h)
    c.ellipse(16, 9, 6, 7, p["base"])
    c.ellipse(16, 9, 3, 4, CLEAR)
    c.rect(14, 15, 18, 29, p["base"])
    c.rect(7, 18, 25, 21, p["base"])
    c.outline(p["deep"])
    c.bevel(p["light"], p["dark"])
    c.set(16, 9, CLEAR)
    return c


def item_charm(p, accent, w=30, h=30):
    c = Canvas(w, h)
    c.ellipse(15, 17, 8, 10, p["base"])                         # the shell
    c.rect(14, 8, 15, 26, p["dark"])                            # the wing-case seam
    c.ellipse(15, 8, 4, 3, p["dark"])                           # the head
    for dy in (14, 18, 22):                                     # legs
        c.line(7, dy, 3, dy + 3, p["deep"])
        c.line(23, dy, 27, dy + 3, p["deep"])
    c.ellipse(15, 17, 8, 10, accent["base"], fill=False, ring=0.25)
    c.set(12, 13, accent["light"]); c.set(18, 13, accent["light"])
    c.outline(p["deep"])
    c.bevel(p["light"], p["dark"])
    return c


def item_shard(p, w=22, h=26):
    c = Canvas(w, h)
    c.poly([(11, 1), (19, 9), (16, 24), (6, 24), (3, 9)], p["base"])
    c.poly([(11, 1), (19, 9), (11, 12)], p["light"])
    c.poly([(11, 12), (19, 9), (16, 24)], p["dark"])
    c.outline(p["deep"])
    return c


def item_cartouche(p, accent, w=30, h=36):
    c = Canvas(w, h)
    c.ellipse(15, 18, 10, 15, p["base"])
    c.ellipse(15, 18, 7, 12, p["dark"])
    for y in range(8, 30, 5):
        c.rect(11, y, 19, y + 1, accent["base"])
        c.rect(13, y + 2, 17, y + 2, accent["light"])
    c.rect(5, 32, 25, 34, p["base"])
    c.outline(p["deep"])
    c.bevel(p["light"], p["dark"])
    return c


def item_bag(p, accent, w=30, h=32):
    c = Canvas(w, h)
    c.ellipse(15, 21, 11, 9, p["base"])
    c.poly([(9, 14), (21, 14), (19, 6), (11, 6)], p["base"])
    c.rect(9, 12, 21, 14, accent["base"])
    c.ellipse(15, 6, 5, 2, accent["light"])
    c.ellipse(15, 22, 4, 4, accent["base"])
    c.outline(p["deep"])
    c.bevel(p["light"], p["dark"])
    return c


def item_tile(tile_canvas):
    return tile_canvas


# ---------------------------------------------------------------- tiles
def tile16(pattern, p, accent=None):
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, p["base"])
    if pattern in ("brick", "golden", "hieroglyph"):
        for row in range(4):
            y = row * 4
            c.rect(0, y, 15, y, p["light"])
            c.rect(0, y + 3, 15, y + 3, p["dark"])
            off = 0 if row % 2 == 0 else 8
            for x in range(off, 16, 16):
                c.rect(x, y, x, y + 3, p["dark"])
            if off:
                c.rect(0, y, 0, y + 3, p["dark"])
        for i in range(0, 16, 3):                      # grain
            c.set((i * 5 + 3) % 16, (i * 3 + 1) % 16, shade(p["base"], -10))
    if pattern == "golden":
        c.rect(0, 0, 15, 0, p["light"]); c.rect(0, 15, 15, 15, p["dark"])
    if pattern == "hieroglyph" and accent:
        for (x, y, w, h) in ((2, 1, 2, 2), (6, 5, 1, 2), (10, 1, 3, 1), (3, 9, 2, 2), (9, 9, 1, 3), (12, 12, 2, 1)):
            c.rect(x, y, x + w - 1, y + h - 1, accent["base"])
    if pattern == "lapis":
        for y in range(16):
            for x in range(16):
                if (x // 4 + y // 4) % 2 == 0:
                    c.set(x, y, p["dark"])
        for k in range(0, 16, 4):
            c.rect(k, 0, k, 15, p["light"]); c.rect(0, k, 15, k, p["light"])
        for (x, y) in ((2, 2), (10, 6), (6, 12), (13, 13)):
            if accent:
                c.set(x, y, accent["base"])
    return c


def tile_sheet(tile):
    """The 288 by 270 frame sheet tModLoader expects for a block (18-pixel cells, 16 by 15 of them): every cell is the same seamless tile."""
    out = Canvas(288, 270)
    for cy in range(15):
        for cx in range(16):
            out.paste(tile, cx * 18, cy * 18)
    return out


# ---------------------------------------------------------------- projectiles
def projectile_orb(p, w=18, h=18):
    c = Canvas(w, h)
    c.ellipse(w / 2, h / 2, w / 2 - 1, h / 2 - 1, mix(p["base"], CLEAR, 0.0))
    c.ellipse(w / 2, h / 2, w / 2 - 4, h / 2 - 4, p["light"])
    c.ellipse(w / 2, h / 2, w / 2 - 6.5, h / 2 - 6.5, (255, 255, 255, 255))
    c.ellipse(w / 2, h / 2, w / 2 - 1, h / 2 - 1, p["dark"], fill=False, ring=0.2)
    return c


def projectile_ray(p, w=14, h=34):
    c = Canvas(w, h)
    c.poly([(7, 0), (13, 20), (10, 33), (4, 33), (1, 20)], p["base"])
    c.poly([(7, 4), (10, 20), (7, 30), (4, 20)], p["light"])
    c.line(7, 8, 7, 28, (255, 255, 255, 255))
    return c


# ---------------------------------------------------------------- creatures
def enemy_cobra(frame, w=34, h=48):
    p, hood, belly = pal("sand"), pal("gold"), pal("bone")
    c = Canvas(w, h)
    sway = [0, 1, -1][frame % 3]
    for i in range(0, 38):                                    # the body: an S of overlapping discs from the coil up to the neck
        t = i / 37
        x = 17 + 5 * math.sin(t * 7 + frame * 0.9) * (1 - t * 0.5) + sway * t
        y = 47 - i
        c.disc(x, y, 4.2 - 1.5 * t if t < 0.8 else 3.2, p["base"] if i % 4 else p["dark"])
    hx, hy = 17 + sway, 12
    c.ellipse(hx, hy + 4, 9, 8, hood["base"])                 # the hood
    c.ellipse(hx, hy + 4, 9, 8, hood["dark"], fill=False, ring=0.2)
    c.ellipse(hx - 3, hy + 3, 1.6, 2, hood["deep"]); c.ellipse(hx + 3, hy + 3, 1.6, 2, hood["deep"])
    c.ellipse(hx, hy - 3, 5, 4, p["base"])                     # the head
    c.rect(hx - 3, hy - 4, hx - 2, hy - 3, pal("blood")["base"]); c.rect(hx + 2, hy - 4, hx + 3, hy - 3, pal("blood")["base"])
    c.rect(hx - 1, hy - 1, hx - 1, hy + 2, (255, 255, 240, 255)); c.rect(hx + 1, hy - 1, hx + 1, hy + 2, (255, 255, 240, 255))
    c.outline(p["deep"])
    return c


def enemy_guardian(frame, w=40, h=56):
    st, gold, bas = pal("sand"), pal("gold"), pal("basalt")
    c = Canvas(w, h)
    bob = [0, -1, 0][frame % 3]
    step = [0, 2, -2][frame % 3]
    c.rect(13, 34 + bob, 18 + step, 54, st["dark"]); c.rect(21 - step, 34 + bob, 27, 54, st["base"])         # legs
    c.rect(11 + step, 52, 19 + step, 55, gold["dark"]); c.rect(21 - step, 52, 29 - step, 55, gold["dark"])
    c.rect(10, 16 + bob, 30, 36 + bob, st["base"])                                                         # torso
    c.rect(8, 30 + bob, 32, 38 + bob, gold["base"]); c.rect(8, 30 + bob, 32, 31 + bob, gold["light"])      # kilt
    c.rect(7, 18 + bob, 11, 36 + bob, st["dark"]); c.rect(29, 18 + bob, 33, 36 + bob, st["dark"])          # arms
    c.rect(6, 34 + bob, 12, 38 + bob, bas["base"]); c.rect(28, 34 + bob, 34, 38 + bob, bas["base"])
    c.rect(18, 20 + bob, 21, 28 + bob, gold["base"]); c.rect(15, 23 + bob, 24, 24 + bob, gold["base"])      # an ankh on the chest
    c.rect(12, 14 + bob, 28, 18 + bob, gold["base"])                                                       # collar
    c.ellipse(20, 8 + bob, 7, 7, bas["base"])                                                              # the jackal head
    c.poly([(26, 7 + bob), (38, 10 + bob), (38, 13 + bob), (26, 13 + bob)], bas["base"])
    c.poly([(14, 3 + bob), (15, -2 + bob), (18, 3 + bob)], bas["base"]); c.poly([(22, 3 + bob), (24, -2 + bob), (26, 3 + bob)], bas["base"])
    c.rect(22, 6 + bob, 24, 7 + bob, pal("duat")["light"])
    c.outline(bas["deep"])
    return c


def enemy_scarab(frame, w=30, h=24):
    sc, gold = pal("scarab"), pal("gold")
    c = Canvas(w, h)
    flap = [0, 3, 5, 3][frame % 4]
    c.poly([(15, 12), (3, 6 - flap), (1, 12 - flap), (13, 15)], (*sc["light"][:3], 190)); c.poly([(15, 12), (27, 6 - flap), (29, 12 - flap), (17, 15)], (*sc["light"][:3], 190))
    c.ellipse(15, 15, 7, 6, sc["base"])
    c.rect(15, 10, 15, 20, gold["base"])
    c.ellipse(15, 9, 4, 3, sc["dark"])
    c.rect(12, 8, 12, 8, pal("blood")["base"]); c.rect(18, 8, 18, 8, pal("blood")["base"])
    for dy in (14, 17, 20):
        c.line(8, dy, 4, dy + 2, sc["deep"]); c.line(22, dy, 26, dy + 2, sc["deep"])
    c.outline(sc["deep"])
    return c


def boss_pharaoh(frame, kind, w, h):
    """A floating pharaoh: a bust over a wisp of linen, a mask face, a crown and a broad collar, with wings or a halo by kind. frame 0..3 bobs and beats."""
    kinds = {
        "forgotten": dict(skin="gold", cloth="linen", trim="lapis", crown="white_red", glow="sun", wings=True),
        "anubis": dict(skin="basalt", cloth="linen", trim="gold", crown="jackal", glow="duat", wings=False),
        "sun": dict(skin="skin", cloth="sun", trim="flame", crown="halo", glow="sun", wings=True),
    }
    k = kinds[kind]
    skin, cloth, trim, glow = pal(k["skin"]), pal(k["cloth"]), pal(k["trim"]), pal(k["glow"])
    gold = pal("gold")
    c = Canvas(w, h)
    cx = w // 2
    bob = [0, 2, 3, 1][frame % 4]
    flap = [0, 6, 10, 6][frame % 4]
    top = int(h * 0.14) + bob
    # wings or aura behind
    if k["wings"]:
        for side in (-1, 1):
            for i in range(7):
                ang = math.radians(200 - i * 14 - flap * 1.5) if side == 1 else math.radians(-20 + i * 14 + flap * 1.5)
                length = w * (0.46 - 0.035 * i)
                c.line(cx + side * 8, top + h * 0.35, cx + side * 8 + math.cos(ang) * length * (1 if side == 1 else -1) * (-1 if side == 1 else 1), top + h * 0.35 - math.sin(ang) * length * 0.55, trim["base"] if i % 2 else gold["base"], 2)
    # the linen wisp: a tapering shroud under the bust
    for yy in range(int(top + h * 0.38), h - 2):
        t = (yy - (top + h * 0.38)) / (h - 2 - (top + h * 0.38))
        half = (w * 0.2) * (1 - t * 0.85) + 2 * math.sin(yy * 0.5 + frame)
        c.rect(cx - half, yy, cx + half, yy, cloth["base"] if (yy // 3) % 2 else cloth["dark"])
    # the torso and collar
    c.ellipse(cx, top + h * 0.40, w * 0.22, h * 0.14, cloth["base"])
    c.ellipse(cx, top + h * 0.33, w * 0.26, h * 0.10, gold["base"])
    c.ellipse(cx, top + h * 0.33, w * 0.20, h * 0.07, trim["base"])
    c.ellipse(cx, top + h * 0.33, w * 0.14, h * 0.045, gold["light"])
    # arms crossed holding a crook and flail
    c.line(cx - w * 0.22, top + h * 0.46, cx + w * 0.10, top + h * 0.40, cloth["dark"], 2)
    c.line(cx + w * 0.22, top + h * 0.46, cx - w * 0.10, top + h * 0.40, cloth["dark"], 2)
    c.line(cx - w * 0.24, top + h * 0.20, cx - w * 0.20, top + h * 0.58, gold["base"], 1)
    c.line(cx + w * 0.24, top + h * 0.20, cx + w * 0.20, top + h * 0.58, gold["base"], 1)
    # the head
    hr = w * 0.15
    c.ellipse(cx, top + h * 0.17, hr, hr * 1.15, skin["base"])
    c.rect(cx - hr * 0.6, top + h * 0.15, cx - hr * 0.2, top + h * 0.15 + 1, glow["light"]); c.rect(cx + hr * 0.2, top + h * 0.15, cx + hr * 0.6, top + h * 0.15 + 1, glow["light"])
    c.rect(cx - hr * 0.7, top + h * 0.15 - 2, cx - hr * 0.1, top + h * 0.15 - 2, trim["base"]); c.rect(cx + hr * 0.1, top + h * 0.15 - 2, cx + hr * 0.7, top + h * 0.15 - 2, trim["base"])
    c.rect(cx - 1, top + h * 0.19, cx, top + h * 0.22, skin["dark"])
    c.rect(cx - hr * 0.4, top + h * 0.25, cx + hr * 0.4, top + h * 0.25, skin["dark"])
    c.rect(cx - 1, top + h * 0.27, cx, top + h * 0.34, trim["base"])                                       # the false beard
    # the crown
    if k["crown"] == "white_red":
        c.rect(cx - hr * 1.1, top + h * 0.05, cx + hr * 1.1, top + h * 0.08, trim["base"])                  # nemes band
        c.poly([(cx - hr * 1.1, top + h * 0.08), (cx - hr * 1.5, top + h * 0.30), (cx - hr * 0.8, top + h * 0.26)], trim["base"])
        c.poly([(cx + hr * 1.1, top + h * 0.08), (cx + hr * 1.5, top + h * 0.30), (cx + hr * 0.8, top + h * 0.26)], trim["base"])
        c.ellipse(cx, top + h * 0.03, hr * 0.9, h * 0.04, pal("blood")["base"])
        c.poly([(cx - hr * 0.45, top + h * 0.03), (cx + hr * 0.45, top + h * 0.03), (cx + hr * 0.3, top - h * 0.12), (cx - hr * 0.3, top - h * 0.12)], (240, 236, 224, 255))
    elif k["crown"] == "jackal":
        c.poly([(cx - hr * 0.9, top + h * 0.07), (cx - hr * 0.7, top - h * 0.12), (cx - hr * 0.35, top + h * 0.06)], skin["base"])
        c.poly([(cx + hr * 0.9, top + h * 0.07), (cx + hr * 0.7, top - h * 0.12), (cx + hr * 0.35, top + h * 0.06)], skin["base"])
        c.poly([(cx, top + h * 0.16), (cx + hr * 1.6, top + h * 0.20), (cx + hr * 1.6, top + h * 0.25), (cx, top + h * 0.25)], skin["base"])   # the snout, in profile
        c.rect(cx + hr * 0.2, top + h * 0.15, cx + hr * 0.4, top + h * 0.16, glow["light"])
    elif k["crown"] == "halo":
        c.ellipse(cx, top + h * 0.12, w * 0.34, w * 0.34, gold["base"], fill=False, ring=0.14)
        for a in range(0, 360, 30):
            r0, r1 = w * 0.36, w * 0.46
            c.line(cx + r0 * math.cos(math.radians(a + frame * 4)), top + h * 0.12 + r0 * math.sin(math.radians(a + frame * 4)), cx + r1 * math.cos(math.radians(a + frame * 4)), top + h * 0.12 + r1 * math.sin(math.radians(a + frame * 4)), glow["light"], 1)
        c.rect(cx - hr * 1.0, top + h * 0.05, cx + hr * 1.0, top + h * 0.08, gold["base"])
    c.outline(pal("basalt")["deep"])
    return c


def boss_head_icon(kind, size=24):
    c = boss_pharaoh(0, kind, 48, 52)
    out = Canvas(size, size)
    for y in range(size):
        for x in range(size):
            out.px[y * size + x] = c.px[int(y * 0.75) * c.w + int(x * 2 * 0.95)] if int(y * 0.75) < c.h and int(x * 2 * 0.95) < c.w else CLEAR
    return out
