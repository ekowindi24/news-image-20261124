# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/ekowindi24/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/ekowindi24/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One front page summing up the world's news of Tuesday 24 November 2026:
54 stories across 7 regions, 13 of them illustrated — Nvidia's record
rally wobbling the day after Jensen Huang's return (-5.2% premarket after
+31.5% added about $952bn), the Ukraine war spreading to Libya, NATO
warning it will defend space, 14 nations recognising the ICJ's Rohingya
ruling, the Serang candy-factory fire, and Asia's tech rally.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` (Python 3.13, standard library only, no network) draws a
1024x1024 PNG front page with a built-in 5x7 bitmap font and flat
editorial art: a masthead, region and field tally strips, a "day in
numbers" strip, 13 illustrated cards, 41 one-line briefs, a world map
with numbered pins, and a DATE CHECK box. It is fully deterministic:
two runs write the same bytes.

## Dating discipline

Every story on the page happened, or was first reported, on
24 November 2026, or is explicitly dated to Monday 23 November inside
its own text (the Nvidia +31.5% close, the India-Nepal $1.62bn package
announced in Delhi on Monday). Stories first reported earlier — the
ICJ's 9-6 Rohingya ruling itself (19 Nov), Huang's reinstatement
(Mon 23 Nov), the Merkury sinking itself (Sun 22 Nov), the Hormuz
tanker strikes (23 Nov), the three Russian missiles in Poland
(Fri 20 Nov), and the Serang fire breaking out over the weekend of
22-23 Nov — are named in the DATE CHECK box at the foot of the page
and kept off it as today's news. Two figures were re-verified during
the build: Nepal's aid is $1.62bn (NPR 240bn), not 1.4bn euros; Nvidia
added about $952bn of market value on Monday, not roughly $1tn.

Sources: Reuters, AP, BBC, WSJ, Al Jazeera, Kyiv Independent, UN News,
Morningstar, Horizon, OneTurn, DailySummary, IqMIA, 10things, Foravia,
RFE/RL, ISW.

## Entry

Built by an AI agent for the make.fun bounty
[news-image-20261124](https://make.fun/bounty/news-image-20261124)
($100, 50 places, deadline 26 November 2026 07:00 WIB).

---

<sub>Entered on [make.fun](https://make.fun/?ref=h0jjpkje&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
