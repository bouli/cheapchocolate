import base64
from dataclasses import dataclass


@dataclass(frozen=True)
class MailboxOption:
    display_name: str
    imap_name: str


class MailboxParseError(ValueError):
    pass


def select_mailbox_name(imap_name):
    if _is_atom(imap_name):
        return imap_name

    escaped = imap_name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def prepare_select_mailbox(mailbox_name, is_protocol_name=False):
    if is_protocol_name:
        imap_name = mailbox_name
    else:
        imap_name = encode_modified_utf7(mailbox_name)

    return select_mailbox_name(imap_name)


def parse_mailbox_list_entries(entries):
    options = []
    for entry in entries:
        try:
            options.append(parse_mailbox_list_entry(entry))
        except MailboxParseError:
            continue
    return options


def parse_mailbox_list_entry(entry):
    if isinstance(entry, bytes):
        try:
            response = entry.decode("ascii")
        except UnicodeDecodeError as error:
            raise MailboxParseError(
                f"Mailbox list entry is not ASCII encoded: {entry!r}"
            ) from error
    else:
        response = str(entry)

    tokens = _tokenize_list_response(response)
    if len(tokens) < 3:
        raise MailboxParseError(f"Could not parse mailbox list entry: {entry!r}")

    imap_name = tokens[-1]
    return MailboxOption(
        display_name=_decode_display_name(imap_name),
        imap_name=imap_name,
    )


def encode_modified_utf7(value):
    encoded = []
    buffer = []

    def flush_buffer():
        if not buffer:
            return
        utf16_bytes = "".join(buffer).encode("utf-16-be")
        modified = base64.b64encode(utf16_bytes).decode("ascii")
        encoded.append("&" + modified.rstrip("=").replace("/", ",") + "-")
        buffer.clear()

    for character in value:
        codepoint = ord(character)
        if character == "&":
            flush_buffer()
            encoded.append("&-")
        elif 0x20 <= codepoint <= 0x7E:
            flush_buffer()
            encoded.append(character)
        else:
            buffer.append(character)

    flush_buffer()
    return "".join(encoded)


def decode_modified_utf7(value):
    decoded = []
    index = 0

    while index < len(value):
        character = value[index]
        if character != "&":
            decoded.append(character)
            index += 1
            continue

        end_index = value.find("-", index)
        if end_index == -1:
            raise MailboxParseError(f"Invalid modified UTF-7 sequence: {value!r}")

        encoded = value[index + 1 : end_index]
        if encoded == "":
            decoded.append("&")
        else:
            decoded.append(_decode_modified_base64(encoded, value))
        index = end_index + 1

    return "".join(decoded)


def _decode_display_name(imap_name):
    try:
        return decode_modified_utf7(imap_name)
    except MailboxParseError:
        return imap_name


def _decode_modified_base64(encoded, original_value):
    base64_value = encoded.replace(",", "/")
    base64_value += "=" * (-len(base64_value) % 4)

    try:
        return base64.b64decode(base64_value, validate=True).decode("utf-16-be")
    except (UnicodeDecodeError, ValueError) as error:
        raise MailboxParseError(
            f"Invalid modified UTF-7 sequence: {original_value!r}"
        ) from error


def _tokenize_list_response(response):
    tokens = []
    index = 0

    while index < len(response):
        character = response[index]
        if character.isspace():
            index += 1
        elif character == "(":
            token, index = _read_parenthesized(response, index)
            tokens.append(token)
        elif character == '"':
            token, index = _read_quoted(response, index)
            tokens.append(token)
        else:
            token, index = _read_atom(response, index)
            tokens.append(token)

    return tokens


def _read_parenthesized(response, start_index):
    depth = 0
    index = start_index

    while index < len(response):
        character = response[index]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return response[start_index : index + 1], index + 1
        index += 1

    raise MailboxParseError(f"Unclosed parenthesized list: {response!r}")


def _read_quoted(response, start_index):
    value = []
    index = start_index + 1

    while index < len(response):
        character = response[index]
        if character == "\\":
            index += 1
            if index >= len(response):
                raise MailboxParseError(f"Unclosed escape sequence: {response!r}")
            value.append(response[index])
        elif character == '"':
            return "".join(value), index + 1
        else:
            value.append(character)
        index += 1

    raise MailboxParseError(f"Unclosed quoted string: {response!r}")


def _read_atom(response, start_index):
    index = start_index
    while index < len(response) and not response[index].isspace():
        index += 1

    return response[start_index:index], index


def _is_atom(value):
    if value == "":
        return False

    atom_specials = set('(){ %*"\\]')
    for character in value:
        if ord(character) < 0x20 or ord(character) == 0x7F:
            return False
        if character in atom_specials:
            return False

    return True
