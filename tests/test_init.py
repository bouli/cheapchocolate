import pytest

import cheapchocolate


def test_main_start_command_receives_default_mail_folders(monkeypatch):
    calls = []

    monkeypatch.setattr("sys.argv", ["cheapchocolate", "start"])
    monkeypatch.setattr(
        cheapchocolate,
        "get_mails",
        lambda folder, remote_read_status=None: calls.append(
            (folder, remote_read_status)
        ),
    )

    cheapchocolate.main()

    assert calls == [("mail_folders", None)]


def test_main_start_command_receives_requested_folder(monkeypatch):
    calls = []

    monkeypatch.setattr("sys.argv", ["cheapchocolate", "start", "--folder", "inbox"])
    monkeypatch.setattr(
        cheapchocolate,
        "get_mails",
        lambda folder, remote_read_status=None: calls.append(
            (folder, remote_read_status)
        ),
    )

    cheapchocolate.main()

    assert calls == [("inbox", None)]


def test_main_start_command_receives_remote_read_status_override(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "sys.argv",
        [
            "cheapchocolate",
            "start",
            "--folder",
            "inbox",
            "--remote-read-status",
            "mark_read",
        ],
    )
    monkeypatch.setattr(
        cheapchocolate,
        "get_mails",
        lambda folder, remote_read_status=None: calls.append(
            (folder, remote_read_status)
        ),
    )

    cheapchocolate.main()

    assert calls == [("inbox", "mark_read")]


def test_main_start_help_names_remote_read_status_options(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cheapchocolate", "start", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cheapchocolate.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--remote-read-status" in help_text
    assert "preserve" in help_text
    assert "mark_read" in help_text


def test_main_folders_command_lists_remote_folders(monkeypatch):
    calls = []

    monkeypatch.setattr("sys.argv", ["cheapchocolate", "folders"])
    monkeypatch.setattr(cheapchocolate, "get_folders", lambda: calls.append("folders"))

    cheapchocolate.main()

    assert calls == ["folders"]


def test_main_version_option_prints_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cheapchocolate", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        cheapchocolate.main()

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "cheapchocolate v0.5.1\n"
