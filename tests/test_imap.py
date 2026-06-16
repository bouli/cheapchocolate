from email.message import EmailMessage

from cheapchocolate.modules import imap


class FakeImapConnection:
    def __init__(self, raw_message=b"", search_result=b""):
        self.raw_message = raw_message
        self.search_result = search_result
        self.fetch_calls = []
        self.selected_folders = []
        self.search_calls = []
        self.closed = False
        self.logged_out = False

    def fetch(self, email_id, query):
        self.fetch_calls.append((email_id, query))
        return "OK", [(b"message", self.raw_message)]

    def select(self, mail_folder):
        self.selected_folders.append(mail_folder)
        return "OK", []

    def search(self, charset, criteria):
        self.search_calls.append((charset, criteria))
        return "OK", [self.search_result]

    def close(self):
        self.closed = True

    def logout(self):
        self.logged_out = True


def build_message():
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["To"] = "receiver@example.com"
    msg["Subject"] = "Daily/report's"
    msg["Date"] = "Wed, 14 Jan 2026 09:30:00 +0000"
    msg.set_content("Hello from CheapChocolate")
    return msg.as_bytes()


def test_imaptime2datetime_formats_imap_date_as_file_id():
    assert imap.imaptime2datetime("Wed, 14 Jan 2026 09:30:00 +0000") == "20260114093000"


def test_add_mail_line_appends_and_strips_outer_whitespace():
    assert imap.add_mail_line(line="subject: Hello", mail_string="from: test") == (
        "from: test\nsubject: Hello"
    )


def test_extract_from_header_decodes_encoded_subject():
    msg = EmailMessage()
    msg["Subject"] = "=?utf-8?q?Ol=C3=A1?="

    assert imap.extract_from_header(msg=msg, key="subject") == "Olá"


def test_clean_folder_name_extracts_remote_folder_name():
    assert imap._clean_folder_name(b'(\\HasNoChildren) "/" "INBOX"') == "INBOX"


def test_load_email_by_id_writes_message_to_local_mailbox(tmp_path, monkeypatch):
    connection = FakeImapConnection(raw_message=build_message())
    monkeypatch.setattr(imap, "get_local_mailbox_folder", lambda: str(tmp_path))

    result = imap.load_email_by_id(
        imap_connection=connection,
        email_id=b"1",
        mail_folder="inbox",
    )

    expected_file = tmp_path / "20260114093000 - Dailyreports [inbox].md"
    assert result is True
    assert connection.fetch_calls == [(b"1", "(RFC822)")]
    assert expected_file.read_text() == "\n".join(
        [
            "----------",
            "from: sender@example.com",
            "to: receiver@example.com",
            'subject: "Daily/report\'s"',
            "date: Wed, 14 Jan 2026 09:30:00 +0000",
            'mail_folder: "inbox"',
            "----------",
            "Hello from CheapChocolate",
            "----------",
        ]
    )


def test_load_email_by_id_skips_existing_local_message(tmp_path, monkeypatch):
    connection = FakeImapConnection(raw_message=build_message())
    monkeypatch.setattr(imap, "get_local_mailbox_folder", lambda: str(tmp_path))
    existing_file = tmp_path / "20260114093000 - Dailyreports [inbox].md"
    existing_file.write_text("already downloaded")

    result = imap.load_email_by_id(
        imap_connection=connection,
        email_id=b"1",
        mail_folder="inbox",
    )

    assert result is None
    assert existing_file.read_text() == "already downloaded"


def test_get_mails_selects_folder_loads_each_message_and_closes_connection(monkeypatch):
    connection = FakeImapConnection(search_result=b"1 2")
    loaded_messages = []

    monkeypatch.setattr(
        imap,
        "load_email_by_id",
        lambda imap_connection, email_id, mail_folder: loaded_messages.append(
            (imap_connection, email_id, mail_folder)
        ),
    )

    imap._get_mails(
        mail_folder="inbox",
        days_to_fetch=1,
        imap_connection=connection,
    )

    assert connection.selected_folders == ["inbox"]
    assert connection.search_calls[0][0] is None
    assert connection.search_calls[0][1].startswith("SINCE ")
    assert loaded_messages == [
        (connection, b"1", "inbox"),
        (connection, b"2", "inbox"),
    ]
    assert connection.closed is True
    assert connection.logged_out is True


def test_get_mails_keeps_shared_connection_open_when_requested(monkeypatch):
    connection = FakeImapConnection(search_result=b"")

    imap._get_mails(
        mail_folder="archive",
        days_to_fetch=1,
        imap_connection=connection,
        let_imap_connection_opened=True,
    )

    assert connection.selected_folders == ["archive"]
    assert connection.closed is False
    assert connection.logged_out is False
