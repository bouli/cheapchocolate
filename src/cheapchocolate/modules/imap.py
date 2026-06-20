import email
import getpass
import imaplib
import os
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path

from dotenv import load_dotenv

from cheapchocolate.core import config
from cheapchocolate.modules.imap_mailbox import (
    parse_mailbox_list_entries,
    select_mailbox_name,
)
from cheapchocolate.modules.mailbox import get_local_mailbox_folder, get_local_mails

NON_MUTATING_MESSAGE_FETCH = "(BODY.PEEK[])"
MUTATING_MESSAGE_FETCH = "(RFC822)"
DUPLICATE_CHECK_FETCH = "(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)])"


def get_env_file_path():
    return Path.cwd() / ".env"


def get_imap_connection():
    load_dotenv(dotenv_path=get_env_file_path())
    if os.getenv("user") is None or os.getenv("user") == "myuser@my-mail.server":
        create_env_file()
        print(
            "🫠 Appearently you did't set up your `.env` file to connect to your email service."
        )
        return None
    try:
        print("☎️  Calling your imap server...")
        imap_connection = imaplib.IMAP4_SSL(os.getenv("server"))
        imap_connection.login(os.getenv("user"), get_imap_password())
        print("🙌 It worked!")
    except:
        print("😅 Oops! We cannot login, can you please check your `/.env` file?")
        return None
    return imap_connection


def get_imap_password():
    password = os.getenv("password")
    if password:
        return password

    return getpass.getpass(f"IMAP password: ")


def create_env_file():
    env_file_path = get_env_file_path()
    if not env_file_path.exists():
        with env_file_path.open("+a") as f:
            f.write("user=myuser@my-mail.server\n")
            f.write("password=mypassword\n")
            f.write("server=imap.my-mail.server\n")


def get_folders():
    imap_connection = get_imap_connection()
    if imap_connection is None:
        return
    print("🗣️  Asking for your folders...")
    result, folders_list = imap_connection.list()

    if len(folders_list) == 0:
        print(f"😅 You have no new folder...")
        close_imap_connection(imap_connection)
        return
    folder_options = parse_mailbox_list_entries(folders_list)
    if len(folder_options) == 0:
        print(f"😅 You have no new folder...")
        close_imap_connection(imap_connection)
        return

    print("These are your folder from your online 📫 mailbox: ")
    for index, folder in enumerate(folder_options):
        print(f"[{index}] {folder.display_name}")

    user_option = -1
    while user_option < 0 or user_option >= len(folder_options):
        user_option = input(
            "Choose one of the online 🗂️ folders above to receive the emails or `q` to quit: "
        )
        if user_option == "q":
            return
        elif user_option.isdigit():
            user_option = int(user_option)
            if user_option >= 0 and user_option < len(folder_options):
                selected_folder = folder_options[user_option]
                mail_folder = selected_folder.display_name
                _get_mails(
                    mail_folder=mail_folder,
                    imap_mailbox=select_mailbox_name(selected_folder.imap_name),
                    imap_connection=imap_connection,
                    remote_read_state=config.get_remote_read_state(),
                )
                mail_folders = config.get_mail_folders()
                if mail_folder not in mail_folders.keys():
                    add_default_folder = input(
                        f"🗃️ Would you like to add `{mail_folder}` to your default `mail_folder`? [Y]es or anything else to No: "
                    )
                    if add_default_folder.upper() == "Y":
                        config.add_mail_folder(mail_folder)
                        print(f"🗃️ {mail_folder} added to your default `mail_folder`.")
            else:
                user_option = -1
        else:
            user_option = -1
    return


def _clean_folder_name(folder):
    folder_name = str(folder).split('"/" "')[1].replace("\"'", "")
    return folder_name


def get_mails(mail_folder="mail_folders", remote_read_state=None):
    if mail_folder != "mail_folders":
        _get_mails(mail_folder=mail_folder, remote_read_state=remote_read_state)
    else:
        mail_folders = config.get_mail_folders()
        imap_connection = get_imap_connection()
        if imap_connection is None:
            return False

        for mail_folder, data in mail_folders.items():
            _get_mails(
                mail_folder=mail_folder,
                days_to_fetch=int(data["days_to_fetch"]),
                imap_connection=imap_connection,
                let_imap_connection_opened=True,
                remote_read_state=remote_read_state,
            )

        close_imap_connection(imap_connection)
        print("🍫 We are done, let`s have a dessert...")


