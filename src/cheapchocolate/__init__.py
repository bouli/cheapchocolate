import argparse
from cheapchocolate.modules.imap import get_mails, get_folders

# import getpass


def main():
    parser = argparse.ArgumentParser(prog="cheapchocolate")
    parser.add_argument("--version", action="version", version="%(prog)s v0.5.1")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    start_parser = subparsers.add_parser(
        "start",
        help="📨 Get today's emails.",
    )
    start_parser.add_argument(
        "--folder",
        default="mail_folders",
        help="Choose an specific mailbox folder to check.",
    )
    start_parser.add_argument(
        "--remote-read-status",
        choices=["preserve", "mark_read"],
        default=None,
        help="Choose whether receiving mail preserves remote read status or marks mail read.",
    )

    folder_parser = subparsers.add_parser(
        "folders",
        help="🗂️ Look for folder of my mailbox.",
    )
    args = parser.parse_args()

    if args.command == "start":
        get_mails(args.folder, remote_read_status=args.remote_read_status)

    if args.command == "folders":
        get_folders()

    return


if __name__ == "__main__":
    main()
