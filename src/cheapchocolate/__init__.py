import argparse

import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime, timedelta
# import getpass

load_dotenv()


def main():
    parser = argparse.ArgumentParser(prog="cheapchocolate")
    parser.add_argument("--version", action="version", version="%(prog)s v0.2.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    start_parser = subparsers.add_parser(
        "start",
        help="📨 Get today's emails.",
    )

    start_parser = subparsers.add_parser(
        "check-mailbox",
        help="📫 Check local mailbox.",
    )
    args = parser.parse_args()

    if args.command == "start" :
        get_mails()

    return

def get_mails():

    today = datetime.today().date()
    time = (today + timedelta(days=-1)).strftime("%d-%b-%Y")
    if os.getenv("user") is None or os.getenv("user") == "myuser@my-mail.server":
        create_env_file()
        print(
            "🫠 Appearently you did't set up your `/.env` file to connect to your email service."
        )
        return
    try:
        print("☎️ Calling your imap server...")
        imap_connection = imaplib.IMAP4_SSL(os.getenv("server"))
        imap_connection.login(os.getenv("user"), os.getenv("password"))
        print("🙌 It worked!")
    except:
        print("😅 Oops! We cannot login, can you please check your `/.env` file?")
        return

    imap_connection.select("inbox")

    print("🗣️ Asking for the today`s mail...")
    result, data = imap_connection.search(None, f"SINCE {time}")
    remote_mails = data[0].split()

    local_mails = get_local_mails()
    mails_to_receive = []
    for remote_mail_id in remote_mails:
        if str(remote_mail_id).replace("'","") not in local_mails:
            mails_to_receive.append(remote_mail_id)

    if len(mails_to_receive) == 0:
        print(f"📭 You have no new mails...")
        imap_connection.close()
        imap_connection.logout()
        return

    print(f"🗃️ You have {len(mails_to_receive)} mails...")

    for email_id in mails_to_receive:
        load_email_by_id(imap_connection, email_id)
    imap_connection.close()
    imap_connection.logout()

    print("🍫 We are done, let`s have a dessert...")


def load_email_by_id(imap_connection, email_id):

    result, msg_data = imap_connection.fetch(email_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    if msg.is_multipart():
        for msg_part in msg.walk():
            try:
                body = msg_part.get_payload(decode=True).decode()
            except:
                pass
    else:
        body = msg.get_payload(decode=True).decode()
    email_id = str(email_id).replace("'", "")
    if not os.path.exists("mailbox"):
        os.mkdir("mailbox")
    with open(
        f'mailbox/{email_id} - {extract_from_header(msg=msg, key="subject")}.md', "+w"
    ) as f:
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
            line="subject: " + extract_from_header(msg=msg, key="subject"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="date: " + extract_from_header(msg=msg, key="date"),
        )
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        mail_string = add_mail_line(mail_string=mail_string, line=body)
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        f.write(mail_string)
        print(
            f'📨 {email_id} - {extract_from_header(msg=msg, key="subject")} received...'
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


def create_env_file():
    if not os.path.exists(".env"):
        with open(".env", "+a") as f:
            f.write("user=myuser@my-mail.server\n")
            f.write("password=mypassword\n")
            f.write("server=imap.my-mail.server\n")

def get_local_mails():
    mails = []
    for mail_file in os.listdir('mailbox'):
        mail_file.split(" - ")[0]
        mails.append(mail_file.split(" - ")[0])
    return mails

if __name__ == "__main__":
    main()
