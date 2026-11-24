#!/usr/bin/env python3
"""news-image-20261124 -- one front page summing up Tuesday 24 November 2026.

Draws a 1024x1024 newspaper front page (54 stories: 13 illustrated cards
plus 41 one-line briefs) with the Python standard library only and no
network access. The PNG bytes are fully deterministic: two runs write the
same file. Output goes to $MAKEFUN_OUTPUT_DIR/entry.png (default ./out/).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (247, 241, 222)   # paper
PAPER2 = (252, 248, 235)  # card paper
INK = (24, 22, 18)        # near-black
GREY = (110, 104, 90)
LINE = (60, 56, 46)
RED = (176, 58, 46)
BLUE = (43, 94, 167)
TEAL = (30, 122, 90)
PURPLE = (125, 60, 152)
AMBER = (156, 106, 18)
SLATE = (85, 85, 85)
OCEAN = (207, 224, 232)
LAND = (232, 221, 192)
LAND_LINE = (138, 125, 90)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (46, 134, 70)
GOLD = (214, 178, 74)
SKY = (38, 48, 74)

REGION_COLOR = {
    "EUROPE": BLUE,
    "MIDDLE EAST": RED,
    "ASIA": TEAL,
    "AFRICA": PURPLE,
    "AMERICAS": AMBER,
    "OCEANIA": (42, 125, 140),
    "WORLD": SLATE,
}

# ------------------------------------------------------------------- canvas
PIX = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i], PIX[i + 1], PIX[i + 2] = color


def fill_rect(x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            PIX[i], PIX[i + 1], PIX[i + 2] = color


def rect_border(x, y, w, h, color, t=1):
    fill_rect(x, y, w, t, color)
    fill_rect(x, y + h - t, w, t, color)
    fill_rect(x, y, t, h, color)
    fill_rect(x + w - t, y, t, h, color)


def hline(x, y, w, color, t=1):
    fill_rect(x, y, w, t, color)


def vline(x, y, h, color, t=1):
    fill_rect(x, y, t, h, color)


def line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, color, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if fill:
                if d2 <= r * r:
                    set_px(xx, yy, color)
            else:
                if r * r - 2 * r <= d2 <= r * r:
                    set_px(xx, yy, color)


def poly_fill(points, color):
    """Scanline fill for a simple polygon given as [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        nodes = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                nodes.append(xi)
        nodes.sort()
        for k in range(0, len(nodes) - 1, 2):
            xa, xb = int(nodes[k]), int(nodes[k + 1])
            for x in range(max(0, xa), min(W, xb + 1)):
                set_px(x, y, color)


def poly_line(points, color):
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        line(int(x0), int(y0), int(x1), int(y1), color)


# ------------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 bits, most significant bit on the left.
# Written from scratch for this page; all page text is set in capitals.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "~": (0, 0, 0x06, 0x09, 0x00, 0, 0),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "·": (0, 0, 0, 0x0C, 0x0C, 0, 0),
}


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(s, x, y, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    fill_rect(cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(s, cx, y, scale, color):
    draw_text(s, cx - text_w(s, scale) // 2, y, scale, color)


def wrap_text(s, max_chars):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, rgb):
    raw = b"".join(
        b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)

# ------------------------------------------------------------------- content
# All figures were checked against the 24 Nov 2026 research file and, for
# the two flagged numbers, re-verified by web search during the build:
#   * Nepal aid is $1.62bn (NPR 240bn / INR 15,000 crore), announced Mon
#     23 Nov in Delhi -- NOT 1.4bn euros.
#   * Nvidia added about $952bn of market value on Mon 23 Nov (+31.5% to
#     $165.05), the biggest one-day gain ever; Tue premarket -5.2%.
# Dating discipline: a story is on this page only if it happened, or was
# first reported, on Tue 24 Nov 2026, or is explicitly dated to Mon 23 Nov
# inside its own text. Everything else big that broke earlier is named in
# the DATE CHECK box instead of being shown as today's news.

CARDS = [
    dict(num=1, region="AMERICAS", kicker="MARKETS - USA - BBC, REUTERS, WSJ",
         headline="NVIDIA RALLY WOBBLES A DAY LATER",
         body="Huang was reinstated Mon 23 Nov; shares jumped 31.5% to $165.05, adding about $952bn - the biggest one-day gain ever. Tue premarket: -5.2% to $156.40 as investors questioned board governance.",
         strip="+31.5% MON - -5.2% TUE PREMARKET - $952BN ADDED", art="nvidia"),
    dict(num=2, region="AFRICA", kicker="WAR - AFRICA - KYIV INDEPENDENT, UN NEWS",
         headline="UKRAINE WAR SPREADS TO LIBYA",
         body="Kyiv confirms 7 naval drones sank Russia's corvette Merkury in Benghazi port; the attack was Sun 22 Nov. Tue: UNSMIL demands an independent probe and Tripoli seeks answers from Kyiv.",
         strip="7 NAVAL DRONES - 1 CORVETTE SUNK", art="libya"),
    dict(num=3, region="EUROPE", kicker="WAR - EUROPE - BBC, NDR",
         headline="NATO: WE WILL DEFEND SPACE, TOO",
         body="Secretary General Mark Rutte says NATO will defend itself against threats from space, after reports Russia is preparing a nuclear-armed satellite launch within 60 days.",
         strip="NUCLEAR SATELLITE LAUNCH WITHIN 60 DAYS?", art="space"),
    dict(num=4, region="MIDDLE EAST", kicker="MIDDLE EAST - REUTERS",
         headline="GAZA: STRIKES KEEP KILLING",
         body="Israeli strikes Tue killed 6+ in Khan Younis and Netzarim, incl. 2 police. Oxfam calls Gaza 'toxic land'.",
         strip="6+ KILLED TUE", art="gaza"),
    dict(num=5, region="ASIA", kicker="ASIA - HORIZON",
         headline="14 NATIONS BACK ICJ RULING",
         body="UK, Spain, Canada, Australia + 10 more recognise the 19 Nov ruling (9-6): Myanmar committed genocide.",
         strip="14 COUNTRIES - 9-6 RULING", art="icj"),
    dict(num=6, region="ASIA", kicker="ASIA - WION, BASARNAS",
         headline="24 DEAD IN SERANG FACTORY FIRE",
         body="Fire at PT Milki Taha (Milkita sweets) broke out over the weekend of 22-23 Nov: 24 dead, ~34 missing.",
         strip="24 DEAD - ~34 MISSING", art="factory"),
    dict(num=7, region="EUROPE", kicker="EUROPE - KYIV INDEPENDENT",
         headline="7 EU STATES WANT CURBS ON RUSSIAN VISAS",
         body="Denmark, Estonia, Finland, Latvia, Lithuania, Poland and Sweden wrote to von der Leyen and Costa on 23 Nov.",
         strip="7 COUNTRIES - 22ND PACKAGE", art="visa"),
    dict(num=8, region="EUROPE", kicker="EUROPE - KYIV INDEPENDENT",
         headline="GERMANY FIRST INTO UKRAINE'S DELTA",
         body="Berlin signs a letter of intent for first access to Ukraine's Delta battlefield system, plus more missiles.",
         strip="FIRST ACCESS - DELTA SYSTEM", art="delta"),
    dict(num=9, region="AMERICAS", kicker="AMERICAS - AP",
         headline="'EL CHAPO ISIDRO' TRIED IN MEXICO",
         body="Meza Flores was caught in Sinaloa with a US drone's help. Mexico refuses extradition and will try him.",
         strip="US DRONE AIDED CAPTURE", art="court"),
    dict(num=10, region="ASIA", kicker="ASIA - GLOBAL TIMES",
         headline="CHINA STARTS 6G; PAKISTANI TO TIANGONG",
         body="China launches 6G trials in 8 regions incl. Beijing and Shanghai. Zeeshan Ali is the first foreigner on Tiangong.",
         strip="6G - 8 REGIONS", art="tiangong"),
    dict(num=11, region="WORLD", kicker="WORLD - REUTERS",
         headline="COP31 COLLAPSES AS TALKS FAIL",
         body="UN climate talks in Turkiye fail with no deal; Australia urged to sack its minister.",
         strip="COP31 COLLAPSES", art="cop"),
    dict(num=12, region="WORLD", kicker="WORLD - UN NEWS",
         headline="UN CHIEF: WORLD NEEDS AI RULES",
         body="From Barbados, Guterres says states must start talks on a global AI-risk framework within a year.",
         strip="FRAMEWORK WITHIN 1 YEAR", art="ai"),
    dict(num=13, region="ASIA", kicker="ASIA - MORNINGSTAR",
         headline="ASIAN TECH RALLY SOARS",
         body="Nikkei +4.2%, Kospi +7.3%, Taiex +9.0% as Huang's return fires an AI rally. TSMC and Foxconn up ~10%.",
         strip="NIKKEI +4.2% - KOSPI +7.3%", art="rally"),
]

# 41 one-line briefs, displayed numbered 14-54 in order. Six items from the
# research list were dropped to keep the page tight: the Murmansk governor
# arrest, the DR Congo plane claim, Hasina's planned return, the
# California/Seychelles mixed item, the Tai Po anniversary, and the
# Netanyahu-urges-Trump item.
BRIEFS = [
    "Zaporizhzhia hit overnight 23 Nov: block damaged, 2 dead, 33 hurt incl. a baby",
    "Russian drone entered Polish airspace 22 Nov; NATO sends AWACS planes to Poland",
    "Zelensky, at NATO assembly in Berlin 23 Nov, asks for Ukraine to join NATO",
    "Leaked Rosstat data: over 700,000 Russian soldiers dead in Ukraine; toll nears 2m",
    "Russia rejects NATO Article 5-style guarantees; Kremlin uses nuclear threats",
    "Russia reported rebuilding a military base about 60 km from Finland",
    "Drone crashes and explodes in Transnistria, Moldova, on the night of 23 Nov",
    "Iran: singer Parastoo Ahmadi and 4 crew each given 74 lashes",
    "Iran will not talk until US meets 7 conditions; weighs ending blockade by force",
    "US sanctions dozens tied to Iran's shadow banking network",
    "Qatar PM meets Vance and Rubio in Washington to revive US-Iran talks",
    "Houthis: Saudi strikes in Hodeida kill 17; bus and truck attacks in Lahj kill ~25",
    "Iraq PM orders oil ministry to run fields in Kurdish-held Diyala, Kirkuk, Nineveh",
    "Ituri fighting disrupts Ebola response; WHO staff trapped 24 hrs+ in a ward",
    "Somalia and Uganda step up operations against Al-Shabaab as drawdown begins",
    "Sudan: US urges halt to arms flows and a humanitarian truce after RSF drone strike",
    "Spain's Supreme Court grants amnesty to Carles Puigdemont",
    "UK PM Burnham: no return to the EU without a referendum; Brexit row heats up",
    "Belgium anti-austerity strike disrupts national transport",
    "Solomon Islands ends its security pact with China",
    "US gives $2bn defence loan to the Philippines, plus Luzon Strait development",
    "China's 4th aircraft carrier nearly finished, reported nuclear-powered",
    "Russian jets enter South Korea's air defence zone Tue; Ulleung Island alerted",
    "China executes an official surnamed Ma for spying for a foreign state",
    "Mon: India pledges $1.62bn aid to Nepal as PM Shah visits Delhi after Aug floods",
    "Quake of 5.6 hits Nepal near the China border; tremors felt in India and China",
    "El Salvador: 3 soldiers die in an accidental blast on an anti-gang mission in Haiti",
    "US Democrats win the House with their biggest margin in decades (midterms)",
    "Trump orders US Army to delay blowing up toxic lead azide stockpile in Iowa",
    "Pentagon rebukes Canada over defence spending and its F-35 review",
    "US blacklists Megaspeed, at the centre of the Nvidia chip scandal",
    "Oregon and Virginia sue SpaceX over alleged Grok child-abuse images",
    "Arm extends CEO Rene Haas's term to 2033 amid Nvidia speculation",
    "CrowdStrike buys Zscaler in a $44bn deal",
    "UN agrees two years of talks on rules for autonomous weapons",
    "Pennsylvania records a 9th measles death; 46 counties affected",
    "Webb: star layers merged hours before supernova Cas A; cancer drug in tobacco",
    "Sport: Australia beat England in 2nd T20; Pope Francis diary published",
    "War threatens food aid for 7.3m more people",
    "US Army audit: Hawaii unit unready to deploy fast if war with China breaks out",
    "Venezuela: power shortages threaten the economic recovery",
]

NUMBERS = [
    "NVDA +31.5% MON, -5.2% TUE",
    "700K+ RUSSIAN WAR DEAD",
    "24 DEAD, ~34 MISSING IN SERANG",
    "$44BN CROWDSTRIKE DEAL",
    "14 NATIONS BACK ICJ RULING",
]

REGION_TALLY = ("EUROPE 14", "MIDDLE EAST 7", "ASIA 10", "AFRICA 4",
                "AMERICAS 12", "OCEANIA 1", "WORLD 6")
FIELD_TALLY = ("WAR & SECURITY 18", "POLITICS & DIPLOMACY 20",
               "ECONOMY & MARKETS 4", "TECHNOLOGY 5",
               "DISASTER & HEALTH 5", "SCIENCE & CULTURE 2")

DATE_CHECK = [
    "KEPT OFF BECAUSE FIRST REPORTED BEFORE TUE 24 NOV: THE ICJ 9-6 ROHINGYA RULING ITSELF (19 NOV - ONLY THE 14-NATION",
    "RECOGNITION IS TODAY'S NEWS, CARD 5); NVIDIA'S REINSTATEMENT OF JENSEN HUANG (MON 23 NOV - TUE'S NEWS IS THE -5.2%",
    "PREMARKET WOBBLE, CARD 1); THE MERKURY SINKING ITSELF (ATTACK SUN 22 NOV - TUE'S NEWS IS THE UN PROBE CALL, CARD 2);",
    "THE HORMUZ TANKER STRIKES (23 NOV, NO NEW TUE DEVELOPMENT); THE THREE RUSSIAN MISSILES IN POLAND (FRI 20 NOV - TUE'S",
    "NEWS IS NATO'S AWACS DEPLOYMENT); THE SERANG FIRE BROKE OUT OVER THE WEEKEND OF 22-23 NOV (SEE CARD 6).",
]

SOURCES = "SOURCES: REUTERS, AP, BBC, WSJ, AL JAZEERA, KYIV INDEPENDENT, UN NEWS, MORNINGSTAR, HORIZON, ONETURN, DAILYSUMMARY, IQMIA, 10THINGS, FORAVIA, RFE/RL, ISW."


# ------------------------------------------------------------ card mini-art
def art_nvidia(x, y, w, h):
    base = y + h - 6
    bars = [(GREEN, 12), (GREEN, 22), (GREEN, 36), (RED, 10)]
    bw = (w - 10) // 4
    for i, (c, bh) in enumerate(bars):
        bx = x + 5 + i * bw
        fill_rect(bx, base - bh, bw - 3, bh, c)
    line(x + 4, base - 38, x + w - 6, base - 16, GOLD)


def art_libya(x, y, w, h):
    fill_rect(x, y + h - 16, w, 16, (90, 140, 180))
    fill_rect(x + w // 2 - 22, y + h - 26, 44, 10, INK)
    fill_rect(x + w // 2 - 6, y + h - 40, 3, 14, INK)
    fill_rect(x + w // 2 - 2, y + h - 40, 14, 3, RED)
    for i in range(7):
        dx = x + 8 + i * ((w - 16) // 6)
        circle(dx, y + 8, 2, INK)
    circle(x + w // 2 + 26, y + h - 30, 5, (230, 120, 30))
    circle(x + w // 2 + 26, y + h - 30, 2, GOLD)


def art_space(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    for sx, sy in [(8, 6), (w - 14, 10), (w // 2, 4), (16, h - 8), (w - 24, h - 12)]:
        set_px(x + sx, y + sy, WHITE)
        set_px(x + sx + 1, y + sy, WHITE)
    fill_rect(x + w // 2 - 5, y + h // 2 - 4, 10, 8, (180, 180, 180))
    fill_rect(x + w // 2 - 20, y + h // 2 - 2, 14, 4, BLUE)
    fill_rect(x + w // 2 + 6, y + h // 2 - 2, 14, 4, BLUE)
    line(x + 4, y + h - 6, x + w - 4, y + 8, GOLD)


def art_gaza(x, y, w, h):
    base = y + h - 4
    hs = [14, 22, 17, 26, 20]
    bw = (w - 6) // 5
    for i, bh in enumerate(hs):
        fill_rect(x + 3 + i * bw, base - bh, bw - 2, bh, (70, 66, 58))
    circle(x + w - 16, y + 8, 6, GREY)
    circle(x + w - 26, y + 4, 4, GREY)
    fill_rect(x + 6, y + 6, 4, 4, RED)
    fill_rect(x + 16, y + 2, 4, 4, RED)


def art_icj(x, y, w, h):
    cx = x + w // 2
    vline(cx, y + 4, h - 14, INK, 2)
    hline(cx - 16, y + 6, 32, INK, 2)
    poly_fill([(cx - 20, y + 8), (cx - 12, y + 8), (cx - 16, y + 18)], INK)
    poly_fill([(cx + 12, y + 8), (cx + 20, y + 8), (cx + 16, y + 18)], INK)
    fill_rect(cx - 18, y + 18, 8, 2, INK)
    fill_rect(cx + 10, y + 18, 8, 2, INK)
    for i in range(14):
        fill_rect(x + 4 + i * ((w - 8) // 14), y + h - 6, 3, 5, TEAL)


def art_factory(x, y, w, h):
    base = y + h - 4
    fill_rect(x + 4, base - 22, w - 8, 22, (120, 100, 80))
    for i in range(4):
        poly_fill([(x + 4 + i * ((w - 8) // 4), base - 22),
                   (x + 4 + (i + 1) * ((w - 8) // 4), base - 22),
                   (x + 4 + (i + 1) * ((w - 8) // 4) - 4, base - 26),
                   (x + 4 + i * ((w - 8) // 4) + 4, base - 26)], INK)
    fill_rect(x + w - 12, base - 26, 5, 26, INK)
    poly_fill([(x + w // 2 - 6, base - 20), (x + w // 2, base - 34),
               (x + w // 2 + 6, base - 20)], (230, 120, 30))
    poly_fill([(x + w // 2 - 3, base - 18), (x + w // 2, base - 26),
               (x + w // 2 + 3, base - 18)], GOLD)
    circle(x + w - 12, y + 2, 4, GREY)
    circle(x + w - 18, y + 8, 3, GREY)


def art_visa(x, y, w, h):
    fill_rect(x + w // 2 - 16, y + 3, 32, h - 6, BLUE)
    rect_border(x + w // 2 - 16, y + 3, 32, h - 6, GOLD, 1)
    circle(x + w // 2, y + h // 2 - 2, 7, GOLD)
    draw_text("7", x + w // 2 - 3, y + h // 2 - 5, 1, BLUE)
    for i in range(7):
        dx = x + 6 + i * ((w - 12) // 6)
        circle(dx, y + h - 5, 1, INK)


def art_delta(x, y, w, h):
    fill_rect(x + 3, y + 2, w - 6, h - 8, SKY)
    fill_rect(x + 3, y + h - 6, w - 6, 2, INK)
    for dx, dy in [(10, 8), (w - 16, 10), (w // 2, 14), (16, h - 14), (w - 22, h - 16)]:
        circle(x + dx, y + dy, 2, GREEN)
    line(x + 6, y + h - 10, x + w - 8, y + 6, GREEN)
    draw_text("DELTA", x + w // 2 - 15, y + h // 2 - 3, 1, WHITE)


def art_court(x, y, w, h):
    base = y + h - 4
    poly_fill([(x + 4, base - 20), (x + w - 4, base - 20),
               (x + w // 2, base - 26)], INK)
    for i in range(3):
        fill_rect(x + 10 + i * ((w - 20) // 3), base - 24, 4, 24, INK)
    fill_rect(x + 4, base - 2, w - 8, 2, INK)
    circle(x + w // 2 - 12, y + 2, 2, INK)
    circle(x + w // 2 + 12, y + 2, 2, INK)
    line(x + w // 2 - 12, y + 2, x + w // 2 + 12, y + 2, INK)


def art_tiangong(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    fill_rect(x + w // 2 - 4, y + h // 2 - 8, 8, 16, (200, 200, 200))
    fill_rect(x + 6, y + h // 2 - 4, 16, 8, BLUE)
    fill_rect(x + w - 22, y + h // 2 - 4, 16, 8, BLUE)
    for r in (5, 9, 13):
        circle(x + w - 12, y + 15, r, GOLD, fill=False)
    draw_text("6G", x + 6, y + 4, 1, WHITE)


def art_cop(x, y, w, h):
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 2
    circle(cx, cy, r, (90, 140, 180))
    circle(cx, cy, r, INK, fill=False)
    line(cx - r, cy, cx + r, cy, INK)
    line(cx, cy - r, cx, cy + r, INK)
    line(cx - r + 4, cy - r + 6, cx + 2, cy + 2, RED)
    line(cx + 2, cy + 2, cx - 2, cy + r - 4, RED)
    line(cx - r + 2, cy + r - 2, cx + r - 2, cy - r + 2, (200, 60, 40))


def art_ai(x, y, w, h):
    cx = x + w // 2
    fill_rect(cx - 12, y + 8, 24, 18, (200, 200, 200))
    rect_border(cx - 12, y + 8, 24, 18, INK, 1)
    fill_rect(cx - 5, y + 14, 4, 4, BLUE)
    fill_rect(cx + 1, y + 14, 4, 4, BLUE)
    vline(cx, y + 2, 6, INK, 2)
    circle(cx, y + 2, 2, RED)
    line(cx - 12, y + 26, x + 4, y + h - 4, TEAL)
    line(cx + 12, y + 26, x + w - 4, y + h - 4, TEAL)
    circle(x + 4, y + h - 4, 3, TEAL)
    circle(x + w - 4, y + h - 4, 3, TEAL)


def art_rally(x, y, w, h):
    base = y + h - 6
    hs = [8, 14, 20]
    bw = (w - 12) // 3
    for i, bh in enumerate(hs):
        bx = x + 6 + i * bw
        fill_rect(bx, base - bh, bw - 4, bh, GREEN)
        vline(bx + (bw - 4) // 2, base - bh - 3, 3, INK, 1)
        vline(bx + (bw - 4) // 2, base, 3, INK, 1)
    line(x + 4, base - 18, x + w - 6, base - 24, GOLD)


ART = {"nvidia": art_nvidia, "libya": art_libya, "space": art_space,
       "gaza": art_gaza, "icj": art_icj, "factory": art_factory,
       "visa": art_visa, "delta": art_delta, "court": art_court,
       "tiangong": art_tiangong, "cop": art_cop, "ai": art_ai,
       "rally": art_rally}

# ------------------------------------------------------------------- layout
MARGIN = 12
CW = W - 2 * MARGIN  # 1000


def draw_card(card, x, y, w, h):
    color = REGION_COLOR[card["region"]]
    fill_rect(x, y, w, h, PAPER2)
    rect_border(x, y, w, h, LINE, 1)
    fill_rect(x, y, w, 4, color)
    pad = 7
    ix = x + pad
    iw = w - 2 * pad
    cy = y + 9
    draw_text(str(card["num"]), ix, cy, 1, color)
    draw_text(card["kicker"], ix + 12, cy, 1, color)
    cy += 11
    head_lines = wrap_text(card["headline"], iw // 12)
    for hl in head_lines:
        draw_text(hl, ix, cy, 2, INK)
        cy += 15
    cy += 2
    art_h = 30 if h <= 150 else 44
    ART[card["art"]](ix, cy, iw, art_h)
    cy += art_h + 4
    body_lines = wrap_text(card["body"], iw // 6)
    for bl in body_lines:
        draw_text(bl.upper(), ix, cy, 1, INK)
        cy += 9
    strip_y = y + h - 13
    fill_rect(x + 1, strip_y - 2, w - 2, 14, color)
    draw_text_centered(card["strip"], x + w // 2, strip_y, 1, WHITE)


# Simplified world continents as (lon, lat) polygons.
CONTINENTS = [
    [(-168, 65), (-150, 70), (-130, 71), (-115, 68), (-100, 68), (-90, 62),
     (-82, 66), (-76, 62), (-70, 58), (-65, 49), (-75, 35), (-80, 26),
     (-85, 15), (-90, 14), (-97, 16), (-105, 20), (-115, 28), (-125, 40),
     (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-55, 60), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-30, 74),
     (-45, 76), (-58, 74), (-60, 70)],
    [(-80, 10), (-75, 5), (-70, 0), (-60, -5), (-50, -5), (-40, -10),
     (-35, -15), (-40, -25), (-50, -30), (-60, -35), (-70, -40), (-70, -50),
     (-72, -54), (-75, -40), (-75, -25), (-80, -15), (-80, -5)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (48, 11), (51, 10), (45, 0), (40, -10), (35, -20), (30, -30),
     (20, -35), (15, -30), (12, -18), (10, -5), (8, 4), (0, 5), (-8, 5),
     (-13, 10)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (25, 65), (20, 70),
     (15, 70), (10, 62), (5, 60), (0, 55), (-5, 50), (-10, 44)],
    [(30, 62), (40, 68), (55, 68), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (162, 58), (155, 52),
     (145, 45), (140, 40), (135, 35), (130, 33), (127, 30), (122, 30),
     (120, 25), (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20),
     (80, 15), (75, 10), (72, 20), (66, 25), (60, 25), (55, 26), (50, 29),
     (48, 30), (45, 30), (40, 32), (35, 36), (30, 36)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -8), (130, -3), (135, 0), (140, -2), (145, -5), (140, -8),
     (130, -10), (120, -12), (110, -8), (100, -2)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (150, -25),
     (146, -20), (142, -15), (140, -12), (135, -12), (130, -13), (125, -15),
     (120, -20), (114, -22)],
]

# (card num, lon, lat, pin display position lon, lat) -- display positions
# are nudged apart with hairlines where Europe / the Middle East crowd.
PINS = [
    (1, -98, 39, -98, 39),
    (2, 20, 32, 12, 26),
    (3, 37, 55, 52, 58),
    (4, 34.5, 31.4, 44, 24),
    (5, 96, 20, 96, 20),
    (6, 106, -6, 106, -6),
    (7, 10, 52, -2, 56),
    (8, 10, 51, 18, 56),
    (9, -107, 25, -107, 25),
    (10, 116, 39, 116, 39),
    (11, 33, 39, 22, 44),
    (12, -59, 13, -59, 13),
    (13, 132, 36, 142, 40),
]


def draw_map(mx, my, mw, mh):
    fill_rect(mx, my, mw, mh, OCEAN)
    rect_border(mx, my, mw, mh, LINE, 1)

    def px(lon, lat):
        return (mx + int((lon + 180) / 360 * mw),
                my + int((75 - lat) / 130 * mh))

    for lon in (-120, -60, 0, 60, 120):
        gx, _ = px(lon, 0)
        for gy in range(my, my + mh, 4):
            set_px(gx, gy, (190, 205, 215))
    for cont in CONTINENTS:
        pts = [px(lon, lat) for lon, lat in cont]
        poly_fill(pts, LAND)
        poly_line(pts, LAND_LINE)
    for num, lon, lat, dlon, dlat in PINS:
        card = CARDS[num - 1]
        color = REGION_COLOR[card["region"]]
        tx, ty = px(lon, lat)
        dx, dy = px(dlon, dlat)
        if (dx, dy) != (tx, ty):
            line(tx, ty, dx, dy, INK)
        r = 8
        circle(dx, dy, r, color)
        circle(dx, dy, r, INK, fill=False)
        label = str(num)
        draw_text(label, dx - text_w(label, 1) // 2, dy - 3, 1, WHITE)
    # legend
    ly = my + mh + 6
    lx = mx + 2
    for name in ("EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS", "WORLD"):
        c = REGION_COLOR[name]
        fill_rect(lx, ly, 8, 8, c)
        lx += 11
        draw_text(name, lx, ly + 1, 1, INK)
        lx += text_w(name, 1) + 10


def main():
    fill_rect(0, 0, W, H, CREAM)
    # --- masthead
    y = 10
    draw_text_centered("THE WORLD TODAY", W // 2, y, 5, INK)
    y += 38
    hline(MARGIN, y, CW, INK, 2)
    y += 5
    draw_text_centered(
        "TUESDAY, 24 NOVEMBER 2026 - 54 STORIES - 7 REGIONS - 13 ILLUSTRATED",
        W // 2, y, 2, INK)
    y += 17
    hline(MARGIN, y, CW, INK, 1)
    # --- tally strips
    y += 6
    fill_rect(MARGIN, y, CW, 16, INK)
    draw_text("BY REGION", MARGIN + 6, y + 5, 1, GOLD)
    draw_text("  ".join(REGION_TALLY), MARGIN + 66, y + 5, 1, WHITE)
    y += 18
    fill_rect(MARGIN, y, CW, 16, (52, 50, 44))
    draw_text("BY FIELD", MARGIN + 6, y + 5, 1, GOLD)
    draw_text("  ".join(FIELD_TALLY), MARGIN + 66, y + 5, 1, WHITE)
    y += 18
    # --- day in numbers
    draw_text("THE DAY IN NUMBERS:", MARGIN, y + 5, 1, RED)
    draw_text(" | ".join(NUMBERS), MARGIN + 124, y + 5, 1, INK)
    hline(MARGIN, y + 17, CW, INK, 1)
    y += 24
    # --- cards row 1: 3 big
    row1_y, row1_h = y, 165
    cw3 = (CW - 16) // 3
    for i in range(3):
        draw_card(CARDS[i], MARGIN + i * (cw3 + 8), row1_y, cw3, row1_h)
    y = row1_y + row1_h + 8
    # --- cards row 2: 5
    row2_y, row2_h = y, 155
    cw5 = (CW - 32) // 5
    for i in range(5):
        draw_card(CARDS[3 + i], MARGIN + i * (cw5 + 8), row2_y, cw5, row2_h)
    y = row2_y + row2_h + 8
    # --- cards row 3: 5
    row3_y, row3_h = y, 155
    for i in range(5):
        draw_card(CARDS[8 + i], MARGIN + i * (cw5 + 8), row3_y, cw5, row3_h)
    y = row3_y + row3_h + 8
    # --- bottom band headers
    draw_text("WHERE IT HAPPENED", MARGIN, y, 1, INK)
    draw_text("THE REST OF THE DAY - 41 MORE STORIES",
              MARGIN + 478, y, 1, INK)
    hline(MARGIN, y + 10, CW, INK, 1)
    y += 14
    # --- map (left) + briefs (right)
    map_x, map_y, map_w, map_h = MARGIN, y, 466, 262
    draw_map(map_x, map_y, map_w, map_h)
    bx = MARGIN + 478
    by = y
    for i, brief in enumerate(BRIEFS):
        draw_text(str(14 + i) + ".", bx, by, 1, RED)
        draw_text(brief.upper(), bx + 24, by, 1, INK)
        by += 7
    # --- date check box
    dy = 944
    fill_rect(MARGIN, dy, CW, 56, PAPER2)
    rect_border(MARGIN, dy, CW, 56, RED, 1)
    draw_text("DATE CHECK - WHY SOME BIG STORIES ARE NOT ON THIS PAGE",
              MARGIN + 6, dy + 4, 1, RED)
    for i, dline in enumerate(DATE_CHECK):
        draw_text(dline, MARGIN + 6, dy + 15 + i * 8, 1, INK)
    # --- sources footer
    draw_text(SOURCES, MARGIN, 1006, 1, GREY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), W, H, PIX)


if __name__ == "__main__":
    main()
