from cheapchocolate.core import config


def test_get_dir_returns_default_app_dir_and_creates_it_when_missing(monkeypatch):
    created_folders = []

    monkeypatch.setattr(config.os.path, "exists", lambda folder: False)
    monkeypatch.setattr(config.os, "mkdir", created_folders.append)

    assert config.get_dir() == "./cheapchocolate"
    assert created_folders == ["./cheapchocolate"]


def test_get_dir_returns_configured_dir_and_does_not_create_existing_folder(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "get_param",
        lambda parent_param, param, default_app_dir: calls.append(
            (parent_param, param, default_app_dir)
        )
        or "./mailbox",
    )
    monkeypatch.setattr(config.os.path, "exists", lambda folder: True)
    monkeypatch.setattr(config.os, "mkdir", lambda folder: (_ for _ in ()).throw(AssertionError))

    assert config.get_dir("mailbox") == "./mailbox"
    assert calls == [("default_dirs", "mailbox", "cheapchocolate")]


def test_get_mails_reads_from_mails_config(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "get_param",
        lambda parent_param, param, default_app_dir: calls.append(
            (parent_param, param, default_app_dir)
        )
        or 1,
    )

    assert config.get_mails("days_to_fetch") == 1
    assert calls == [("mails", "days_to_fetch", "cheapchocolate")]


def test_load_config_returns_valid_config(monkeypatch):
    calls = []
    loaded_config = {"default_dirs": {"mailbox": "./mailbox"}}

    monkeypatch.setattr(
        config.config_files,
        "create_and_read_config_file",
        lambda file_name, default_app_dir, force_default=False: calls.append(
            (file_name, default_app_dir, force_default)
        )
        or loaded_config,
    )

    assert config.load_config() == loaded_config
    assert calls == [("config.yaml", "cheapchocolate", False)]


def test_load_config_reloads_defaults_when_config_is_missing_default_dirs(monkeypatch):
    calls = []
    responses = [
        {"mails": {"days_to_fetch": 1}},
        {"default_dirs": {"mailbox": "./mailbox"}},
    ]

    monkeypatch.setattr(
        config.config_files,
        "create_and_read_config_file",
        lambda file_name, default_app_dir, force_default=False: calls.append(
            (file_name, default_app_dir, force_default)
        )
        or responses.pop(0),
    )

    assert config.load_config() == {"default_dirs": {"mailbox": "./mailbox"}}
    assert calls == [
        ("config.yaml", "cheapchocolate", False),
        ("config.yaml", "cheapchocolate", True),
    ]


def test_get_files_reads_from_default_files_config(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "get_param",
        lambda parent_param, param, default_app_dir: calls.append(
            (parent_param, param, default_app_dir)
        )
        or "mail_folders.yaml",
    )

    assert config.get_files("mail_folders") == "mail_folders.yaml"
    assert calls == [("default_files", "mail_folders", "cheapchocolate")]


def test_get_param_delegates_to_config_files(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "get_param",
        lambda parent_param, param, default_app_dir: calls.append(
            (parent_param, param, default_app_dir)
        )
        or "value",
    )

    assert config.get_param("section", "key") == "value"
    assert calls == [("section", "key", "cheapchocolate")]


def test_get_mail_folders_reads_configured_mail_folders_file(monkeypatch):
    calls = []

    monkeypatch.setattr(config, "get_files", lambda param: "mail_folders.yaml")
    monkeypatch.setattr(
        config.config_files,
        "create_and_read_config_file",
        lambda file_name, default_app_dir, complete_file=True: calls.append(
            (file_name, default_app_dir, complete_file)
        )
        or {"inbox": {"days_to_fetch": 0}},
    )

    assert config.get_mail_folders() == {"inbox": {"days_to_fetch": 0}}
    assert calls == [("mail_folders.yaml", "cheapchocolate", False)]


def test_add_mail_folder_appends_folder_with_default_days_to_fetch(monkeypatch):
    appended = []

    monkeypatch.setattr(config, "get_files", lambda param: "mail_folders.yaml")
    monkeypatch.setattr(config, "get_mails", lambda param: 2)
    monkeypatch.setattr(
        config,
        "_append_config_file",
        lambda data, file_name: appended.append((data, file_name)),
    )

    config.add_mail_folder("archive")

    assert appended == [
        ({"archive": {"days_to_fetch": 2}}, "mail_folders.yaml"),
    ]


def test_overwrite_config_file_delegates_with_default_app_dir(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "overwrite_config_file",
        lambda data, file_name, default_app_dir: calls.append(
            (data, file_name, default_app_dir)
        ),
    )

    config.overwrite_config_file({"mails": {}}, "config.yaml")

    assert calls == [({"mails": {}}, "config.yaml", "cheapchocolate")]


def test_append_config_file_delegates_with_default_app_dir(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.config_files,
        "append_config_file",
        lambda data, file_name, default_app_dir: calls.append(
            (data, file_name, default_app_dir)
        ),
    )

    config._append_config_file({"inbox": {}}, "mail_folders.yaml")

    assert calls == [({"inbox": {}}, "mail_folders.yaml", "cheapchocolate")]
