import unittest

from cheapchocolate.modules.imap_mailbox import (
    MailboxOption,
    MailboxParseError,
    decode_modified_utf7,
    encode_modified_utf7,
    parse_mailbox_list_entries,
    parse_mailbox_list_entry,
    prepare_select_mailbox,
    select_mailbox_name,
)


class MailboxListEntryParsingTests(unittest.TestCase):
    def test_parse_inbox_folder(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "INBOX"'),
            MailboxOption(display_name="INBOX", imap_name="INBOX"),
        )

    def test_parse_archive_folder(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "Archive"'),
            MailboxOption(display_name="Archive", imap_name="Archive"),
        )

    def test_parse_folder_name_with_spaces(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "Project Archive"'),
            MailboxOption(
                display_name="Project Archive",
                imap_name="Project Archive",
            ),
        )

    def test_parse_folder_name_with_punctuation_and_ampersand(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "! choir &- team"'),
            MailboxOption(
                display_name="! choir & team",
                imap_name="! choir &- team",
            ),
        )

    def test_parse_gmail_modified_utf7_folder_name(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "! choir &2DTdHg-"'),
            MailboxOption(
                display_name="! choir \U0001D11E",
                imap_name="! choir &2DTdHg-",
            ),
        )

    def test_parse_escaped_quote_in_quoted_folder_name(self):
        self.assertEqual(
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/" "Project \\"Alpha\\""'),
            MailboxOption(
                display_name='Project "Alpha"',
                imap_name='Project "Alpha"',
            ),
        )

    def test_parse_unquoted_folder_name(self):
        self.assertEqual(
            parse_mailbox_list_entry(b"(\\HasNoChildren) NIL Archive"),
            MailboxOption(display_name="Archive", imap_name="Archive"),
        )

    def test_parse_entries_skips_malformed_entries(self):
        self.assertEqual(
            parse_mailbox_list_entries(
                [
                    b'(\\HasNoChildren) "/" "INBOX"',
                    b'(\\HasNoChildren "/" "Broken"',
                    b'(\xff) "/" "Broken"',
                    b'(\\HasNoChildren) "/" "Archive"',
                ]
            ),
            [
                MailboxOption(display_name="INBOX", imap_name="INBOX"),
                MailboxOption(display_name="Archive", imap_name="Archive"),
            ],
        )

    def test_parse_entry_rejects_missing_mailbox_name(self):
        with self.assertRaises(MailboxParseError):
            parse_mailbox_list_entry(b'(\\HasNoChildren) "/"')


class ModifiedUtf7Tests(unittest.TestCase):
    def test_decode_literal_ampersand(self):
        self.assertEqual(decode_modified_utf7("A&-B"), "A&B")

    def test_decode_non_ascii_character(self):
        self.assertEqual(decode_modified_utf7("Envoy&AOk-"), "Envoyé")

    def test_encode_literal_ampersand(self):
        self.assertEqual(encode_modified_utf7("A&B"), "A&-B")

    def test_encode_non_ascii_character(self):
        self.assertEqual(encode_modified_utf7("Envoyé"), "Envoy&AOk-")

    def test_encode_and_decode_round_trip(self):
        value = "! choir \U0001D11E"

        self.assertEqual(decode_modified_utf7(encode_modified_utf7(value)), value)


class SelectMailboxNameTests(unittest.TestCase):
    def test_atom_mailbox_name_is_not_quoted(self):
        self.assertEqual(select_mailbox_name("INBOX"), "INBOX")

    def test_mailbox_name_with_spaces_is_quoted(self):
        self.assertEqual(
            select_mailbox_name("! choir &2DTdHg-"),
            '"! choir &2DTdHg-"',
        )

    def test_mailbox_name_with_quote_is_escaped(self):
        self.assertEqual(
            select_mailbox_name('Project "Alpha"'),
            '"Project \\"Alpha\\""',
        )

    def test_prepare_select_mailbox_encodes_readable_non_ascii_name(self):
        self.assertEqual(
            prepare_select_mailbox("! choir \U0001D11E"),
            '"! choir &2DTdHg-"',
        )

    def test_prepare_select_mailbox_preserves_protocol_name(self):
        self.assertEqual(
            prepare_select_mailbox("! choir &2DTdHg-", is_protocol_name=True),
            '"! choir &2DTdHg-"',
        )


if __name__ == "__main__":
    unittest.main()
