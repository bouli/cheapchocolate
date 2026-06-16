import yaml

from cheapchocolate.core import config, config_files


def test_load_config_creates_safe_default_remote_read_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    loaded_config = config.load_config()

    assert loaded_config["mails"]["remote_read_state"] == "preserve"
    assert config.get_remote_read_state() == "preserve"


def test_existing_config_is_completed_with_remote_read_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app_dir = tmp_path / config.default_app_dir
    app_dir.mkdir()
    config_file = app_dir / "config.yaml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "default_dirs": {"mailbox": "./custom-mailbox"},
                "default_files": {"mail_folders": "custom-folders.yaml"},
                "mails": {"days_to_fetch": 7},
            }
        )
    )

    loaded_config = config.load_config()

    assert loaded_config["mails"] == {
        "days_to_fetch": 7,
        "remote_read_state": "preserve",
    }
    assert loaded_config["default_dirs"]["mailbox"] == "./custom-mailbox"
    assert loaded_config["default_files"]["mail_folders"] == "custom-folders.yaml"

    written_config = yaml.safe_load(config_file.read_text())
    assert written_config == loaded_config


def test_explicit_mark_read_config_is_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app_dir = tmp_path / config.default_app_dir
    app_dir.mkdir()
    (app_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "default_dirs": {"mailbox": "./mailbox"},
                "default_files": {"mail_folders": "mail_folders.yaml"},
                "mails": {
                    "days_to_fetch": 1,
                    "remote_read_state": "mark_read",
                },
            }
        )
    )

    assert config.get_remote_read_state() == "mark_read"
    assert config.should_mark_remote_read()


def test_invalid_remote_read_state_raises_predictable_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app_dir = tmp_path / config.default_app_dir
    app_dir.mkdir()
    (app_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "default_dirs": {"mailbox": "./mailbox"},
                "default_files": {"mail_folders": "mail_folders.yaml"},
                "mails": {
                    "days_to_fetch": 1,
                    "remote_read_state": "sometimes",
                },
            }
        )
    )

    try:
        config.get_remote_read_state()
    except ValueError as error:
        assert "Invalid mails.remote_read_state: sometimes" in str(error)
        assert "mark_read" in str(error)
        assert "preserve" in str(error)
    else:
        raise AssertionError("Expected invalid remote_read_state to raise ValueError")


def test_complete_config_file_preserves_existing_nested_values(tmp_path):
    app_dir = tmp_path / "cheapchocolate"
    app_dir.mkdir()
    config_file = app_dir / "config.yaml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "default_dirs": {"mailbox": "./custom-mailbox"},
                "default_files": {"mail_folders": "mail_folders.yaml"},
                "mails": {"days_to_fetch": 3},
            }
        )
    )

    config_files.create_and_read_config_file(
        file_name="config.yaml",
        default_app_dir=str(app_dir),
    )

    assert yaml.safe_load(config_file.read_text())["mails"] == {
        "days_to_fetch": 3,
        "remote_read_state": "preserve",
    }
