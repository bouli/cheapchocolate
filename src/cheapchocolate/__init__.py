import argparse

from cheapchocolate.core import config
from cheapchocolate.modules.imap import get_folders, get_mails

# import getpass


def main():
    parser = argparse.ArgumentParser(prog="cheapchocolate")
    parser.add_argument("--version", action="version", version="%(prog)s v0.5.4")

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
        "--remote-read-state",
        choices=sorted(config.VALID_REMOTE_READ_STATES),
        default=None,
        help=(
            "Override receive read-state behavior for this run: preserve remote "
            "status or mark_read while receiving."
        ),
    )

    folder_parser = subparsers.add_parser(
        "folders",
        help="🗂️ Look for folder of my mailbox.",
    )
    args = parser.parse_args()

    if args.command == "start":
        get_mails(args.folder, remote_read_state=args.remote_read_state)

    if args.command == "folders":
        get_folders()

    return


if __name__ == "__main__":
    main()
