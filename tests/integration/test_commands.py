from __future__ import annotations

from typer.testing import CliRunner

from px_cli.app import app

runner = CliRunner()


class TestCliBasic:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "px" in result.stdout

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        # Typer exits with code 2 when no_args_is_help=True
        assert result.exit_code == 2

    def test_vm_help(self):
        result = runner.invoke(app, ["vm", "--help"])
        assert result.exit_code == 0
        assert "Manage" in result.stdout

    def test_storage_help(self):
        result = runner.invoke(app, ["storage", "--help"])
        assert result.exit_code == 0
        assert "Manage" in result.stdout

    def test_backup_help(self):
        result = runner.invoke(app, ["backup", "--help"])
        assert result.exit_code == 0
        assert "Manage" in result.stdout

    def test_vm_top_help(self):
        result = runner.invoke(app, ["vm", "top", "--help"])
        assert result.exit_code == 0
        assert "resource" in result.stdout.lower()

    def test_vm_info_help(self):
        result = runner.invoke(app, ["vm", "info", "--help"])
        assert result.exit_code == 0
        assert "configuration" in result.stdout.lower()
