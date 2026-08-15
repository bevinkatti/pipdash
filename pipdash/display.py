"""
pipdash.display
Rich terminal rendering for pipdash output.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.padding import Padding
import json as _json

console = Console()

CYAN   = "bold cyan"
YELLOW = "bold yellow"
GREEN  = "bold green"
DIM    = "dim"
WHITE  = "bold white"
RED    = "bold red"


def _bar(pct: int, width: int = 12) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def show_stats(d: dict) -> None:
    c = console

    # ── Header ────────────────────────────────────────────────────────────────
    c.print()
    header = Text()
    header.append("📦 ", style="")
    header.append(d["name"], style=CYAN)
    header.append(f"  v{d['version']}", style=DIM)
    if d.get("summary"):
        header.append(f"\n   {d['summary']}", style=DIM)
    c.print(header)
    c.print("─" * 50, style=DIM)

    # ── Download stats ─────────────────────────────────────────────────────────
    periods = [
        ("Last 24 hours", d.get("last_day")),
        ("Last 7 days", d.get("last_week")),
        ("Last 30 days", d.get("last_month")),
        ("Last 90 days", d.get("last_90d")),
        ("Last 180 days", d.get("last_180d")),
    ]
    for label, value in periods:
        if value is not None:
            c.print(f"  [bold]{label:<20}[/bold] {value}")

    # ── All-time (highlighted) ─────────────────────────────────────────────────
    c.print("─" * 50, style=DIM)
    all_time_text = Text()
    all_time_text.append("  ⬇  All-time Downloads   ", style="bold white")
    all_time_text.append(d["all_time"], style="bold yellow")
    c.print(all_time_text)
    c.print("─" * 50, style=DIM)

    # ── Python version breakdown ───────────────────────────────────────────────
    if d.get("py_pcts"):
        c.print(f"\n  [bold]Python Versions[/bold]")
        for ver, pct in d["py_pcts"].items():
            bar = _bar(pct)
            c.print(f"    [cyan]{ver:<8}[/cyan] {bar} {pct}%")

    # ── OS breakdown ──────────────────────────────────────────────────────────
    if d.get("os_pcts"):
        c.print(f"\n  [bold]Platforms[/bold]")
        for os_name, pct in d["os_pcts"].items():
            bar = _bar(pct)
            c.print(f"    [cyan]{os_name:<8}[/cyan] {bar} {pct}%")

    # ── Metadata ──────────────────────────────────────────────────────────────
    c.print()
    c.print("─" * 50, style=DIM)
    if d.get("author") and d["author"] != "N/A":
        c.print(f"  [bold]Author[/bold]          {d['author']}")
    c.print(f"  [bold]License[/bold]         {d['license']}")
    if d.get("requires_python"):
        c.print(f"  [bold]Requires Python[/bold] {d['requires_python']}")
    c.print(f"  [bold]Total Versions[/bold]  {d['total_versions']}")
    if d.get("first_release"):
        c.print(f"  [bold]First Released[/bold]  {d['first_release']}")
    c.print(f"  [bold]Latest Release[/bold]  v{d['version']}  ({d['release_date']})")
    if d.get("home"):
        c.print(f"  [bold]Repository[/bold]      [link={d['home']}]{d['home']}[/link]")
    c.print()


def show_info(d: dict) -> None:
    c = console
    c.print()
    header = Text()
    header.append("📦 ", style="")
    header.append(d["name"], style=CYAN)
    header.append(f"  v{d['version']}", style=DIM)
    c.print(header)
    if d.get("summary"):
        c.print(f"   [dim]{d['summary']}[/dim]")
    c.print("─" * 50, style=DIM)

    rows = [
        ("Author",          d.get("author", "N/A")),
        ("License",         d.get("license", "N/A")),
        ("Requires Python", d.get("requires_python") or "any"),
        ("Versions",        str(d.get("total_versions", ""))),
        ("First Released",  d.get("first_release", "")),
        ("Latest Release",  f"v{d['version']}  ({d.get('release_date', '')})"),
    ]
    for label, value in rows:
        if value:
            c.print(f"  [bold]{label:<20}[/bold] {value}")

    if d.get("home"):
        c.print(f"  [bold]{'Repository':<20}[/bold] [link={d['home']}]{d['home']}[/link]")

    urls = d.get("project_urls", {})
    for key in ("Documentation", "Changelog", "Bug Tracker"):
        if key in urls:
            c.print(f"  [bold]{key:<20}[/bold] [link={urls[key]}]{urls[key]}[/link]")

    if d.get("topics"):
        c.print(f"\n  [bold]Topics[/bold]")
        for t in d["topics"]:
            c.print(f"    • {t}")

    deps = d.get("requires_dist") or []
    if deps:
        c.print(f"\n  [bold]Dependencies[/bold]  ({len(deps)} packages)")
        for dep in deps[:8]:
            c.print(f"    • [dim]{dep}[/dim]")
        if len(deps) > 8:
            c.print(f"    [dim]... and {len(deps) - 8} more[/dim]")
    c.print()


def show_compare(packages: list[dict]) -> None:
    c = console
    c.print()
    c.print("[bold]📊 Package Comparison[/bold]")
    c.print("─" * 60, style=DIM)

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0, 2))
    table.add_column("Metric", style="bold", no_wrap=True)
    for d in packages:
        table.add_column(f"{d['name']}\nv{d['version']}", justify="right")

    metrics = [
        ("Last 24h",       "last_day"),
        ("Last 7 days",    "last_week"),
        ("Last 30 days",   "last_month"),
        ("Last 90 days",   "last_90d"),
        ("Last 180 days",  "last_180d"),
        ("All-time ⬇",     "all_time"),
        ("License",        "license"),
        ("Requires Python","requires_python"),
        ("Versions",       "total_versions"),
        ("First Released", "first_release"),
        ("Latest",         "release_date"),
    ]

    for label, key in metrics:
        row = [label]
        values = [str(d.get(key)) if d.get(key) is not None else "—" for d in packages]
        # Highlight the highest numeric value in download rows
        if key in ("last_day_raw", "last_week_raw", "last_month_raw", "last_90d_raw", "last_180d_raw", "all_time_raw"):
            pass  # raw not shown
        for i, (d, val) in enumerate(zip(packages, values)):
            raw_key = key + "_raw"
            row.append(val)
        table.add_row(*row)

    c.print(table)
    c.print()


def show_json(data) -> None:
    """Print data as pretty JSON."""
    # Remove _raw fields for cleaner output
    if isinstance(data, dict):
        clean = {k: v for k, v in data.items() if not k.endswith("_raw")}
    elif isinstance(data, list):
        clean = [{k: v for k, v in d.items() if not k.endswith("_raw")} for d in data]
    else:
        clean = data
    console.print_json(_json.dumps(clean, indent=2, default=str))
