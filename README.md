# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/sun-justin/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/sun-justin/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A program that draws a newspaper front page summing up the world news of Wednesday 25 November 2026 (1024x1024 PNG).

## What it draws

**THE WORLD TODAY — Wednesday 25 November 2026**: 37 dated stories across 9 regions:

- Lead: two oil tankers strike naval mines and catch fire in the
  Strait of Hormuz; Iran's Revolutionary Guards say the vessels
  used an unauthorised route.
- Pakistan's first astronaut, Muhammad Zeeshan Ali, reaches orbit
  aboard Shenzhou-24 and docks with Tiangong three and a half hours
  after launch; the crew will run 90 experiments.
- A Brooklyn jury convicts Huawei on 10 of 12 counts — bank fraud,
  wire fraud, sanctions violations and trade-secret theft — after
  a trial of more than two months.
- Briefs: Asian chip stocks rout the KOSPI 6.16% and the Nikkei
  2.78%; the Dow closes above 50,000 for the first time (50,018.70);
  90 nations reject the COP31 draft; Houthis hit Ras Tanura and a
  Riyadh tower; RSF drone strikes kill 19 civilians in Sudan;
  Colombia frees all supermarket hostages; Real Madrid thrash PSV 5-1.
- A stats strip (37 stories, 9 regions, KOSPI -6.16%, 2 tankers mined,
  490,334 Russian war dead, 90 nations reject the COP31 draft), a
  markets strip (KOSPI -6.16%, Nikkei -2.78%, Dow +0.85%, S&P 500
  -0.50%, Nasdaq -1.48%, gold $3,524, Brent $87.43, Bitcoin $59,000)
  and a world map marking 14 places.

## How it works

`main.py` is pure Python 3 standard library. It draws every pixel itself —
a hand-built 5x7 bitmap font, gradient skies, shaded illustrations, a world
map, paper grain and a hand-written PNG encoder (`zlib` + `struct`) — with
no network, no clock and no randomness, so two runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The image is written to `out/entry.png` (1024x1024, under 1 MiB).
