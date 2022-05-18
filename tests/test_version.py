from typer.testing import CliRunner

from voice_presentation_control import __app_name__, __version__, cli

runner = CliRunner()


def test_version():
    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert f"{__app_name__} {__version__}\n" in result.stdout