def _get_mails(
    mail_folder="inbox",
    days_to_fetch: int = 0,
    imap_connection=None,
    imap_mailbox=None,
    let_imap_connection_opened=False,
    remote_read_state=None,
):
    if days_to_fetch == 0:
        days_to_fetch = int(config.get_mails("days_to_fetch"))
    if remote_read_state is None:
        remote_read_state = config.get_remote_read_state()

    days_to_fetch = days_to_fetch * -1

    today = datetime.today().date()
    time = (today + timedelta(days=days_to_fetch)).strftime("%d-%b-%Y")

    if imap_connection is None:
        imap_connection = get_imap_connection()
        if imap_connection is None:
            return False

    select_mailbox = imap_mailbox if imap_mailbox is not None else mail_folder
    imap_connection.select(select_mailbox)

    print(f"🗣️  Asking for the today`s mail in {mail_folder} (since {time})...")
    result, data = imap_connection.search(None, f"SINCE {time}")
    mails_to_receive = data[0].split()

    if len(mails_to_receive) == 0:
        print(f"📭 You have no new mails in {mail_folder}...")
        if not let_imap_connection_opened:
            close_imap_connection(imap_connection)
        return

    print(f"🗃️  You have {len(mails_to_receive)} mails to sync...")

    for email_id in mails_to_receive:
        load_email_by_id(
            imap_connection=imap_connection,
            email_id=email_id,
            mail_folder=mail_folder,
            remote_read_state=remote_read_state,
        )

    if not let_imap_connection_opened:
        close_imap_connection(imap_connection)
        print("🍫 We are done, let`s have a dessert...")


def load_email_by_id(
    imap_connection,
    email_id,
    mail_folder="inbox",
    remote_read_state=config.REMOTE_READ_STATE_PRESERVE,
):

    result, header_data = imap_connection.fetch(email_id, DUPLICATE_CHECK_FETCH)
    header_msg = email.message_from_bytes(header_data[0][1])
    mailbox_file = local_mailbox_file_path(header_msg, mail_folder)

    if os.path.exists(mailbox_file):
        print(
            f'📜 {mailbox_file.stem.replace(f" [{mail_folder}]", "")} previously downloaded...'
        )
        return False

    message_fetch = message_fetch_for_remote_read_state(remote_read_state)
    result, msg_data = imap_connection.fetch(email_id, message_fetch)

    msg = email.message_from_bytes(msg_data[0][1])

    if msg.is_multipart():
        for msg_part in msg.walk():
            try:
                body = msg_part.get_payload(decode=True).decode()
            except:
                pass
    else:
        body = msg.get_payload(decode=True).decode()
    with open(mailbox_file, "+w") as f:
        mail_string = ""
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="from: " + extract_from_header(msg=msg, key="from"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="to: " + extract_from_header(msg=msg, key="to"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line='subject: "' + extract_from_header(msg=msg, key="subject") + '"',
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="date: " + extract_from_header(msg=msg, key="date"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line='mail_folder: "' + mail_folder + '"',
        )
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        mail_string = add_mail_line(mail_string=mail_string, line=body)
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        f.write(mail_string)
        print(f'📨 {mailbox_file.stem.replace(f" [{mail_folder}]", "")} received...')
        return True


def local_mailbox_file_path(msg, mail_folder):
    email_id = imaptime2datetime(extract_from_header(msg=msg, key="date"))
    subject_file_name = (
        extract_from_header(msg=msg, key="subject").replace("'", "").replace("/", "")
    )
    return Path(
        get_local_mailbox_folder(),
        f"{email_id} - {subject_file_name} [{mail_folder}].md",
    )


def message_fetch_for_remote_read_state(remote_read_state):
    if config.should_mark_remote_read(remote_read_state):
        return MUTATING_MESSAGE_FETCH
    return NON_MUTATING_MESSAGE_FETCH


def imaptime2datetime(imap_time):
    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    imap_time = imap_time.split(",")[1].strip().split(" ")
    return (
        imap_time[2]
        + months[imap_time[1]]
        + imap_time[0]
        + imap_time[3].replace(":", "")
    )


def add_mail_line(line, mail_string, verbose=False):
    mail_string = mail_string + "\n" + line
    if verbose:
        print(line)
    return mail_string.strip()


def extract_from_header(msg, key):
    value, encoding = decode_header(msg[key])[0]
    if isinstance(value, bytes) and isinstance(encoding, str):
        value = value.decode(encoding)
    else:
        value = str(value)
    return value


def close_imap_connection(imap_connection: imaplib.IMAP4_SSL):

    imap_connection.close()
    imap_connection.logout()
    print(f"👋 Tschüss...")
