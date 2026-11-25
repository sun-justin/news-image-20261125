#!/usr/bin/env python3
"""THE WORLD TODAY - Wednesday 25 November 2026.

A pure-stdlib Python program that draws a dense newspaper front page
summing up the world news of Wednesday 25 November 2026 as a 1024x1024
PNG. Everything is drawn from scratch in this file: a hand-built 5x7
bitmap font (with a bold pass), gradient skies, shaded illustrations
(two oil tankers burning in the Strait of Hormuz, a Shenzhou-24
rocket climbing to Tiangong, a Brooklyn courthouse at dusk), a world
map, a stats strip, a markets strip, paper grain, and 37 dated
stories across 9 regions.

No network, no clock, no randomness: two runs write byte-identical
output. Run with:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
The image is written to <MAKEFUN_OUTPUT_DIR>/entry.png.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 242, 230)
PAPER2 = (236, 229, 212)
INK = (23, 20, 16)
INK_SOFT = (64, 58, 49)
RED = (169, 30, 25)
DARKRED = (118, 20, 17)
BLUE = (25, 52, 102)
STEEL = (56, 82, 118)
GOLD = (170, 126, 46)
GREEN = (27, 94, 52)
GREY = (128, 122, 110)
RULE = (96, 88, 74)
SEA = (164, 184, 194)
LAND = (198, 184, 150)
NIGHT = (17, 27, 51)
SKY = (232, 214, 176)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return self.px[i], self.px[i + 1], self.px[i + 2]

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def vgrad(self, x, y, w, h, top, bot):
        for j in range(h):
            t = j / max(1, h - 1)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.rect(x, y + j, w, 1, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = t // 2
        for s in range(steps + 1):
            px = x0 + dx * s // steps
            py = y0 + dy * s // steps
            for a in range(-r, r + 1):
                for b in range(-r, r + 1):
                    self.set(px + a, py + b, c)

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d <= r * r:
                    self.set(xx, yy, c)
                elif not fill and abs(d - r * r) <= r * 2:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs_at = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs_at.append(x0 + (x1 - x0) * t)
            xs_at.sort()
            for k in range(0, len(xs_at) - 1, 2):
                for xx in range(int(xs_at[k]), int(xs_at[k + 1]) + 1):
                    self.set(xx, yy, c)

    def blend_rect(self, x, y, w, h, c, a):
        """Blend colour c over the rectangle with alpha a (0..1)."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                for k in range(3):
                    self.px[i + k] = int(self.px[i + k] * (1 - a) + c[k] * a)
                i += 3


def grain(c, seed=1234567):
    """Deterministic paper grain over the whole canvas (LCG)."""
    s = seed
    for i in range(0, len(c.px), 3):
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        n = (s >> 16) % 13 - 6
        for k in range(3):
            v = c.px[i + k] + n
            c.px[i + k] = 0 if v < 0 else (255 if v > 255 else v)


def write_png(c, path):
    raw = bytearray()
    stride = c.w * 3
    for y in range(c.h):
        raw.append(0)
        raw += c.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = on.
