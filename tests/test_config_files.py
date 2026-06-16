import pytest
import yaml

from cheapchocolate.core import config_files


def test_config_file_path_ensures_default_app_dir(tmp_path):
    app_dir = tmp_path / "cheapchocolate"

    path = config_files.config_file_path("config.yaml", str(app_dir))

    assert path == str(app_dir / "config.yaml")
    assert app_dir.is_dir()


def test_config_file_exists_returns_false_when_missing_and_creates_app_dir(tmp_path):
    app_dir = tmp_path / "cheapchocolate"

    assert config_files.config_file_exists("config.yaml", str(app_dir)) is False
    assert app_dir.is_dir()


def test_overwrite_config_file_writes_yaml(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    data = {"mails": {"days_to_fetch": 3}}

    config_files.overwrite_config_file(data, "config.yaml", str(app_dir))

    assert yaml.safe_load((app_dir / "config.yaml").read_text()) == data


def test_append_config_file_merges_data_and_prevents_duplicate_keys(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    config_files.overwrite_config_file(
        {"inbox": {"days_to_fetch": 1}},
        "mail_folders.yaml",
        str(app_dir),
    )

    config_files.append_config_file(
        {
            "archive": {"days_to_fetch": 5},
            "inbox": {"days_to_fetch": 2},
        },
        "mail_folders.yaml",
        str(app_dir),
    )

    assert yaml.safe_load((app_dir / "mail_folders.yaml").read_text()) == {
        "archive": {"days_to_fetch": 5},
        "inbox": {"days_to_fetch": 2},
    }


def test_complete_config_file_appends_missing_default_sections(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    config_files.overwrite_config_file(
        {"default_dirs": {"mailbox": "./mailbox"}},
        "config.yaml",
        str(app_dir),
    )

    updated = config_files.complete_config_file(
        config_params={"default_dirs": {"mailbox": "./mailbox"}},
        default_config_params={
            "default_dirs": {"mailbox": "./mailbox"},
            "mails": {"days_to_fetch": 1},
        },
        file_name="config.yaml",
        default_app_dir=str(app_dir),
    )

    assert updated is True
    assert yaml.safe_load((app_dir / "config.yaml").read_text()) == {
        "default_dirs": {"mailbox": "./mailbox"},
        "mails": {"days_to_fetch": 1},
    }


def test_complete_config_file_adds_missing_nested_default_values(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    config_files.overwrite_config_file(
        {"mails": {"days_to_fetch": 1}},
        "config.yaml",
        str(app_dir),
    )

    updated = config_files.complete_config_file(
        config_params={"mails": {"days_to_fetch": 1}},
        default_config_params={
            "mails": {
                "days_to_fetch": 1,
                "remote_read_status": "preserve",
            },
        },
        file_name="config.yaml",
        default_app_dir=str(app_dir),
    )

    assert updated is True
    assert yaml.safe_load((app_dir / "config.yaml").read_text()) == {
        "mails": {
            "days_to_fetch": 1,
            "remote_read_status": "preserve",
        },
    }


def test_complete_config_file_returns_false_when_no_update_is_needed(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    config_params = {"default_dirs": {}, "mails": {}}

    updated = config_files.complete_config_file(
        config_params=config_params,
        default_config_params={"default_dirs": {}, "mails": {}},
        file_name="config.yaml",
        default_app_dir=str(app_dir),
    )

    assert updated is False
    assert not (app_dir / "config.yaml").exists()


def test_create_and_read_config_file_writes_defaults_when_file_is_missing(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "cheapchocolate"
    default_config = {"mails": {"days_to_fetch": 1}}

    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert (
        config_files.create_and_read_config_file("config.yaml", str(app_dir))
        == default_config
    )
    assert yaml.safe_load((app_dir / "config.yaml").read_text()) == default_config


def test_create_and_read_config_file_reads_existing_file(tmp_path, monkeypatch):
    app_dir = tmp_path / "cheapchocolate"
    existing_config = {"mails": {"days_to_fetch": 7}}
    default_config = {"mails": {"days_to_fetch": 1}}

    config_files.overwrite_config_file(existing_config, "config.yaml", str(app_dir))
    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert (
        config_files.create_and_read_config_file("config.yaml", str(app_dir))
        == existing_config
    )


def test_create_and_read_config_file_completes_existing_file(tmp_path, monkeypatch):
    app_dir = tmp_path / "cheapchocolate"
    existing_config = {"default_dirs": {"mailbox": "./mailbox"}}
    default_config = {
        "default_dirs": {"mailbox": "./mailbox"},
        "mails": {"days_to_fetch": 1, "remote_read_status": "preserve"},
    }

    config_files.overwrite_config_file(existing_config, "config.yaml", str(app_dir))
    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert config_files.create_and_read_config_file("config.yaml", str(app_dir)) == {
        "default_dirs": {"mailbox": "./mailbox"},
        "mails": {"days_to_fetch": 1, "remote_read_status": "preserve"},
    }


def test_create_and_read_config_file_preserves_incomplete_file_when_completion_disabled(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "cheapchocolate"
    existing_config = {"inbox": {"days_to_fetch": 0}}
    default_config = {
        "inbox": {"days_to_fetch": 0},
        "archive": {"days_to_fetch": 1},
    }

    config_files.overwrite_config_file(
        existing_config,
        "mail_folders.yaml",
        str(app_dir),
    )
    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert config_files.create_and_read_config_file(
        "mail_folders.yaml",
        str(app_dir),
        complete_file=False,
    ) == {"inbox": {"days_to_fetch": 0}}


def test_create_and_read_config_file_uses_defaults_when_force_default_is_true(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "cheapchocolate"
    existing_config = {"mails": {"days_to_fetch": 7}}
    default_config = {"mails": {"days_to_fetch": 1}}

    config_files.overwrite_config_file(existing_config, "config.yaml", str(app_dir))
    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert config_files.create_and_read_config_file(
        "config.yaml",
        str(app_dir),
        force_default=True,
    ) == default_config
    assert yaml.safe_load((app_dir / "config.yaml").read_text()) == default_config


def test_create_and_read_config_file_restores_defaults_when_yaml_is_empty(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "cheapchocolate"
    default_config = {"mails": {"days_to_fetch": 1}}

    config_files.config_file_path("config.yaml", str(app_dir))
    (app_dir / "config.yaml").write_text("")
    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert (
        config_files.create_and_read_config_file("config.yaml", str(app_dir))
        == default_config
    )


def test_get_param_returns_nested_config_value(tmp_path, monkeypatch):
    app_dir = tmp_path / "cheapchocolate"
    default_config = {"default_dirs": {"mailbox": "./mailbox"}}

    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    assert config_files.get_param("default_dirs", "mailbox", str(app_dir)) == "./mailbox"


def test_get_param_raises_when_param_is_missing(tmp_path, monkeypatch):
    app_dir = tmp_path / "cheapchocolate"
    default_config = {"default_dirs": {"mailbox": "./mailbox"}}

    monkeypatch.setattr(
        config_files,
        "_get_default_file",
        lambda default_file: default_config,
    )

    with pytest.raises(Exception, match="missing do not exist in your params default_dirs"):
        config_files.get_param("default_dirs", "missing", str(app_dir))


def test_get_default_file_reads_packaged_default_yaml():
    assert config_files._get_default_file("config.yaml") == {
        "default_dirs": {"mailbox": "./mailbox"},
        "default_files": {"mail_folders": "mail_folders.yaml"},
        "mails": {"days_to_fetch": 1, "remote_read_status": "preserve"},
    }
