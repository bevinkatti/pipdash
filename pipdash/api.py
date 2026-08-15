"""
pipdash.api
Fetches package metadata and download statistics from PyPI, PyPI Stats,
and Pepy.tech's public badge endpoints.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

__version__ = "1.1.0"
HEADERS = {"User-Agent": f"pipdash/{__version__} (github.com/bevinkatti/pipdash)"}

PYPI_URL      = "https://pypi.org/pypi/{package}/json"
STATS_OVERALL = "https://pypistats.org/api/packages/{package}/overall"
STATS_RECENT  = "https://pypistats.org/api/packages/{package}/recent"
STATS_PYTHON  = "https://pypistats.org/api/packages/{package}/python_major"
STATS_SYSTEM  = "https://pypistats.org/api/packages/{package}/system"
PEPY_BADGE    = "https://api.pepy.tech/personalized-badge/{package}"


def _get(url: str) -> dict:
    r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _get_pepy_badge(package: str, period: str) -> Optional[int]:
    """Fetch an exact public Pepy badge count for TOTAL, WEEK, or MONTH.

    Pepy's public badge endpoints do not require an API key. We request the
    raw integer form so the CLI can display exact counts rather than the
    abbreviated badge value.
    """
    try:
        response = httpx.get(
            PEPY_BADGE.format(package=package),
            params={
                "period": period,
                "units": "NONE",
                "left_text": "downloads",
            },
            headers=HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        response.raise_for_status()
        values = [
            re.sub(r"<[^>]+>", "", node).strip()
            for node in re.findall(r"<text[^>]*>(.*?)</text>", response.text, flags=re.DOTALL)
        ]
        numeric = [value for value in values if re.fullmatch(r"[\d,]+", value)]
        return int(numeric[-1].replace(",", "")) if numeric else None
    except (httpx.HTTPError, ValueError):
        return None


def fmt_num(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def fmt_pepy_num(n: int) -> str:
    """Format a Pepy-style count (for example, 2.35k)."""
    if n >= 1_000_000_000_000:
        return f"{n / 1_000_000_000_000:.2f}T"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}G"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.2f}k"
    return f"{n:,}"


def _pct_breakdown(rows: list, key: str, top: int = 4) -> dict:
    filtered = [r for r in rows if r.get("category") == "without_mirrors" and r.get(key)]
    total = sum(r["downloads"] for r in filtered) or 1
    return {
        r[key]: round(r["downloads"] / total * 100)
        for r in sorted(filtered, key=lambda x: -x["downloads"])[:top]
    }


def _days_since(date_str: str) -> int:
    if not date_str:
        return 0
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 0


def _without_mirrors(rows):
    """PyPI Stats' default clean series: excludes known mirror downloads."""
    return [r for r in rows if r.get("category") == "without_mirrors"]


def _rolling_days(daily_rows: list, days: int) -> Optional[int]:
    """Return an exact rolling total only when the entire window exists."""
    daily_by_date = {
        r.get("date"): int(r.get("downloads", 0))
        for r in daily_rows
        if r.get("date")
    }
    latest_date = max(daily_by_date) if daily_by_date else None
    if not latest_date:
        return None

    latest = datetime.fromisoformat(latest_date)
    earliest_needed = latest - timedelta(days=days - 1)
    expected_dates = [
        (earliest_needed + timedelta(days=i)).date().isoformat()
        for i in range(days)
    ]
    if not all(date in daily_by_date for date in expected_dates):
        return None
    return sum(daily_by_date[date] for date in expected_dates)


