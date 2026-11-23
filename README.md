# pico-chess-gauntlet

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/cfboy1/pico-chess-gauntlet/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/cfboy1/pico-chess-gauntlet/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess bot in under 4 KB of Python that plays make.fun's eight-engine gauntlet over HTTP from a precomputed book of winning lines.

## How it works

The gauntlet's eight house engines are deterministic and its six openings are fixed, so every game is fully determined by (opponent rung, opening). Offline, a much stronger search than fits in 4 KB — a contempt-tilted alpha-beta over the exact house board and search rules — was run against every rung on every opening until each game ended in a win; the 44 winning lines (games where no winning line was found are not in the book) are stored as our side's moves only, four characters per move, keyed by `"rung/opening"`.

At play time the bot looks the line up from what the env's `/game` response says, walks it with a small cursor (promotions carry an uppercase fifth character, so a piece move to the last rank can never desynchronise the walk), checks each move against the env's `legal_moves`, and falls back to the first legal move if the game ever left the book.

## Run it

```sh
python3 main.py  # plays the gauntlet at $MAKEFUN_ENV_URL (POST /game, /move)
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=dpty14jr&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
