import os
import tempfile
import unittest
from contextlib import contextmanager
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import Mock, call, patch

from cheapchocolate.modules import imap


@contextmanager
def temporary_cwd():
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        try:
            yield Path(tmp_dir)
        finally:
            os.chdir(previous_cwd)


class ImapConnectionTests(unittest.TestCase):

    def test_create_env_file_writes_template_to_current_working_directory(self):
        with temporary_cwd() as tmp_dir:
            imap.create_env_file()

            self.assertEqual(
                (tmp_dir / ".env").read_text(),
                "user=myuser@my-mail.server\n"
                "password=mypassword\n"
                "server=imap.my-mail.server\n",
            )

    def test_get_imap_connection_loads_env_from_current_working_directory(self):
        with temporary_cwd():
            Path(".env").write_text(
                "user=test@example.com\n"
                "password=secret\n"
                "server=imap.example.com\n"
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("cheapchocolate.modules.imap.imaplib.IMAP4_SSL") as imap_ssl,
            ):
                connection = imap.get_imap_connection()

            imap_ssl.assert_called_once_with("imap.example.com")
            imap_ssl.return_value.login.assert_called_once_with(
                "test@example.com", "secret"
            )
            self.assertIs(connection, imap_ssl.return_value)

    def test_get_imap_connection_prompts_when_password_is_missing(self):
        with temporary_cwd():
            Path(".env").write_text(
                "user=test@example.com\n"
                "server=imap.example.com\n"
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("cheapchocolate.modules.imap.getpass.getpass") as getpass,
                patch("cheapchocolate.modules.imap.imaplib.IMAP4_SSL") as imap_ssl,
            ):
                getpass.return_value = "prompted-secret"

                connection = imap.get_imap_connection()

            getpass.assert_called_once_with("IMAP password: ")
            imap_ssl.return_value.login.assert_called_once_with(
                "test@example.com", "prompted-secret"
            )
            self.assertIs(connection, imap_ssl.return_value)

    def test_get_imap_connection_creates_template_when_user_is_missing(self):
        with temporary_cwd() as tmp_dir:
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("cheapchocolate.modules.imap.imaplib.IMAP4_SSL") as imap_ssl,
            ):
                connection = imap.get_imap_connection()

            self.assertIsNone(connection)
            self.assertTrue((tmp_dir / ".env").exists())
            imap_ssl.assert_not_called()

    def test_get_imap_connection_returns_none_when_login_fails(self):
        with temporary_cwd():
            Path(".env").write_text(
                "user=test@example.com\n"
                "password=wrong\n"
                "server=imap.example.com\n"
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("cheapchocolate.modules.imap.imaplib.IMAP4_SSL") as imap_ssl,
            ):
                imap_ssl.return_value.login.side_effect = imap.imaplib.IMAP4.error

                self.assertIsNone(imap.get_imap_connection())


