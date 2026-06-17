# 🍫 cheapchocolate v0.6.1

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

By default, receiving mail preserves the remote read/unread status of each
message. CheapChocolate downloads messages with a non-mutating IMAP fetch, so
unread messages stay unread on the server and read messages stay read.

To opt into the previous behavior where received messages can be marked read on
the remote mailbox, set `mails.remote_read_state` in your CheapChocolate
`config.yaml`:

```yaml
mails:
  days_to_fetch: 1
  remote_read_state: mark_read
```

The safe default is:

```yaml
mails:
  remote_read_state: preserve
```

For a one-off receive run, override the saved setting from the command line:

```shell
cheapchocolate start --remote-read-state preserve
cheapchocolate start --remote-read-state mark_read
```

You can still receive a specific folder with the same read-state override:

```shell
cheapchocolate start --folder inbox --remote-read-state preserve
```

## See Also

- Github: https://github.com/bouli/cheapchocolate
- PyPI: https://pypi.org/project/cheapchocolate/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
