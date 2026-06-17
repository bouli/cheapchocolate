import os

import conveoconfi

default_app_dir = "cheapchocolate"
default_files_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "default_files"
)
REMOTE_READ_STATE_PRESERVE = "preserve"
REMOTE_READ_STATE_MARK_READ = "mark_read"
VALID_REMOTE_READ_STATES = {
    REMOTE_READ_STATE_PRESERVE,
    REMOTE_READ_STATE_MARK_READ,
}


def get_dir(param="cheapchocolate"):
    parent_param = "default_dirs"

    if param == default_app_dir:
        folder = "./" + param
    else:
        folder = conveoconfi.get_param(
            parent_param=parent_param,
            param=param,
            default_app_dir=default_app_dir,
            default_files_dir=default_files_dir,
        )
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder


def get_mails(param):
    parent_param = "mails"
    return conveoconfi.get_param(
        parent_param=parent_param,
        param=param,
        default_app_dir=default_app_dir,
        default_files_dir=default_files_dir,
    )


def get_remote_read_state():
    remote_read_state = get_mails("remote_read_state")
    if remote_read_state not in VALID_REMOTE_READ_STATES:
        valid_values = ", ".join(sorted(VALID_REMOTE_READ_STATES))
        raise ValueError(
            f"Invalid mails.remote_read_state: {remote_read_state}. "
            f"Expected one of: {valid_values}."
        )
    return remote_read_state


def should_mark_remote_read(remote_read_state=None):
    if remote_read_state is None:
        remote_read_state = get_remote_read_state()
    elif remote_read_state not in VALID_REMOTE_READ_STATES:
        valid_values = ", ".join(sorted(VALID_REMOTE_READ_STATES))
        raise ValueError(
            f"Invalid mails.remote_read_state: {remote_read_state}. "
            f"Expected one of: {valid_values}."
        )
    return remote_read_state == REMOTE_READ_STATE_MARK_READ


def load_config(force_default=False):
    config_file_name = "config.yaml"
    config_params = conveoconfi.create_and_read_config_file(
        file_name=config_file_name,
        default_app_dir=default_app_dir,
        force_default=force_default,
        default_files_dir=default_files_dir,
    )

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params


def get_files(param):
    parent_param = "default_files"
    return conveoconfi.get_param(
        parent_param=parent_param,
        param=param,
        default_app_dir=default_app_dir,
        default_files_dir=default_files_dir,
    )


def get_param(parent_param, param):
    return conveoconfi.get_param(
        parent_param=parent_param,
        param=param,
        default_app_dir=default_app_dir,
        default_files_dir=default_files_dir,
    )


def get_mail_folders():
    mail_folders = get_files(param="mail_folders")
    return conveoconfi.create_and_read_config_file(
        file_name=mail_folders,
        default_app_dir=default_app_dir,
        complete_file=False,
        default_files_dir=default_files_dir,
    )


def add_mail_folder(mail_folder):
    mail_folders = get_files(param="mail_folders")
    data = {mail_folder: {"days_to_fetch": get_mails("days_to_fetch")}}
    _append_config_file(data, file_name=mail_folders)


def overwrite_config_file(data, file_name):
    conveoconfi.overwrite_config_file(
        file_name=file_name, default_app_dir=default_app_dir, data=data
    )


def _append_config_file(data, file_name):
    conveoconfi.append_config_file(
        file_name=file_name, default_app_dir=default_app_dir, data=data
    )