class MailFetchingTests(unittest.TestCase):
    def test_get_mails_returns_false_when_connection_cannot_be_created(self):
        with patch("cheapchocolate.modules.imap.get_imap_connection", return_value=None):
            self.assertFalse(imap._get_mails(mail_folder="inbox"))

    def test_get_mails_closes_connection_when_there_are_no_messages(self):
        connection = Mock()
        connection.search.return_value = ("OK", [b""])

        with (
            patch("cheapchocolate.modules.imap.config.get_mails", return_value="1"),
            patch(
                "cheapchocolate.modules.imap.config.get_remote_read_state",
                return_value="preserve",
            ),
            patch("cheapchocolate.modules.imap.close_imap_connection") as close,
        ):
            result = imap._get_mails(mail_folder="inbox", imap_connection=connection)

        self.assertIsNone(result)
        connection.select.assert_called_once_with("inbox")
        connection.search.assert_called_once()
        close.assert_called_once_with(connection)

    def test_get_mails_downloads_each_message_and_keeps_shared_connection_open(self):
        connection = Mock()
        connection.search.return_value = ("OK", [b"1 2"])

        with (
            patch("cheapchocolate.modules.imap.config.get_mails", return_value="1"),
            patch(
                "cheapchocolate.modules.imap.config.get_remote_read_state",
                return_value="preserve",
            ),
            patch("cheapchocolate.modules.imap.load_email_by_id") as load_email_by_id,
            patch("cheapchocolate.modules.imap.close_imap_connection") as close,
        ):
            imap._get_mails(
                mail_folder="inbox",
                imap_connection=connection,
                let_imap_connection_opened=True,
            )

        load_email_by_id.assert_has_calls(
            [
                call(
                    imap_connection=connection,
                    email_id=b"1",
                    mail_folder="inbox",
                    remote_read_state="preserve",
                ),
                call(
                    imap_connection=connection,
                    email_id=b"2",
                    mail_folder="inbox",
                    remote_read_state="preserve",
                ),
            ]
        )
        close.assert_not_called()

    def test_get_mails_uses_non_mutating_fetch_for_default_receive_path(self):
        message = EmailMessage()
        message["from"] = "sender@example.com"
        message["to"] = "receiver@example.com"
        message["subject"] = "Unread Message"
        message["date"] = "Mon, 01 Jan 2024 12:34:56 +0000"
        message.set_content("Unread body")

        connection = Mock()
        connection.search.return_value = ("OK", [b"1"])
        connection.fetch.return_value = ("OK", [(b"1", message.as_bytes())])

        with tempfile.TemporaryDirectory() as mailbox_folder:
            with (
                patch("cheapchocolate.modules.imap.config.get_mails", return_value="1"),
                patch(
                    "cheapchocolate.modules.imap.config.get_remote_read_state",
                    return_value="preserve",
                ),
                patch(
                    "cheapchocolate.modules.imap.get_local_mailbox_folder",
                    return_value=mailbox_folder,
                ),
                patch("cheapchocolate.modules.imap.close_imap_connection"),
            ):
                imap._get_mails(mail_folder="inbox", imap_connection=connection)

        connection.fetch.assert_called_once_with(
            b"1", imap.NON_MUTATING_MESSAGE_FETCH
        )
        connection.store.assert_not_called()

    def test_get_mails_uses_non_mutating_fetch_for_single_folder_receive_path(self):
        connection = Mock()
        connection.search.return_value = ("OK", [b"1"])

        with (
            patch("cheapchocolate.modules.imap.config.get_mails", return_value="1"),
            patch(
                "cheapchocolate.modules.imap.config.get_remote_read_state",
                return_value="preserve",
            ),
            patch("cheapchocolate.modules.imap.load_email_by_id") as load_email_by_id,
            patch("cheapchocolate.modules.imap.close_imap_connection"),
        ):
            imap._get_mails(mail_folder="Archive", imap_connection=connection)

        load_email_by_id.assert_called_once_with(
            imap_connection=connection,
            email_id=b"1",
            mail_folder="Archive",
            remote_read_state="preserve",
        )
        connection.store.assert_not_called()

    def test_get_mails_uses_mutating_fetch_when_config_marks_remote_read(self):
        message = EmailMessage()
        message["from"] = "sender@example.com"
        message["to"] = "receiver@example.com"
        message["subject"] = "Read During Receive"
        message["date"] = "Mon, 01 Jan 2024 12:34:56 +0000"
        message.set_content("Body")

        connection = Mock()
        connection.search.return_value = ("OK", [b"1"])
        connection.fetch.return_value = ("OK", [(b"1", message.as_bytes())])

        with tempfile.TemporaryDirectory() as mailbox_folder:
            with (
                patch("cheapchocolate.modules.imap.config.get_mails", return_value="1"),
                patch(
                    "cheapchocolate.modules.imap.config.get_remote_read_state",
                    return_value="mark_read",
                ),
                patch(
                    "cheapchocolate.modules.imap.get_local_mailbox_folder",
                    return_value=mailbox_folder,
                ),
                patch("cheapchocolate.modules.imap.close_imap_connection"),
            ):
                imap._get_mails(mail_folder="inbox", imap_connection=connection)

        connection.fetch.assert_called_once_with(b"1", imap.MUTATING_MESSAGE_FETCH)
        connection.store.assert_not_called()

    def test_get_mails_remote_read_state_override_takes_precedence(self):
        mail_folders = {"inbox": {"days_to_fetch": 1}}
        connection = Mock()
        connection.search.return_value = ("OK", [b"1"])

        with (
            patch(
                "cheapchocolate.modules.imap.config.get_mail_folders",
                return_value=mail_folders,
            ),
            patch(
                "cheapchocolate.modules.imap.config.get_remote_read_state",
                return_value="preserve",
            ),
            patch(
                "cheapchocolate.modules.imap.get_imap_connection",
                return_value=connection,
            ),
            patch("cheapchocolate.modules.imap.load_email_by_id") as load_email_by_id,
            patch("cheapchocolate.modules.imap.close_imap_connection"),
        ):
            imap.get_mails(remote_read_state="mark_read")

        load_email_by_id.assert_called_once_with(
            imap_connection=connection,
            email_id=b"1",
            mail_folder="inbox",
            remote_read_state="mark_read",
        )

    def test_message_fetch_rejects_invalid_remote_read_state(self):
        with self.assertRaises(ValueError):
            imap.message_fetch_for_remote_read_state("invalid")


