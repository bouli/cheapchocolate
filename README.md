# 🍫 cheapchocolate v0.5.1

CheapChocolate is an simple imap client to receive you daily email.


## Installation

You can install directly in your `pip`:
```shell
pip install cheapchocolate
```

I recomend to use the [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), so you can just use the command bellow and everything is installed:
```shell
uv add cheapchocolate
uv run cheapchocolate --version
```

But you can use everything as a tool, for example:
```shell
uvx cheapchocolate --version
```

## How to use

Set up your information in the `.env` file for your imap server, your user and password.
```shell
cheapchocolate start
```
> You can run `cheapchocolate start`, and it will create the file for you.

By default, CheapChocolate preserves the remote read/unread status of your emails.
Unread messages stay unread on the IMAP server after they are received locally.

To receive a specific folder:
```shell
cheapchocolate start --folder inbox
```

To override the remote read status behavior for one run:
```shell
cheapchocolate start --remote-read-status preserve
cheapchocolate start --remote-read-status mark_read
```

`preserve` keeps the remote status unchanged. `mark_read` marks a message as read on
the remote mailbox after CheapChocolate writes the local copy.

To make `mark_read` the default behavior, update your `cheapchocolate/config.yaml`:
```yaml
mails:
  days_to_fetch: 1
  remote_read_status: mark_read
```

Use `remote_read_status: preserve` to return to the safe default.

## See Also

- Github: https://github.com/bouli/cheapchocolate
- PyPI: https://pypi.org/project/cheapchocolate/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
