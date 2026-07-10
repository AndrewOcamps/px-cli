# AGENTS.md — AI Agent Instructions for px-cli

## Project Overview

- **px-cli**: Command-line tool for managing Proxmox VE clusters
- **Python 3.10+** | Typer CLI | Rich output | Pydantic models/settings
- `src/px_cli/` layout, hatchling build system
- Entry point: `px = px_cli.app:main`

## Quick Reference — Commands

| Task                    | Command                                      |
|-------------------------|----------------------------------------------|
| Install (editable)      | `pip install -e ".[dev]"`                    |
| Lint                    | `ruff check .`                               |
| Format                  | `ruff format .`                              |
| Type check              | `mypy src/`                                  |
| Test                    | `pytest`                                     |
| Test with coverage      | `pytest --cov=src/ --cov-report=term-missing`|
| Pre-commit (all hooks)  | `pre-commit run --all-files`                 |

**Always run lint, typecheck, and tests before committing.**

## Architecture

| File/Directory          | Purpose                                      |
|-------------------------|----------------------------------------------|
| `src/px_cli/app.py`     | Top-level Typer app, registers all sub-apps  |
| `src/px_cli/client.py`  | Proxmox API HTTP client (all API calls)      |
| `src/px_cli/config.py`  | Pydantic Settings config (`~/.proxmox/config`)|
| `src/px_cli/models.py`  | Pydantic data models for API responses       |
| `src/px_cli/utils.py`   | Shared helpers (tables, confirm, resolve)    |
| `src/px_cli/exceptions.py` | `PxError` hierarchy                      |
| `src/px_cli/logging.py` | Structured logging with `--verbose`          |
| `src/px_cli/commands/`  | One file per command group                   |
| `tests/unit/`           | Mock-based unit tests                        |
| `tests/integration/`    | CliRunner-based integration tests            |

## Adding a New Command

1. Create `src/px_cli/commands/<name>.py` with a `typer.Typer()` sub-app
2. Register in `src/px_cli/app.py` via `app.add_typer(..., name="<name>")`
3. Add Pydantic model in `src/px_cli/models.py` if new API response shape
4. Add API method to `src/px_cli/client.py` if new endpoint needed
5. Add unit tests in `tests/unit/` (mock HTTP with `requests_mock`)
6. Add integration tests in `tests/integration/` if needed (`CliRunner`)

## Adding a New Sub-command to Existing Group

1. Add function in the existing command file (e.g., `commands/vm.py`)
2. Decorate with `@vm_app.command()`
3. Follow existing patterns for `--confirm`/`--dry-run`/`--wait` options
4. Add unit test in `tests/unit/`

## Code Style

- **Ruff rules**: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming), `W` (warnings), `UP` (pyupgrade)
- **Line length**: 100
- **mypy**: strict — no implicit optionals, warn unused ignores/casts/configs
- **No comments** in code unless explicitly requested
- Follow existing patterns — always check neighboring files for style

## Testing Patterns

- Fixtures in `tests/conftest.py`: `mock_client`, `requests_mocker`, `sample_vm`, `sample_config`, `tmp_config_dir`
- Unit tests mock HTTP via `requests_mock.Mocker`
- Integration tests use `typer.testing.CliRunner`
- Tests grouped by class: `TestXxxInit`, `TestXxxRequests`, `TestXxxActions`

## CI Pipeline

- Python 3.10, 3.11, 3.12 matrix on `ubuntu-latest`
- Pipeline: `ruff check .` → `mypy src/` → `pytest --cov=src/`
- Release: push tag `v*` → build + GitHub Release with dist artifacts
