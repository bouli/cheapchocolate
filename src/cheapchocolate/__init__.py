import argparse
from cheapchocolate.modules.imap import get_mails, get_folders
# import getpass

def main():
    parser = argparse.ArgumentParser(prog="cheapchocolate")
    parser.add_argument("--version", action="version", version="%(prog)s v0.2.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    start_parser = subparsers.add_parser(
        "start",
        help="📨 Get today's emails.",
    )

    args = parser.parse_args()

    if args.command == "start" :
        get_mails()

    return

if __name__ == "__main__":
    main()