def get_stats(package: str, zero_traffic: bool = False) -> dict:
    """Fetch full package stats.

    Default mode is Pepy-aligned where Pepy exposes a public badge:
    - all-time: Pepy TOTAL
    - 7d: Pepy WEEK
    - 30d: Pepy MONTH
    - 24h / 90d / 180d: PyPI Stats (no public Pepy badge for these periods)

    ``zero_traffic=True`` uses PyPI Stats consistently for every download
    period. PyPI Stats excludes known mirrors; it does not mean CI traffic is
    removed.
    """
    package = package.strip().lower()

    # ── PyPI metadata ────────────────────────────────────────────────────────
    pypi = _get(PYPI_URL.format(package=package))
    info = pypi["info"]
    releases = pypi.get("releases", {})

    latest = info["version"]
    files = releases.get(latest, [])
    release_date = files[0]["upload_time"][:10] if files else ""
    days_old = _days_since(files[0]["upload_time"] if files else "")

    author = (info.get("author") or info.get("maintainer") or "").strip() or "N/A"
    license_ = (info.get("license_expression") or info.get("license") or "").strip() or "N/A"
    summary = info.get("summary", "").strip()
    home = (
        (info.get("project_urls") or {}).get("Source")
        or (info.get("project_urls") or {}).get("Repository")
        or (info.get("project_urls") or {}).get("Homepage")
        or info.get("home_page")
        or ""
    ).strip()
    requires_python = info.get("requires_python") or ""
    total_versions = len([v for v, f in releases.items() if f])

    all_dates = []
    for _ver, flist in releases.items():
        if flist:
            all_dates.append(flist[0].get("upload_time", ""))
    first_release = sorted(all_dates)[0][:10] if all_dates else ""

    # ── PyPI Stats ──────────────────────────────────────────────────────────
    overall = _get(STATS_OVERALL.format(package=package))
    recent = _get(STATS_RECENT.format(package=package))
    python = _get(STATS_PYTHON.format(package=package))
    system = _get(STATS_SYSTEM.format(package=package))

    daily_rows = _without_mirrors(overall["data"])
    pypistats_all_time = sum(r["downloads"] for r in daily_rows)

    # PyPI Stats' recent endpoint is already mirror-excluded per its API docs.
    pypi_day = int(recent["data"].get("last_day", 0))
    pypi_week = int(recent["data"].get("last_week", 0))
    pypi_month = int(recent["data"].get("last_month", 0))
    pypi_90d = _rolling_days(daily_rows, 90)
    pypi_180d = _rolling_days(daily_rows, 180)

    if zero_traffic:
        # Consistent PyPI Stats / known-mirror-excluded view.
        all_time_raw = pypistats_all_time
        last_day_raw = pypi_day
        last_week_raw = pypi_week
        last_month_raw = pypi_month
        last_90d_raw = pypi_90d
        last_180d_raw = pypi_180d
        stats_source = "pypistats.org (without known mirrors)"
        all_time_source = stats_source
        all_time_formatted = fmt_num(all_time_raw)
    else:
        # Pepy's public badge endpoints are the closest match to the Pepy UI
        # without requiring users to configure an API key.
        pepy_total = _get_pepy_badge(package, "TOTAL")
        pepy_week = _get_pepy_badge(package, "WEEK")
        pepy_month = _get_pepy_badge(package, "MONTH")

        all_time_raw = pepy_total if pepy_total is not None else pypistats_all_time
        last_day_raw = pypi_day
        last_week_raw = pepy_week if pepy_week is not None else pypi_week
        last_month_raw = pepy_month if pepy_month is not None else pypi_month
        last_90d_raw = pypi_90d
        last_180d_raw = pypi_180d

        all_time_source = "pepy.tech" if pepy_total is not None else "pypistats.org (fallback)"
        stats_source = "Pepy + PyPI Stats"
        all_time_formatted = fmt_pepy_num(all_time_raw) if pepy_total is not None else fmt_num(all_time_raw)

    py_pcts = _pct_breakdown(python["data"], "python_version", top=5)
    os_pcts = _pct_breakdown(system["data"], "system", top=4)

    return {
        "name": info["name"],
        "version": latest,
        "summary": summary,
        "author": author,
        "license": license_,
        "release_date": release_date,
        "days_old": days_old,
        "first_release": first_release,
        "total_versions": total_versions,
        "home": home,
        "requires_python": requires_python,
        "all_time_raw": all_time_raw,
        "all_time_source": all_time_source,
        "stats_source": stats_source,
        "zero_traffic": zero_traffic,
        "last_day_raw": last_day_raw,
        "last_week_raw": last_week_raw,
        "last_month_raw": last_month_raw,
        "last_90d_raw": last_90d_raw,
        "last_180d_raw": last_180d_raw,
        "all_time": all_time_formatted,
        "last_day": fmt_num(last_day_raw),
        "last_week": fmt_num(last_week_raw),
        "last_month": fmt_num(last_month_raw),
        "last_90d": fmt_num(last_90d_raw) if last_90d_raw is not None else None,
        "last_180d": fmt_num(last_180d_raw) if last_180d_raw is not None else None,
        "py_pcts": py_pcts,
        "os_pcts": os_pcts,
    }


def get_info(package: str) -> dict:
    """Lightweight: only metadata, no download API call needed."""
    package = package.strip().lower()
    pypi = _get(PYPI_URL.format(package=package))
    info = pypi["info"]
    releases = pypi.get("releases", {})

    latest = info["version"]
    files = releases.get(latest, [])
    release_date = files[0]["upload_time"][:10] if files else ""

    all_dates = []
    for _ver, flist in releases.items():
        if flist:
            all_dates.append(flist[0].get("upload_time", ""))
    first_release = sorted(all_dates)[0][:10] if all_dates else ""

    author = (info.get("author") or info.get("maintainer") or "").strip() or "N/A"
    license_ = (info.get("license_expression") or info.get("license") or "").strip() or "N/A"

    return {
        "name": info["name"],
        "version": latest,
        "summary": (info.get("summary") or "").strip(),
        "author": author,
        "license": license_,
        "requires_python": info.get("requires_python") or "",
        "total_versions": len([v for v, f in releases.items() if f]),
        "first_release": first_release,
        "release_date": release_date,
        "home": (
            (info.get("project_urls") or {}).get("Source")
            or (info.get("project_urls") or {}).get("Repository")
            or (info.get("project_urls") or {}).get("Homepage")
            or info.get("home_page")
            or ""
        ).strip(),
        "project_urls": info.get("project_urls") or {},
        "topics": info.get("classifiers") or [],
        "requires_dist": info.get("requires_dist") or [],
    }
