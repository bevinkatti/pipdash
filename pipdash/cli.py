"""
pipdash.cli
Command-line interface for pipdash.
"""

import sys
import json
import httpx
from rich.console import Console
from rich.panel import Panel

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
  pipdash stats rag-harness
  pipdash stats numpy --json
  pipdash stats rich -zerotraffic
  pipdash info django
  pipdash compare requests httpx aiohttp

[bold]Data sources:[/bold]
  pypi.org · pypistats.org · pepy.tech
"""
#==== Cli Home screen ======

HOME = f"""
[bold bright_cyan]  ██████╗ ██╗██████╗ ██████╗  █████╗ ███████╗██╗  ██╗[/bold bright_cyan]
[bold cyan]  ██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██╔════╝██║  ██║[/bold cyan]
[bold bright_cyan]  ██████╔╝██║██████╔╝██║  ██║███████║███████╗███████║[/bold bright_cyan]
[bold cyan]  ██╔═══╝ ██║██╔═══╝ ██║  ██║██╔══██║╚════██║██╔══██║[/bold cyan]
[bold bright_cyan]  ██║     ██║██║     ██████╔╝██║  ██║███████║██║  ██║[/bold bright_cyan]
[bold cyan]  ╚═╝     ╚═╝╚═╝     ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝[/bold cyan]
[bold dim]                        v{__version__}[/bold dim]

[bold white] PyPI package downloads, stats & metadata — at your fingertips.[/bold white]

[dim]  ──────────────────────────────────────────────────────[/dim]
[bold bright_cyan]  QUICK START[/bold bright_cyan]

[green]    $ pipdash stats <package>[/green]
[green]    $ pipdash info <package>[/green]
[green]    $ pipdash compare <package1> <package2> ...[/green]
[dim]  ──────────────────────────────────────────────────────[/dim]

[orange]    Run [bold]pipdash --help[/bold] for all commands and options.[/orange]
"""
# home Preview
def show_home_preview() -> None:
    preview = """[bold]$ pipdash stats rich[/bold]

[bold bright_cyan]📦 rich[/bold bright_cyan]
    [dim]v15.0.0[/dim]

[bold bright_cyan]📊 Downloads[/bold bright_cyan]
    [dim]Last 24 hours[/dim]       [bold]14.90M[/bold]
    [dim]Last 7 days[/dim]         [bold]122.32M[/bold]
    [dim]Last 30 days[/dim]        [bold]614.61M[/bold]

    [bold]⬇ Total downloads[/bold]    [bold]8.20G[/bold]

[bold bright_cyan]ℹ Package[/bold bright_cyan]
    [dim]License[/dim]             [bold]MIT[/bold]
    [dim]Python[/dim]              [bold]>=3.9[/bold]
    """

    panel_width = min(72, console.width - 4)

    console.print(
        Panel(
            preview,
            title="[bold bright_cyan]Example output[/bold bright_cyan]",
            border_style="cyan",
            padding=(0, 1),
            width=panel_width,
        )
    )

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

    if not args:
        console.print(HOME)
        show_home_preview()
        sys.exit(0)

    if args[0] in ("--help", "-help", "-h"):
        console.print(HELP)
        sys.exit(0)

    if args[0] in ("--version", "-V", "-v"):
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
