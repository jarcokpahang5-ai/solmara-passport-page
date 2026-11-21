#!/usr/bin/env python3
"""Solmara passport page — make.fun entry.

Draws one invented passport spread for the Republic of Solmara (a country
that does not exist) and writes it as a PNG to $MAKEFUN_OUTPUT_DIR/entry.png.

Pure Python 3.13 standard library only. No network, no randomness, no
wall-clock reads: two runs produce byte-identical output.
"""

import binascii
import math
import os
import struct
import zlib

W, H = 1024, 640

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
_G = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}
FONT = {ch: tuple(tuple(c == "1" for c in row) for row in rows)
        for ch, rows in _G.items()}
BLANK = ((False,) * 5,) * 7


def text_width(s, scale, spacing=None):
    adv = 5 * scale + (scale if spacing is None else spacing)
    return len(s) * adv - (scale if spacing is None else spacing)


# ---------------------------------------------------------------- canvas
class Canvas:
    """RGB canvas with a magenta colour-key for transparency on stamps."""

    KEY = (255, 0, 255)

    def __init__(self, w, h, bg=(255, 0, 255)):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])

    def fill(self, color):
        self.px[:] = bytes(color) * (self.w * self.h)

    def rect(self, x0, y0, x1, y1, color):
        x0, x1 = max(0, x0), min(self.w, x1)
        y0, y1 = max(0, y0), min(self.h, y1)
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, color):
        self.rect(x0, y, x1, y + 1, color)

    def vline(self, x, y0, y1, color):
        self.rect(x, y0, x + 1, y1, color)

    def outline(self, x0, y0, x1, y1, color, t=1):
        for k in range(t):
            self.hline(x0, x1, y0 + k, color)
            self.hline(x0, x1, y1 - 1 - k, color)
            self.vline(x0 + k, y0, y1, color)
            self.vline(x1 - 1 - k, y0, y1, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.put(px, py, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def disc(self, cx, cy, r, color):
        for y in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - y * y)))
            self.hline(cx - half, cx + half + 1, cy + y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for y in range(-ry, ry + 1):
            t = 1.0 - (y * y) / float(ry * ry)
            half = int(rx * math.sqrt(max(0.0, t)))
            self.hline(cx - half, cx + half + 1, cy + y, color)

    def blit(self, src, x0, y0):
        """Copy a fully opaque source canvas onto this one."""
        for y in range(src.h):
            i = ((y0 + y) * self.w + x0) * 3
            j = y * src.w * 3
            self.px[i:i + src.w * 3] = src.px[j:j + src.w * 3]

    def text(self, x, y, s, scale, color, bold=False, spacing=None):
        adv = 5 * scale + (scale if spacing is None else spacing)
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for gy in range(7):
                for gx in range(5):
                    if glyph[gy][gx]:
                        self.rect(cx + gx * scale, y + gy * scale,
                                  cx + gx * scale + scale,
                                  y + gy * scale + scale, color)
                        if bold:
                            self.rect(cx + gx * scale + 1, y + gy * scale,
                                      cx + gx * scale + scale + 1,
                                      y + gy * scale + scale, color)
            cx += adv
        return cx

    def text_centred(self, cx, y, s, scale, color, bold=False, spacing=None):
        self.text(cx - text_width(s, scale, spacing) // 2, y, s, scale,
                  color, bold=bold, spacing=spacing)


def blit_rotated(dst, src, cx, cy, angle_deg):
    """Blit src canvas onto dst, rotated about its centre (magenta = clear)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    hw, hh = src.w / 2.0, src.h / 2.0
    # bounding box of the rotated rectangle
    corners = [(-hw, -hh), (hw, -hh), (-hw, hh), (hw, hh)]
    rx = [c[0] * ca - c[1] * sa for c in corners]
    ry = [c[0] * sa + c[1] * ca for c in corners]
    x0, x1 = int(cx + min(rx)) - 1, int(cx + max(rx)) + 2
    y0, y1 = int(cy + min(ry)) - 1, int(cy + max(ry)) + 2
    for dy in range(y0, y1):
        for dx in range(x0, x1):
            ox, oy = dx - cx, dy - cy
            sx = ox * ca + oy * sa + hw
            sy = -ox * sa + oy * ca + hh
            ix, iy = int(sx), int(sy)
            if 0 <= ix < src.w and 0 <= iy < src.h:
                c = src.get(ix, iy)
                if c != Canvas.KEY:
                    dst.put(dx, dy, c)


# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, rgb):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3]
                    for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
CREAM = (246, 239, 220)
CREAM_DARK = (232, 222, 196)
PAPER_LINE = (184, 169, 126)
INK = (28, 43, 74)          # deep navy ink
INK_SOFT = (74, 84, 106)
BURGUNDY = (122, 31, 43)
GOLD = (176, 138, 58)
DESK = (38, 44, 54)
FOLD = (24, 28, 36)
STAMP_BLUE = (43, 74, 122)
STAMP_GREEN = (46, 107, 79)
STAMP_PURPLE = (91, 58, 122)
STAMP_RED = (150, 48, 40)
MRZ_BG = (238, 234, 222)


def guilloche(cv, x0, y0, x1, y1, color):
    """Faint wavy security lines across a page."""
    for k in range(0, (y1 - y0) // 14 + 1):
        yb = y0 + 8 + k * 14
        prev = None
        for x in range(x0, x1, 3):
            y = yb + int(3 * math.sin((x - x0) / 26.0 + k * 1.7))
            if prev is not None:
                cv.line(prev[0], prev[1], x, y, color)
            prev = (x, y)


def emblem(cv, cx, cy, r, color):
    """Coat of arms of Solmara: a rising sun over three waves."""
    cv.circle(cx, cy, r, color)
    cv.circle(cx, cy, r - 3, color)
    # sun: half disc with rays
    cv.disc(cx, cy - 2, r - 9, color)
    cv.rect(cx - (r - 9), cy - 2, cx + (r - 9) + 1, cy + 2, CREAM)
    for k in range(-3, 4):
        ang = math.pi * (0.5 + k * 0.22)
        x0 = cx + int((r - 6) * math.cos(ang))
        y0 = cy - 2 - int((r - 6) * math.sin(ang))
        x1 = cx + int((r + 4) * math.cos(ang))
        y1 = cy - 2 - int((r + 4) * math.sin(ang))
        cv.line(x0, y0, x1, y1, color)
    # three waves
    for k, wy in enumerate((cy + 6, cy + 11, cy + 16)):
        prev = None
        for x in range(cx - r + 5, cx + r - 4, 2):
            y = wy + int(2 * math.sin((x - cx) / 7.0 + k * 1.3))
            if prev is not None:
                cv.line(prev[0], prev[1], x, y, color)
            prev = (x, y)


def portrait(cv, x0, y0, x1, y1):
    """Stylised portrait photograph: a woman in three-quarter view."""
    cv.outline(x0, y0, x1, y1, INK, 2)
    # photo background: pale blue-grey bands with faint diagonal light
    for y in range(y0 + 2, y1 - 1):
        t = (y - y0) / float(y1 - y0)
        base = (196 - int(22 * t), 206 - int(20 * t), 214 - int(14 * t))
        cv.hline(x0 + 2, x1 - 1, y, base)
    for k in range(-40, 260, 26):
        cv.line(x0 + 2 + k, y1 - 2, x0 + 2 + k + 60, y0 + 2, (214, 221, 226))
    # shoulders / jacket
    cv.ellipse((x0 + x1) // 2, y1 + 26, 78, 66, (51, 80, 110))
    cv.ellipse((x0 + x1) // 2, y1 + 30, 60, 52, (43, 68, 96))
    # neck and head
    cx = (x0 + x1) // 2
    cv.rect(cx - 13, y0 + 118, cx + 14, y0 + 150, (201, 161, 132))
    cv.disc(cx, y0 + 92, 40, (201, 161, 132))
    # hair: dark sweep over the top of the head
    cv.disc(cx, y0 + 66, 41, (58, 46, 38))
    cv.rect(cx - 41, y0 + 66, cx + 42, y0 + 92, (58, 46, 38))
    cv.disc(cx, y0 + 92, 40, (201, 161, 132))
    cv.rect(cx - 40, y0 + 92, cx + 41, y0 + 104, (201, 161, 132))
    # hair falling on the right side
    cv.ellipse(cx + 34, y0 + 108, 10, 30, (58, 46, 38))
    # collar and jacket opening
    cv.line(cx - 8, y0 + 148, cx, y0 + 168, CREAM)
    cv.line(cx + 8, y0 + 148, cx, y0 + 168, CREAM)
    cv.line(cx - 8, y0 + 148, cx - 26, y0 + 168, (226, 228, 230))
    cv.line(cx + 8, y0 + 148, cx + 26, y0 + 168, (226, 228, 230))
    # faint scanlines over the photo, like a printed photograph
    for y in range(y0 + 4, y1 - 2, 4):
        cv.hline(x0 + 2, x1 - 1, y, (255, 255, 255))


def wrap_text(s, scale, max_w, spacing=None):
    words, lines, cur = s.split(" "), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale, spacing) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def stamp_canvas(w, h, color, title, lines, date_text, kind):
    """A rubber stamp on a transparent (magenta-key) canvas."""
    cv = Canvas(w, h)
    cv.outline(4, 4, w - 4, h - 4, color, 2)
    cv.outline(10, 10, w - 10, h - 10, color, 1)
    y = 20
    cv.text_centred(w // 2, y, title, 2, color, bold=True)
    y += 22
    cv.hline(16, w - 16, y, color)
    y += 8
    for ln in lines:
        cv.text_centred(w // 2, y, ln, 1, color)
        y += 12
    if kind == "round":
        # circular date stamp overlapping the corner
        ccx, ccy, r = w - 52, h - 40, 30
        cv.circle(ccx, ccy, r, color)
        cv.circle(ccx, ccy, r - 4, color)
        cv.text_centred(ccx, ccy - 11, date_text, 1, color, bold=True)
        cv.text_centred(ccx, ccy + 2, "SOLMARA", 1, color)
    else:
        cv.text_centred(w // 2, y + 4, date_text, 1, color, bold=True)
    # deterministic wear: knock out a sparse, fixed pattern of ink dots
    for yy in range(4, h - 4):
        for xx in range(4, w - 4):
            if cv.get(xx, yy) != Canvas.KEY and (xx * 7 + yy * 13) % 61 == 0:
                cv.put(xx, yy, Canvas.KEY)
    return cv


def field(cv, x, y, label, value, value_scale=2, label_color=INK_SOFT):
    cv.text(x, y, label, 1, label_color)
    cv.text(x, y + 11, value, value_scale, INK, bold=True)


def draw():
    cv = Canvas(W, H, DESK)
    # desk shading at the edges
    cv.rect(0, 0, W, 10, (30, 35, 44))
    cv.rect(0, H - 10, W, H, (30, 35, 44))

    # ---- the two pages
    LX0, LY0, LX1, LY1 = 28, 24, 500, 616
    RX0, RY0, RX1, RY1 = 524, 24, 996, 616
    cv.rect(LX0, LY0, LX1, LY1, CREAM)
    cv.rect(RX0, RY0, RX1, RY1, CREAM)
    # centre fold shadow
    cv.rect(500, 24, 524, 616, FOLD)
    cv.rect(500, 24, 504, 616, (52, 58, 70))
    cv.rect(520, 24, 524, 616, (52, 58, 70))
    # page inner rules
    cv.outline(LX0 + 10, LY0 + 10, LX1 - 10, LY1 - 10, PAPER_LINE, 1)
    cv.outline(RX0 + 10, RY0 + 10, RX1 - 10, RY1 - 10, PAPER_LINE, 1)
    guilloche(cv, LX0 + 12, LY0 + 12, LX1 - 12, LY1 - 12, CREAM_DARK)
    guilloche(cv, RX0 + 12, RY0 + 12, RX1 - 12, RY1 - 12, CREAM_DARK)

    # ================= LEFT PAGE — data page =================
    emblem(cv, 264, 62, 24, BURGUNDY)
    cv.text_centred(264, 96, "REPUBLIC OF SOLMARA", 2, INK, bold=True)
    cv.text_centred(264, 118, "PASSPORT", 3, BURGUNDY, bold=True)
    cv.text_centred(264, 140, "PASSEPORT  ·  PASAPOR", 1, INK_SOFT)
    cv.hline(60, 468, 158, INK)
    cv.hline(60, 468, 160, GOLD)

    # portrait (drawn on its own canvas so nothing spills past its frame)
    pc = Canvas(170, 220, CREAM)
    portrait(pc, 0, 0, 170, 220)
    cv.blit(pc, 52, 176)
    cv.text_centred(137, 402, "PHOTOGRAPH", 1, INK_SOFT)

    # personal data, right of the portrait
    fx = 244
    field(cv, fx, 176, "SURNAME / NOM", "SOLEN")
    field(cv, fx, 212, "GIVEN NAMES / PRENOMS", "ARA VELMIRA")
    field(cv, fx, 248, "NATIONALITY / NATIONALITE", "SOLMARIAN")
    field(cv, fx, 284, "DATE OF BIRTH / NEE LE", "14 MAR 1988")
    field(cv, fx, 320, "PLACE OF BIRTH / LIEU DE NAISSANCE", "PORT LUMEN")
    field(cv, fx, 356, "SEX / SEXE", "F")
    cv.text(360, 356, "PERSONAL NO", 1, INK_SOFT)
    cv.text(360, 367, "8803142214", 2, INK, bold=True)

    # document details, full width under the portrait
    cv.hline(52, 476, 424, PAPER_LINE)
    field(cv, 52, 436, "PASSPORT NO", "SM0048217")
    field(cv, 196, 436, "DATE OF ISSUE", "12 JAN 2021")
    field(cv, 356, 436, "DATE OF EXPIRY", "12 JAN 2031")
    field(cv, 52, 472, "AUTHORITY / AUTORITE",
          "MINISTRY OF THE INTERIOR - PORT LUMEN", value_scale=1)

    # holder's signature: a flowing hand
    cv.text(52, 500, "HOLDER'S SIGNATURE", 1, INK_SOFT)
    sx, sy = 52, 522
    for x in range(0, 150, 2):
        y = sy + int(4 * math.sin(x / 14.0) + 2 * math.sin(x / 5.0))
        cv.put(sx + x, y, INK)
        cv.put(sx + x, y + 1, INK)
    cv.hline(52, 202, 534, INK)

    # machine-readable zone
    mrz1 = ("P<SMR" + "SOLEN<<ARA<VELMIRA").ljust(44, "<")
    mrz2 = "SM0048217<8SMR8803145F3101122".ljust(44, "<")
    cv.rect(52, 546, 476, 600, MRZ_BG)
    cv.outline(52, 546, 476, 600, PAPER_LINE, 1)
    cv.text(60, 554, mrz1, 2, INK, spacing=-1)
    cv.text(60, 574, mrz2, 2, INK, spacing=-1)

    # ================= RIGHT PAGE — visas and stamps =================
    cv.text_centred(760, 44, "VISAS", 3, BURGUNDY, bold=True)
    cv.text_centred(760, 70, "STAMPS AND ENDORSEMENTS", 1, INK_SOFT)
    cv.hline(560, 960, 92, INK)
    cv.hline(560, 960, 94, GOLD)

    # neighbouring countries' stamps — all dated after the 12 JAN 2021
    # issue and before the 12 JAN 2031 expiry, in travel order.
    st1 = stamp_canvas(270, 118, STAMP_BLUE, "KAVARRA",
                       ["ARRIVAL", "PORT OF KAVAR", "OFFICER 17"],
                       "03 JUN 2023", "round")
    blit_rotated(cv, st1, 675, 170, -7)
    st2 = stamp_canvas(260, 108, STAMP_GREEN, "TELMOR",
                       ["ENTRY", "LAND BORDER NORTH", "OFFICER 04"],
                       "19 AUG 2024", "round")
    blit_rotated(cv, st2, 860, 290, 6)
    st3 = stamp_canvas(260, 100, STAMP_PURPLE, "ISLE OF NARIN",
                       ["ENTRY 27 FEB 2025", "EXIT 11 MAR 2025",
                        "FERRY TERMINAL"],
                       "11 MAR 2025", "text")
    blit_rotated(cv, st3, 660, 395, -4)
    fee = stamp_canvas(170, 96, STAMP_RED, "FEE PAID",
                       ["40 LUM", "PORT LUMEN"], "12 JAN 2021", "text")
    blit_rotated(cv, fee, 905, 150, 8)

    # the telling detail: a visa condition that reveals the place
    bx0, by0, bx1, by1 = 548, 456, 972, 556
    cv.rect(bx0, by0, bx1, by1, (250, 244, 228))
    cv.outline(bx0, by0, bx1, by1, BURGUNDY, 2)
    cv.text(bx0 + 14, by0 + 12, "VISA CONDITION", 2, BURGUNDY, bold=True)
    cond = ("HOLDER MAY ENTER THE CORAL FREE ZONE BY SEA FERRY ONLY. "
            "MAXIMUM STAY 30 DAYS. EMPLOYMENT PROHIBITED. "
            "THE BEARER TRAVELS ON A FISHING LICENCE, NOT A WORK PERMIT.")
    y = by0 + 40
    for ln in wrap_text(cond, 1, bx1 - bx0 - 28):
        cv.text(bx0 + 14, y, ln, 1, INK)
        y += 13

    # trilingual footer
    cv.text_centred(760, 576, "SOLMARIAN - ENGLISH - FRANCAIS", 1, INK_SOFT)
    cv.text_centred(760, 592,
                    "THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC",
                    1, INK_SOFT)
    cv.text_centred(760, 604, "OF SOLMARA", 1, INK_SOFT)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, cv.w, cv.h, bytes(cv.px))
    print("wrote %s (%dx%d, %d bytes)" % (path, cv.w, cv.h, size))


if __name__ == "__main__":
    main()
