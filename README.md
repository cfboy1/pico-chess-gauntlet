# pico-chess-gauntlet

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/cfboy1/pico-chess-gauntlet/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/cfboy1/pico-chess-gauntlet/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess engine in under 4 KB of Python that plays make.fun's eight-engine gauntlet over HTTP: negamax alpha-beta with a transposition table, killer moves, quiescence with check evasions, null-move pruning and a phase-interpolated piece-square evaluation. Every move is derived from the position and the game's move history under a fixed node budget, so a trial replays byte for byte.

## Run it

```sh
python3 main.py  # plays the gauntlet at $MAKEFUN_ENV_URL (POST /game, /move)
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=dpty14jr&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
