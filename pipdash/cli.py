"""
pipdash.cli
Command-line interface for pipdash.
"""

import sys
import json
import httpx
from rich.console import Console

from pipdash import __version__
from pipdash.api import get_stats, get_info
from pipdash.display import show_stats, show_info, show_compare, show_json

console = Console()
err_console = Console(stderr=True, style="bold red")

HELP = f"""
[bold cyan]pipdash[/bold cyan] v{__version__} — PyPI package stats at your fingertips

[bold]Usage:[/bold]
  pipdash stats <package> [--json]     Download stats + metadata
  pipdash stats <package> -zerotraffic  PyPI Stats-only view (no Pepy periods)
  pipdash info  <package> [--json]     Package metadata & dependencies
  pipdash compare <pkg1> <pkg2> ...    Side-by-side comparison

[bold]Options:[/bold]
  --json    Output raw JSON (pipe-friendly)
  --help    Show this message
  --version Show version

[bold]Examples:[/bold]
  pipdash stats requests
  pipdash stats numpy --json
  pipdash stats rag-harness -zerotraffic
  pipdash info django
  pipdash compare requests httpx aiohttp

[bold]Data sources:[/bold]
  pypi.org · pypistats.org · pepy.tech
"""


def _is_flag(arg: str) -> bool:
    return arg.startswith("--")


def _handle_error(e: Exception, package: str) -> None:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            err_console.print(f"\n❌ Package '{package}' not found on PyPI.\n"
                              f"   Check the spelling or visit https://pypi.org/search/?q={package}\n")
        elif code == 429:
            err_console.print(f"\n❌ Rate limited by pypistats.org. Please wait a moment and try again.\n")
        else:
            err_console.print(f"\n❌ HTTP {code} error fetching data for '{package}'.\n")
    elif isinstance(e, httpx.ConnectError):
        err_console.print(f"\n❌ Could not connect. Check your internet connection.\n")
    elif isinstance(e, httpx.TimeoutException):
        err_console.print(f"\n❌ Request timed out. Try again in a moment.\n")
    else:
        err_console.print(f"\n❌ Unexpected error: {e}\n")
    sys.exit(1)


def cmd_stats(args: list[str]) -> None:
    flags   = [a for a in args if _is_flag(a)]
    positional = [a for a in args if not _is_flag(a)]

    if not positional:
        err_console.print("\n❌ Usage: pipdash stats <package> [--json]\n")
        sys.exit(1)

    package = positional[0]
    as_json = "--json" in flags
    zero_traffic = "-zerotraffic" in flags or "--zerotraffic" in flags

    if not as_json:
        console.print(f"\n[dim]Fetching stats for '{package}'...[/dim]")

    try:
        data = get_stats(package, zero_traffic=zero_traffic)
    except Exception as e:
        _handle_error(e, package)

    if as_json:
        show_json(data)
    else:
        show_stats(data)


def cmd_info(args: list[str]) -> None:
    flags      = [a for a in args if _is_flag(a)]
    positional = [a for a in args if not _is_flag(a)]

    if not positional:
        err_console.print("\n❌ Usage: pipdash info <package> [--json]\n")
        sys.exit(1)

    package = positional[0]
    as_json = "--json" in flags

    if not as_json:
        console.print(f"\n[dim]Fetching info for '{package}'...[/dim]")

    try:
        data = get_info(package)
    except Exception as e:
        _handle_error(e, package)

    if as_json:
        show_json(data)
    else:
        show_info(data)


def cmd_compare(args: list[str]) -> None:
    flags      = [a for a in args if _is_flag(a)]
    positional = [a for a in args if not _is_flag(a)]

    if len(positional) < 2:
        err_console.print("\n❌ Usage: pipdash compare <pkg1> <pkg2> [pkg3...]\n")
        sys.exit(1)

    as_json = "--json" in flags
    results = []

    for pkg in positional:
        if not as_json:
            console.print(f"[dim]Fetching '{pkg}'...[/dim]")
        try:
            results.append(get_stats(pkg))
        except Exception as e:
            _handle_error(e, pkg)

    if as_json:
        show_json(results)
    else:
        show_compare(results)


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        console.print(HELP)
        sys.exit(0)

    if args[0] in ("--version", "-V"):
        console.print(f"pipdash v{__version__}")
        sys.exit(0)

    cmd  = args[0]
    rest = args[1:]

    if cmd == "stats":
        cmd_stats(rest)
    elif cmd == "info":
        cmd_info(rest)
    elif cmd == "compare":
        cmd_compare(rest)
    else:
        err_console.print(f"\n❌ Unknown command '{cmd}'.")
        console.print("   Run [bold]pipdash --help[/bold] to see available commands.\n")
        sys.exit(1)
