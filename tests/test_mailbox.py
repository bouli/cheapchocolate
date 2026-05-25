from cheapchocolate.modules import mailbox


def test_get_local_mailbox_folder_uses_configured_mailbox_dir(monkeypatch):
    calls = []

    def fake_get_dir(param):
        calls.append(param)
        return "/tmp/cheapchocolate-mailbox"

    monkeypatch.setattr(mailbox.config, "get_dir", fake_get_dir)

    assert mailbox.get_local_mailbox_folder() == "/tmp/cheapchocolate-mailbox"
    assert calls == ["mailbox"]


def test_get_local_mails_returns_mail_ids_from_local_filenames(monkeypatch):
    monkeypatch.setattr(
        mailbox,
        "get_local_mailbox_folder",
        lambda: "/tmp/cheapchocolate-mailbox",
    )

    listed_paths = []

    def fake_listdir(path):
        listed_paths.append(path)
        return [
            "abc123 - Welcome.eml",
            "def456 - Daily report - final.eml",
            "no-delimiter.eml",
        ]

    monkeypatch.setattr(mailbox.os, "listdir", fake_listdir)

    assert mailbox.get_local_mails() == ["abc123", "def456", "no-delimiter.eml"]
    assert listed_paths == ["/tmp/cheapchocolate-mailbox"]


def test_get_local_mails_returns_empty_list_when_mailbox_is_empty(monkeypatch):
    monkeypatch.setattr(mailbox, "get_local_mailbox_folder", lambda: "/empty/mailbox")
    monkeypatch.setattr(mailbox.os, "listdir", lambda path: [])

    assert mailbox.get_local_mails() == []