FONT = {
"A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
"C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
"D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
"E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
"F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
"G": (".####", "#....", "#....", "#..##", "#...#", "#...#", ".###."),
"H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
"J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
"K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
"L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
"M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
"N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
"O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
"Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
"R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
"S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
"T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
"U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
"W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
"X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
"Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
"Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
"0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
"1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
"2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
"3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
"4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
"5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
"6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
"7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
"8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
"9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
" ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
"!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
"?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
"'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
'"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
"-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
"(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
"/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
"%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
"$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
"&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
"+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
"=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
"X2": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
"_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
"<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
"[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
"]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}
# Em dash renders as a wide bar; map the unicode dashes to it.
FONT["\u2014"] = (".....", ".....", "#####", "#####", ".....", ".....", ".....")
FONT["\u2013"] = (".....", ".....", ".....", "#####", ".....", ".....", ".....")
FONT["\u2019"] = FONT["'"]
FONT["\u00b7"] = FONT["."]


def _norm(s):
    return (s.replace("\u201c", '"').replace("\u201d", '"')
             .replace("\u00e9", "e").replace("\u00e8", "e")
             .replace("\u00e0", "a").replace("\u00fc", "u")
             .replace("\u00f6", "o").replace("\u00e1", "a")
             .replace("\u00ed", "i").replace("\u00f3", "o")
             .replace("\u00f1", "n").replace("\u00e7", "c")
             .replace("\u00d7", "x").replace("\u20ac", "E")
             .replace("\u00a3", "L").replace("\u20b9", "Rs"))


def text_w(s, scale=1):
    return len(_norm(s).upper()) * 6 * scale


def draw_text(c, x, y, s, scale=1, color=INK, bold=False):
    s = _norm(s).upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if g[row][col] == "#":
                    for dx in range(scale):
                        for dy in range(scale):
                            c.set(cx + col * scale + dx, y + row * scale + dy, color)
                            if bold:
                                c.set(cx + col * scale + dx + 1,
                                      y + row * scale + dy, color)
        cx += 6 * scale
    return cx


def wrap(s, width_chars):
    """Greedy word wrap; returns list of lines, each <= width_chars."""
    words = _norm(s).upper().split()
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(c, x, y, s, width_chars, scale=1, color=INK, leading=None,
              bold=False, max_lines=None):
    lines = wrap(s, width_chars)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading if leading is not None else 7 * scale + 3
    for i, ln in enumerate(lines):
        draw_text(c, x, y + i * lh, ln, scale, color, bold)
    return y + len(lines) * lh

# ---------------------------------------------------------------- art panels
def art_hormuz(c, x, y, w, h):
    """Two tankers burning in the Strait of Hormuz at dusk."""
    c.vgrad(x, y, w, h, (238, 150, 74), (122, 52, 38))
    c.circle(x + int(w * 0.72), y + 26, 15, (250, 226, 150))
    c.circle(x + int(w * 0.72), y + 26, 10, (255, 240, 190))
    # sea
    c.vgrad(x, y + h - 52, w, 52, (44, 62, 84), (20, 30, 52))
    for i in range(6):
        c.hline(x + 8 + i * 47, y + h - 46 + (i % 3) * 12,
                30, (120, 140, 160))
    # tanker 1 (left, listing)
    tx, ty = x + 18, y + h - 74
    c.poly([(tx, ty), (tx + 128, ty), (tx + 122, ty + 22),
            (tx + 6, ty + 22)], (28, 26, 24))
    c.rect(tx + 96, ty - 16, 16, 16, (52, 48, 44))
    c.rect(tx + 100, ty - 26, 8, 10, (52, 48, 44))
    # tanker 2 (right)
    tx2, ty2 = x + w - 150, y + h - 66
    c.poly([(tx2, ty2), (tx2 + 122, ty2), (tx2 + 116, ty2 + 20),
            (tx2 + 6, ty2 + 20)], (36, 33, 30))
    c.rect(tx2 + 20, ty2 - 14, 14, 14, (58, 54, 50))
    # flames on both decks
    for fx, fy, fr in [(tx + 40, ty - 8, 12), (tx + 62, ty - 14, 16),
                       (tx + 84, ty - 6, 10), (tx2 + 60, ty2 - 8, 13),
                       (tx2 + 84, ty2 - 14, 15), (tx2 + 104, ty2 - 6, 9)]:
        c.circle(fx, fy, fr, (226, 110, 30))
        c.circle(fx, fy + 3, fr - 5, (250, 190, 60))
        c.circle(fx, fy + 5, fr - 9, (255, 236, 140))
    # smoke columns
    for sx, sy, sr in [(tx + 52, ty - 34, 12), (tx + 70, ty - 52, 15),
                       (tx + 56, ty - 68, 17), (tx2 + 74, ty2 - 36, 12),
                       (tx2 + 90, ty2 - 54, 14)]:
        c.circle(sx, sy, sr, (74, 66, 60))
        c.circle(sx + 4, sy - 4, sr - 4, (96, 88, 80))
    # naval mine in foreground water
    mx, my = x + w // 2, y + h - 14
    c.circle(mx, my, 7, (16, 16, 16))
    for ang in range(0, 360, 45):
        import math
        dx = int(10 * math.cos(math.radians(ang)))
        dy = int(10 * math.sin(math.radians(ang)))
        c.line(mx, my, mx + dx, my + dy, (16, 16, 16), 2)


def art_shenzhou(c, x, y, w, h):
    """Shenzhou-24 climbing to Tiangong against a night sky."""
    c.vgrad(x, y, w, h, (10, 16, 38), (30, 48, 92))
    # stars (fixed pattern)
    for sx, sy in [(14, 12), (52, 30), (96, 10), (150, 22), (210, 8),
                   (262, 34), (300, 14), (36, 58), (120, 48), (180, 60),
                   (240, 52), (288, 66), (70, 84), (160, 78), (230, 92)]:
        c.set(x + sx, y + sy, (255, 255, 255))
        c.set(x + sx + 1, y + sy, (220, 220, 220))
    # Earth curve at bottom
    c.poly([(x, y + h), (x + w, y + h), (x + w, y + h - 26),
            (x + int(w * 0.7), y + h - 44), (x + int(w * 0.3), y + h - 44),
            (x, y + h - 26)], (52, 110, 168))
    c.poly([(x, y + h), (x + w, y + h), (x + w, y + h - 26),
            (x + int(w * 0.7), y + h - 44), (x + int(w * 0.3), y + h - 44),
            (x, y + h - 26)], (52, 110, 168))
    c.hline(x, y + h - 27, w, (140, 190, 230))
    # Tiangong station (upper right)
    sx, sy = x + w - 96, y + 30
    c.rect(sx, sy, 56, 12, (190, 196, 204))
    c.rect(sx - 26, sy + 2, 26, 8, (120, 150, 200))
    c.rect(sx + 56, sy + 2, 26, 8, (120, 150, 200))
    c.rect(sx + 22, sy - 8, 12, 8, (220, 224, 230))
    c.rect(sx + 8, sy + 12, 40, 4, (150, 156, 164))
    # rocket (centre, climbing)
    rx = x + w // 2 - 52
    ry = y + 62
    c.poly([(rx + 8, ry), (rx + 22, ry), (rx + 22, ry + 62),
            (rx + 8, ry + 62)], (232, 234, 238))
    c.poly([(rx + 8, ry), (rx + 22, ry), (rx + 15, ry - 16)], (196, 40, 34))
    c.rect(rx + 8, ry + 26, 14, 10, (196, 40, 34))
    c.poly([(rx + 2, ry + 62), (rx + 8, ry + 48), (rx + 8, ry + 62)],
           (170, 40, 36))
    c.poly([(rx + 28, ry + 62), (rx + 22, ry + 48), (rx + 22, ry + 62)],
           (170, 40, 36))
    c.circle(rx + 15, ry + 12, 4, (30, 60, 110))
    # flame + exhaust plume
    c.poly([(rx + 9, ry + 62), (rx + 21, ry + 62), (rx + 15, ry + 96)],
           (250, 170, 40))
    c.poly([(rx + 12, ry + 62), (rx + 18, ry + 62), (rx + 15, ry + 84)],
           (255, 236, 140))
    for i, (px, py, pr) in enumerate([(rx - 8, ry + 78, 9), (rx + 38, ry + 84, 11),
                                      (rx + 2, ry + 96, 12), (rx + 30, ry + 98, 10)]):
        c.circle(px, py, pr, (214, 214, 214) if i % 2 else (232, 232, 232))
    # launch tower silhouette (left)
    c.rect(x + 14, y + 96, 6, h - 96 - 44, (24, 26, 34))
    c.rect(x + 26, y + 108, 6, h - 108 - 44, (24, 26, 34))
    c.line(x + 14, y + 96, x + 32, y + 108, (24, 26, 34), 2)


def art_huawei(c, x, y, w, h):
    """A Brooklyn federal courthouse at dusk, scales of justice."""
    c.vgrad(x, y, w, h, (214, 170, 120), (96, 84, 110))
    c.circle(x + 40, y + 24, 13, (250, 226, 160))
    # skyline behind
    for bx, bw, bh in [(0, 34, 44), (40, 26, 58), (72, 30, 38),
                       (w - 104, 30, 52), (w - 68, 26, 40), (w - 36, 36, 62)]:
        c.rect(x + bx, y + h - 62 - bh, bw, bh + 62, (74, 66, 84))
    # courthouse
    bx, by = x + 78, y + 58
    bw, bh = w - 156, h - 58 - 18
    c.rect(bx, by, bw, bh, (196, 182, 158))
    c.poly([(bx - 8, by), (bx + bw + 8, by), (bx + bw // 2, by - 26)],
           (150, 132, 108))
    c.rect(bx, by, bw, 6, (120, 104, 82))
    for i in range(5):
        cx = bx + 14 + i * ((bw - 28) // 4)
        c.rect(cx, by + 10, 10, bh - 26, (224, 212, 186))
        c.rect(cx - 2, by + 8, 14, 4, (224, 212, 186))
        c.rect(cx - 2, by + bh - 18, 14, 4, (224, 212, 186))
    # door + steps
    c.rect(bx + bw // 2 - 16, by + bh - 30, 32, 30, (52, 44, 38))
    c.rect(bx - 10, by + bh, bw + 20, 5, (168, 154, 130))
    c.rect(bx - 18, by + bh + 5, bw + 36, 5, (150, 136, 112))
    # scales of justice (right foreground)
    sx, sy = x + w - 52, y + h - 62
    c.vline(sx, sy - 26, 26, (40, 34, 28))
    c.hline(sx - 18, sy - 26, 36, (40, 34, 28))
    c.circle(sx, sy - 30, 3, (40, 34, 28))
    c.line(sx - 18, sy - 26, sx - 24, sy - 8, (40, 34, 28), 1)
    c.line(sx + 18, sy - 26, sx + 24, sy - 8, (40, 34, 28), 1)
    c.poly([(sx - 30, sy - 8), (sx - 18, sy - 8), (sx - 24, sy - 2)],
           (180, 150, 60))
    c.poly([(sx + 18, sy - 8), (sx + 30, sy - 8), (sx + 24, sy - 2)],
           (180, 150, 60))
    c.rect(sx - 3, sy, 6, 4, (40, 34, 28))


# ---------------------------------------------------------------- world map
# Land spans as (row, col_start, col_end) on an 80x24 grid
# (lon -180..180, lat 80..-55).
LAND_SPANS = [
    (0, 12, 18), (0, 25, 27), (0, 40, 58),
    (1, 3, 7), (1, 10, 20), (1, 24, 27), (1, 36, 37), (1, 40, 60),
    (2, 2, 6), (2, 9, 21), (2, 32, 32), (2, 35, 38), (2, 39, 62),
    (3, 8, 22), (3, 33, 33), (3, 36, 39), (3, 39, 63),
    (4, 7, 23), (4, 33, 42), (4, 43, 64),
    (5, 6, 24), (5, 33, 44), (5, 45, 63),
    (6, 6, 25), (6, 34, 43), (6, 46, 62), (6, 66, 67),
    (7, 7, 25), (7, 35, 44), (7, 45, 49), (7, 55, 62), (7, 67, 67),
    (8, 8, 24), (8, 34, 44), (8, 46, 50), (8, 53, 55), (8, 56, 62),
    (9, 8, 13), (9, 34, 45), (9, 46, 50), (9, 53, 55), (9, 58, 61),
    (10, 9, 14), (10, 34, 46), (10, 54, 55), (10, 58, 62),
    (11, 10, 14), (11, 35, 47), (11, 59, 62),
    (12, 12, 17), (12, 35, 48), (12, 59, 64),
    (13, 12, 18), (13, 35, 48), (13, 60, 65),
    (14, 12, 19), (14, 36, 48), (14, 61, 66),
    (15, 12, 19), (15, 37, 48),
    (16, 12, 19), (16, 37, 47), (16, 60, 65),
    (17, 12, 18), (17, 37, 47), (17, 59, 66),
    (18, 12, 18), (18, 38, 46), (18, 59, 66),
    (19, 12, 17), (19, 38, 45), (19, 60, 65),
    (20, 12, 16), (20, 38, 44), (20, 60, 64), (20, 68, 69),
    (21, 12, 15), (21, 61, 63), (21, 68, 68),
    (22, 12, 14), (22, 68, 68),
    (23, 12, 13),
]
# (label, lon, lat, dx, dy) — dx/dy shift the label from its dot.
MAP_LABELS = [
    ("HORMUZ", 56.0, 26.5, 6, -12),
    ("GAZA", 34.5, 31.5, -30, 8),
    ("RIYADH", 46.7, 24.6, 6, 8),
    ("BENGHAZI", 20.0, 32.0, -52, -12),
    ("KYIV", 30.5, 50.4, 6, 8),
    ("WARSAW", 21.0, 52.2, -40, -14),
    ("ANTALYA", 30.7, 36.9, -8, -24),
    ("JIUQUAN", 98.5, 39.8, 6, -12),
    ("SEOUL", 127.0, 37.5, 6, 6),
    ("TOKYO", 139.7, 35.7, 6, -12),
    ("CARTAGENA", -75.5, 10.4, -72, 4),
    ("CANBERRA", 149.1, -35.3, -58, 8),
    ("HONIARA", 160.0, -9.4, 6, -12),
    ("NAIROBI", 36.8, -1.3, 6, 6),
]


def draw_map(c, x, y, w, h):
    c.rect(x, y, w, h, SEA)
    cw, ch = w / 80.0, h / 24.0
    for (r, c0, c1) in LAND_SPANS:
        for cc in range(c0, c1 + 1):
            c.rect(int(x + cc * cw), int(y + r * ch),
                   int(cw) + 1, int(ch) + 1, LAND)
    # graticule
    for gx in range(1, 8):
        c.vline(x + gx * w // 8, y, h, (140, 160, 170))
    for gy in range(1, 4):
        c.hline(x, y + gy * h // 4, w, (140, 160, 170))
    for (label, lon, lat, dx, dy) in MAP_LABELS:
        px = int(x + (lon + 180) / 360.0 * w)
        py = int(y + (80 - lat) / 135.0 * h)
        c.circle(px, py, 3, RED)
        c.circle(px, py, 1, (255, 255, 255))
        draw_text(c, px + dx, py + dy, label, 1, INK, bold=True)

# ---------------------------------------------------------------- content
LEADS = [
    ("STRAIT OF HORMUZ - MIDDLE EAST", "TWO TANKERS MINED IN HORMUZ",
     "Iran's Revolutionary Guards say two oil tankers struck naval "
     "mines and caught fire in the Strait of Hormuz. The vessels had "
     "used an unauthorised route, Tehran says. Brent fell to $87.43 "
     "as Gulf supply fears clashed with rising exports.", art_hormuz),
    ("JIUQUAN - SPACE", "PAKISTAN'S FIRST ASTRONAUT REACHES ORBIT",
     "Shenzhou-24 lifted off at 08:18 Beijing time and docked with "
     "Tiangong three and a half hours later. Muhammad Zeeshan Ali, "
     "40, is the first Pakistani in orbit and the first foreigner "
     "aboard the Chinese station. The crew will run 90 experiments.",
     art_shenzhou),
    ("NEW YORK - TECHNOLOGY", "HUAWEI CONVICTED IN US COURT",
     "A Brooklyn jury found Huawei guilty on 10 of 12 counts, "
     "including bank fraud, wire fraud, sanctions violations and "
     "conspiracy to steal trade secrets, after a trial of more than "
     "two months. The jury acquitted the firm of racketeering.",
     art_huawei),
]

# (tag, headline, detail) — every headline and detail <= 52 chars.
BRIEFS = [
    ("RAS TANURA", "HOUTHIS SAY THEY HIT SAUDI REFINERY",
     "Ras Tanura attack caused fires, spokesman says"),
    ("GAZA", "ISRAEL KILLS HAMAS SECURITY CHIEF",
     "Abuelouf dies with wife and two children in strike"),
    ("RIYADH", "HOUTHI STRIKE ON TOWER INJURES 11",
     "King Abdullah district tower hit on Tuesday"),
    ("TEHRAN", "US WEIGHS HITTING TOP IRANIAN LEADERS",
     "Israel cites chemical weapons in push for action"),
    ("BENGHAZI", "LIBYA VOWS REVENGE FOR DRONE DEATHS",
     "Ukraine strike killed two naval officers Sunday"),
    ("SAMARA", "UKRAINE DRONES HIT TWO ROSNEFT REFINERIES",
     "Syzran and Kuibyshev ablaze; one killed, 145 downed"),
    ("ODESA", "RUSSIAN STRIKE KILLS TWO, INJURES THREE",
     "Child among wounded; Kyiv flat ablaze, two hurt"),
    ("KYIV", "ZELENSKY: UKRAINE NEEDS 115BN EUROS IN 2027",
     "Aid plea as US pauses Patriot supplies to Kyiv"),
    ("WASHINGTON", "US PAUSES PATRIOT SUPPLIES TO UKRAINE",
     "Defence chief halts deliveries amid aid debate"),
    ("BERLIN", "MERZ: RUSSIA WANTS MORE THAN UKRAINE",
     "Chancellor accuses Moscow of escalating threats"),
    ("WARSAW", "RUSSIAN DRONE ENTERS POLISH AIRSPACE",
     "Second incursion in four days, Warsaw says"),
    ("BRUSSELS", "EUROZONE INFLATION RISES TO 4.0 PERCENT",
     "Eurostat reports higher prices alongside growth"),
    ("MADRID", "REAL MADRID 5-1 PSV; CITY HELD 2-2",
     "Arsenal 1-1 Dortmund in Champions League ties"),
    ("LUTON", "EASYJET PROFIT FALLS 89 PERCENT",
     "Fuel costs hit airline with 244m pound blow"),
    ("BEIJING", "CHINA PROBES SHANGHAI PARTY CHIEF",
     "Chen Jining investigated, Beijing announces"),
    ("SHANGHAI", "QIANFAN: CHINA'S ANSWER TO STARLINK",
     "Satellite network takes shape, analysts say"),
    ("MUMBAI", "INDIA GOLD STEADY AT 10,560 RUPEES",
     "Per gram on Wednesday, little changed on day"),
    ("BOGOR", "FLOODED GOLD MINE TOLL RISES TO SIX",
     "Three more bodies found; 20 miners still trapped"),
    ("CANBERRA", "AUSTRALIA INFLATION RISES TO 4.9 PERCENT",
     "Fuel drives prices; RBA expected to hold rates"),
    ("HONIARA", "SOLOMONS SIGN PACT BARRING FOREIGN BASES",
     "Treaty with Australia signed in Canberra"),
    ("WASHINGTON", "TRUMP PLANS TARIFFS ON 16 ECONOMIES",
     "China, EU and Japan among targets, US media say"),
    ("TEXAS", "DELL Q3 REVENUE 54.9BN DOLLARS, UP 103 PCT",
     "AI server sales 22.0bn dollars, up 291 percent"),
    ("MADRID", "ABREGO GARCIA LEAVES US FOR SPAIN",
     "20-month deportation fight ends in voluntary exit"),
    ("SAN FRANCISCO", "AI STAFF DOUBT MODELS ARE SAFE TO RELEASE",
     "Axios cites two dozen sources at Anthropic, OpenAI"),
    ("SEATTLE", "AMAZON BUYS DECART TO CHASE NVIDIA",
     "Deal bets on software to close the chip gap"),
    ("CARTAGENA", "FORCES FREE ALL SUPERMARKET HOSTAGES",
     "Siege ends; one captor killed in storming"),
    ("CARACAS", "US BACKS VENEZUELA RECONCILIATION TALKS",
     "1,300 apply for 32 top-court seats in overhaul"),
    ("BLUE NILE", "RSF DRONE STRIKES KILL 19 CIVILIANS",
     "20 wounded in two cities, rights lawyers say"),
    ("DAKAR", "CAS RESTORES SENEGAL'S AFCON TITLE",
     "Court backs Senegal on appeal; Morocco vows fight"),
    ("LUSAKA", "ZAMBIA INDICTS OPPOSITION LEADER",
     "Treason charges filed against opposition chief"),
    ("NAIROBI", "STEINMEIER ENDS AFRICA TOUR IN KENYA",
     "German president meets Ruto in Nairobi"),
    ("ANTALYA", "COP31: 90 NATIONS REJECT DRAFT TEXT",
     "Longest COP ends with no Antalya Pact agreed"),
    ("VATICAN", "POPE LAMENTS COP31 FAILURE",
     "Leo XIV: extreme weather events more frequent"),
    ("GENEVA", "UN: CUTS THREATEN HIV PROGRESS",
     "Funding cuts put decades of gains at risk"),
]

REGIONS = ["MIDDLE EAST", "EUROPE", "EAST ASIA", "SOUTH ASIA",
           "SOUTHEAST ASIA & OCEANIA", "NORTH AMERICA",
           "LATIN AMERICA", "AFRICA", "GLOBAL"]

STATS = [("37", "STORIES"), ("9", "REGIONS"), ("-6.16%", "KOSPI"),
         ("2", "TANKERS MINED"), ("490,334", "RUSSIAN WAR DEAD"),
         ("90", "NATIONS REJECT COP31 DRAFT")]

MARKETS_1 = ("KOSPI 4,697.51 -6.16%   NIKKEI 57,011.62 -2.78%   "
             "TAIEX 38,142 -4.9%   HANG SENG 21,966.01 -1.1%   "
             "SHANGHAI 3,476.47 -2.0%")
MARKETS_2 = ("DOW 50,018.70 +0.85%   S&P 7,201.09 -0.50%   "
             "NASDAQ 23,733.54 -1.48%   GOLD $3,524 -0.9%   "
             "BRENT $87.43 -1.5%   WTI $80.56 -1.8%   BITCOIN $59,000")

SOURCES = ("Sources: Just Security 25 Nov; Principia 25 Nov; Daily "
           "Edition No. 280; AP; Reuters; Xinhua; Eurostat; UEFA; CAS.")


# ---------------------------------------------------------------- page
def draw_page():
    c = Canvas(W, H, PAPER)
    # --- masthead
    c.hline(24, 8, 976, INK)
    c.hline(24, 11, 976, INK)
    draw_text(c, 24, 22, "VOL. I - NO. 280", 1, INK_SOFT)
    draw_text(c, 1024 - 24 - text_w("PRICE: ONE IMAGE", 1), 22,
              "PRICE: ONE IMAGE", 1, INK_SOFT)
    title = "THE WORLD TODAY"
    draw_text(c, (W - text_w(title, 5)) // 2, 20, title, 5, INK, bold=True)
    draw_text(c, (W - text_w("WEDNESDAY 25 NOVEMBER 2026", 2)) // 2, 62,
              "WEDNESDAY 25 NOVEMBER 2026", 2, DARKRED, bold=True)
    c.hline(24, 84, 976, INK)
    c.hline(24, 87, 976, INK)
    # --- stats strip
    sy = 94
    sw = 976 // 6
    for i, (num, label) in enumerate(STATS):
        bx = 24 + i * sw
        draw_text(c, bx + 8, sy, num, 2, RED, bold=True)
        draw_text(c, bx + 8, sy + 18, label, 1, INK_SOFT)
        if i:
            c.vline(bx, sy, 30, RULE)
    c.hline(24, sy + 32, 976, INK)
    # --- leads
    col_x = [24, 355, 686]
    col_w = 314
    for ci, (kicker, head, body, art) in enumerate(LEADS):
        x = col_x[ci]
        draw_text(c, x, 138, kicker, 1, RED, bold=True)
        c.hline(x, 150, col_w, RULE)
        art(c, x, 154, col_w, 150)
        c.rect(x, 154, col_w, 1, INK)
        c.rect(x, 303, col_w, 1, INK)
        hy = draw_para(c, x, 310, head, 26, scale=2, color=INK,
                       leading=17, bold=True, max_lines=2)
        draw_para(c, x, hy + 6, body, 52, scale=1, color=INK_SOFT,
                  leading=10, max_lines=5)
        if ci < 2:
            c.vline(x + col_w + 8, 138, 268, RULE)
    c.hline(24, 412, 976, INK)
    # --- markets strip
    draw_text(c, 24, 420, "MARKETS - WEDNESDAY 25 NOVEMBER 2026", 1, INK, bold=True)
    draw_text(c, 24, 432, MARKETS_1, 1, INK_SOFT)
    draw_text(c, 24, 444, MARKETS_2, 1, INK_SOFT)
    c.hline(24, 458, 976, INK)
    # --- map
    draw_text(c, 24, 466, "THE WORLD - WHERE TODAY'S NEWS HAPPENED", 1,
              INK, bold=True)
    draw_text(c, 1024 - 24 - text_w("14 PLACES MARKED", 1), 466,
              "14 PLACES MARKED", 1, INK_SOFT)
    draw_map(c, 24, 480, 976, 146)
    c.hline(24, 632, 976, INK)
    # --- briefs
    draw_text(c, 24, 640, "AROUND THE WORLD - 34 BRIEFS", 1, INK, bold=True)
    draw_text(c, 1024 - 24 - text_w("ALL DATED 25 NOVEMBER 2026", 1), 640,
              "ALL DATED 25 NOVEMBER 2026", 1, INK_SOFT)
    c.hline(24, 652, 976, RULE)
    cols = [BRIEFS[i::3] for i in range(3)]
    for ci, col in enumerate(cols):
        x = col_x[ci]
        yy = 660
        for (tag, head, detail) in col:
            draw_text(c, x, yy, tag, 1, RED, bold=True)
            draw_text(c, x, yy + 9, head, 1, INK, bold=True)
            draw_text(c, x, yy + 18, detail, 1, INK_SOFT)
            yy += 28
    # --- footer
    c.hline(24, 998, 976, INK)
    draw_text(c, 24, 1006, SOURCES, 1, INK_SOFT)
    grain(c)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    assert len(LEADS) + len(BRIEFS) == 37, "story count"
    assert len(REGIONS) == 9, "region count"
    for (tag, head, detail) in BRIEFS:
        assert len(head) <= 52 and len(detail) <= 52, (tag, head, detail)
    c = draw_page()
    path = os.path.join(out_dir, "entry.png")
    n = write_png(c, path)
    print(f"wrote {path} ({n} bytes)")


if __name__ == "__main__":
    main()
