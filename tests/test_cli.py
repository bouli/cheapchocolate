import sys
from unittest.mock import patch

from cheapchocolate import main


def test_start_command_passes_remote_read_state_override():
    with (
        patch.object(
            sys,
            "argv",
            ["cheapchocolate", "start", "--remote-read-state", "mark_read"],
        ),
        patch("cheapchocolate.get_mails") as get_mails,
    ):
        main()

    get_mails.assert_called_once_with("mail_folders", remote_read_state="mark_read")


def test_start_command_defaults_to_configured_remote_read_state():
    with (
        patch.object(sys, "argv", ["cheapchocolate", "start"]),
        patch("cheapchocolate.get_mails") as get_mails,
    ):
        main()

    get_mails.assert_called_once_with("mail_folders", remote_read_state=None)


def test_start_command_help_names_remote_read_state_modes(capsys):
    with (
        patch.object(sys, "argv", ["cheapchocolate", "start", "--help"]),
        patch("cheapchocolate.get_mails"),
    ):
        try:
            main()
        except SystemExit as error:
            assert error.code == 0
        else:
            raise AssertionError("Expected argparse help to exit")

    help_text = capsys.readouterr().out
    assert "--remote-read-state" in help_text
    assert "preserve" in help_text
    assert "mark_read" in help_text