class MessageParsingTests(unittest.TestCase):
    def test_imaptime2datetime_converts_header_date(self):
        self.assertEqual(
            imap.imaptime2datetime("Mon, 01 Jan 2024 12:34:56 +0000"),
            "20240101123456",
        )

    def test_extract_from_header_decodes_encoded_value(self):
        message = EmailMessage()
        message["subject"] = "=?utf-8?q?Daily_Chocolate?="

        self.assertEqual(
            imap.extract_from_header(message, "subject"), "Daily Chocolate"
        )

    def test_add_mail_line_appends_and_strips_outer_whitespace(self):
        self.assertEqual(
            imap.add_mail_line(line="second", mail_string="first"),
            "first\nsecond",
        )

    def test_clean_folder_name_extracts_folder_name(self):
        self.assertEqual(
            imap._clean_folder_name(b'(\\HasNoChildren) "/" "INBOX"'), "INBOX"
        )

    def test_load_email_by_id_writes_message_to_mailbox_folder(self):
        message = EmailMessage()
        message["from"] = "sender@example.com"
        message["to"] = "receiver@example.com"
        message["subject"] = "Test /Subject's"
        message["date"] = "Mon, 01 Jan 2024 12:34:56 +0000"
        message.set_content("Hello from the body")

        connection = Mock()
        connection.fetch.return_value = ("OK", [(b"1", message.as_bytes())])

        with tempfile.TemporaryDirectory() as mailbox_folder:
            with patch(
                "cheapchocolate.modules.imap.get_local_mailbox_folder",
                return_value=mailbox_folder,
            ):
                result = imap.load_email_by_id(connection, b"1", mail_folder="inbox")

            written_file = (
                Path(mailbox_folder) / "20240101123456 - Test Subjects [inbox].md"
            )
            self.assertTrue(result)
            self.assertTrue(written_file.exists())
            self.assertIn("from: sender@example.com", written_file.read_text())
            self.assertIn("Hello from the body", written_file.read_text())

    def test_load_email_by_id_fetches_without_marking_remote_message_read(self):
        message = EmailMessage()
        message["from"] = "sender@example.com"
        message["to"] = "receiver@example.com"
        message["subject"] = "Preserved Status"
        message["date"] = "Mon, 01 Jan 2024 12:34:56 +0000"
        message.set_content("Body")

        connection = Mock()
        connection.fetch.return_value = ("OK", [(b"1", message.as_bytes())])

        with tempfile.TemporaryDirectory() as mailbox_folder:
            with patch(
                "cheapchocolate.modules.imap.get_local_mailbox_folder",
                return_value=mailbox_folder,
            ):
                imap.load_email_by_id(connection, b"1", mail_folder="inbox")

        connection.fetch.assert_called_once_with(
            b"1", imap.NON_MUTATING_MESSAGE_FETCH
        )
        connection.store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
