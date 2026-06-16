from cheapchocolate.modules import mailbox


def test_get_local_mailbox_folder_uses_configured_mailbox_dir(monkeypatch):
    monkeypatch.setattr(mailbox.config, "get_dir", lambda param: f"/tmp/{param}")

    assert mailbox.get_local_mailbox_folder() == "/tmp/mailbox"


def test_get_local_mails_returns_message_ids_from_local_filenames(monkeypatch):
    monkeypatch.setattr(mailbox, "get_local_mailbox_folder", lambda: "/mailbox")
    monkeypatch.setattr(
        mailbox.os,
        "listdir",
        lambda folder: [
            "20260114093000 - Morning update [inbox].md",
            "20260114101530 - Invoice [finance].md",
        ],
    )

    assert mailbox.get_local_mails() == ["20260114093000", "20260114101530"]


def test_get_local_mails_lists_configured_mailbox_folder(monkeypatch):
    listed_folders = []

    monkeypatch.setattr(mailbox, "get_local_mailbox_folder", lambda: "/custom-mailbox")
    monkeypatch.setattr(
        mailbox.os,
        "listdir",
        lambda folder: listed_folders.append(folder) or [],
    )

    assert mailbox.get_local_mails() == []
    assert listed_folders == ["/custom-mailbox"]
