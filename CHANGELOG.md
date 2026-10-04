# Changelog

## [1.1.4] - 2026-10-04

### Added
- Added a branded, colorful terminal homepage for `pipdash`.
- Added quick-start commands and an example stats output preview.
- Added a responsive Rich panel for the terminal output preview.

### Changed
- `pipdash` without arguments now shows a concise terminal homepage.
- `pipdash --help` remains the full command and option reference.

## [1.1.3] - 2026-08-15

### Fixed
- Removed unnecessary blank spacing between all-time download statistics and package metadata.

## [1.0.1] - 2026-08-15

### Changed
- All-time downloads now use Pepy.tech's public total-download badge so the headline total matches Pepy.
- Removed synthetic 90-day and 180-day estimates.
- 90-day and 180-day values are now summed from the actual PyPI Stats daily series and are shown only when the full window is available.

## [1.0.0] - 2026-08-15

### Added
- `pipdash stats <package>` — full download stats with 24h / 7d / 30d / optional 90d / 180d / all-time
- All-time downloads highlighted in bold yellow
- Python version and platform breakdown with visual bars
- `pipdash info <package>` — metadata, dependencies, project links
- `pipdash compare <pkg1> <pkg2>` — side-by-side comparison table
- `--json` flag on all commands for scripting
- Clean error messages for 404, 429 (rate limit), and network errors
- No API key or account required
