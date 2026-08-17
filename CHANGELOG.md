# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `px vm info <vmid>`: show basic configuration of a VM or container in table or JSON format

## [0.3.1] - 2026-07-09

### Added
- Missing options documentation in commands.md (19 commands)

### Changed
- README: updated install instructions, quickstart
- LICENSE: GPL-3.0 → MIT (matching pyproject.toml)
- CHANGELOG: corrected PyPI claim → GitHub Release only

## [0.3.0] - 2026-07-09

### Added
- Enterprise-grade project restructuring with `pyproject.toml` (PEP 517/518/621)
- `src/` layout for clean import isolation
- Pydantic models replacing TypedDicts (`models.py`)
- Pydantic Settings for configuration (`config.py`) with `PX_ENDPOINT`/`PX_TOKEN` env var support
- Exception hierarchy (`exceptions.py`): `PxError` → `ConfigError`, `AuthError`, `ApiError`, `NotFoundError`
- Structured logging (`logging.py`) with `--verbose` support
- Retry logic with exponential backoff in client (`client.py`)
- Context manager support for `ProxmoxClient`
- Comprehensive test suite: 42 unit + integration tests
- GitHub Actions CI: lint (ruff) + typecheck (mypy) + test (pytest) on Python 3.10-3.12
- GitHub Actions Release workflow: build package and create GitHub Release on version tags
- Pre-commit hooks: ruff, mypy, trailing-whitespace, end-of-file-fixer

### Changed
- Migrated from flat `px_cli/` to `src/px_cli/` layout
- Replaced `requirements.txt` with `[project.dependencies]` in pyproject.toml
- Replaced `install.py` with standard `pip install -e .`
- Updated `px` entry point to use `src/` directory

### Removed
- `install.py` (superseded by pip-installable package)
- `requirements.txt` (moved to pyproject.toml)

## [0.2.0] - 2026-07-08

### Added
- Typer-based CLI with 9 command groups: vm, storage, backup, template, node, pool, cluster, firewall
- Interactive `install.py` for first-time setup
- `px login` / `px logout` with automatic API token creation
- Snapshot management under `px vm snapshot`
- Rich table output for all list commands

### Changed
- Migrated from click to Typer
- Flat aliases replaced by command groups

## [0.1.0] - 2026-07-07

### Added
- Initial release with basic Proxmox CLI functionality
- Click-based command structure
- API token authentication
- VM list, start, stop, restart commands
