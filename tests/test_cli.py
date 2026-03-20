from click.testing import CliRunner

from youtube_agent.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ideate" in result.output
    assert "produce" in result.output
    assert "analyze" in result.output
    assert "full" in result.output
    assert "resume" in result.output
    assert "sessions" in result.output


def test_ideate_command_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["ideate", "--help"])
    assert result.exit_code == 0
