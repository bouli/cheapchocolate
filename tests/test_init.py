import pytest

import cheapchocolate


def test_main_start_command_receives_default_mail_folders(monkeypatch):
    calls = []

    monkeypatch.setattr("sys.argv", ["cheapchocolate", "start"])
    monkeypatch.setattr(cheapchocolate, "get_mails", calls.append)

    cheapchocolate.main()

    assert calls == ["mail_folders"]


def test_main_start_command_receives_requested_folder(monkeypatch):
    calls = []

    monkeypatch.setattr("sys.argv", ["cheapchocolate", "start", "--folder", "inbox"])
    monkeypatch.setattr(cheapchocolate, "get_mails", calls.append)

    cheapchocolate.main()

    assert calls == ["inbox"]


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
