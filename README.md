<p align="center">
  <h1 align="center">📦 pipdash</h1>
  <p align="center">PyPI package download stats and metadata — right in your terminal.</p>

<p align="center">
  <a href="https://pypi.org/project/pipdash/">
    <img src="https://img.shields.io/pypi/v/pipdash?style=for-the-badge" alt="PyPI Version">
  </a>
<a href="https://github.com/bevinkatti/pipdash">
  <img src="https://img.shields.io/github/stars/bevinkatti/pipdash?style=for-the-badge&logo=github" alt="GitHub Stars">
</a>
  <a href="https://pypi.org/project/pipdash/">
    <img src="https://img.shields.io/pypi/pyversions/pipdash?style=for-the-badge" alt="Python Versions">
  </a>
  <a href="https://github.com/bevinkatti/pipdash/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/bevinkatti/pipdash?style=for-the-badge" alt="License">
  </a>
</p>
---

No browser. No login. No config. One command.

```bash
pipdash stats requests
```
```
📦 requests  v2.34.2
   Python HTTP for Humans.
──────────────────────────────────────────────────
  Last 24 hours      9.80k
  Last 7 days        65.00k
  Last 30 days       271.00k
  Last 90 days       813.00k
  Last 180 days      1.63M
──────────────────────────────────────────────────
  ⬇  All-time Downloads   5.20M
──────────────────────────────────────────────────

  Python Versions
    3.12     ████████░░░░  41%
    3.11     ████████░░░░  28%
    3.10     ██████░░░░░░  18%
    3.9      ████░░░░░░░░   8%

  Platforms
    Linux    ████████░░░░  62%
    Windows  ██████░░░░░░  22%
    macOS    ████░░░░░░░░  14%

──────────────────────────────────────────────────
  License          MIT
  Requires Python  >=3.10
  Total Versions   163
  First Released   2011-02-14
  Latest Release   v2.34.2  (2026-05-14)
  Repository       https://github.com/<owner>/<repo>
```

---

## Install

```bash
pip install pipdash
```

## Commands

### `pipdash stats <package-name>`
Full download statistics + metadata. Pepy is used where its public badge API exposes the same metric; PyPI Stats fills the remaining periods.

```bash
pipdash stats numpy
pipdash stats django --json      # JSON output for scripting
pipdash stats rag-harness --zerotraffic
```

### `--zerotraffic`
Use one consistent PyPI Stats view for every download period. It excludes known mirror downloads and never inserts estimates. Periods unavailable because the package is too new are omitted.

### `pipdash info <package>`
Package metadata, dependencies, and links — no download API call needed.

```bash
pipdash info flask
pipdash info fastapi --json
```

### `pipdash compare <pkg1> <pkg2> ...`
Side-by-side stats comparison of multiple packages.

```bash
pipdash compare requests httpx aiohttp
pipdash compare django flask fastapi
```

### Flags
| Flag | Description |
|------|-------------|
| `--json` | Output raw JSON (works with all commands) |
| `--help` | Show help |
| `--version` | Show version |

---

## Data sources

| Source | Data |
|--------|------|
| [pypi.org](https://pypi.org) | Package metadata, versions, release dates |
| [pypistats.org](https://pypistats.org) | 24h, rolling periods, Python version, OS, and the zero-traffic view |
| [pepy.tech](https://pepy.tech) | All-time, 7-day, and 30-day counts via public badges |

No API key required. No sign-up. Completely free.

> Note: Pepy’s public badge endpoints provide exact total, weekly, and monthly counts without an API key. PyPI Stats excludes known mirror downloads and is used for the remaining periods and the `-zerotraffic` mode. Pepy’s richer project API requires an API key, so pipdash does not depend on one.

---

## Why pipdash?

- Uses Pepy where its public badges expose the same metric, while keeping the rest of the period history available from PyPI Stats
- PyPI's own API gives no useful download stats
- pypistats.org has an API but no nice CLI
- `pipdash` wraps both into one clean command

---

## Contributing

```bash
git clone https://github.com/bevinkatti/pipdash.git
cd pipdash
pip install -e ".[dev]"
```

Issues and PRs welcome.

## License

MIT © [Abhishek Bevinkatti](https://github.com/bevinkatti)
