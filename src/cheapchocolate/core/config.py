import os
from cheapchocolate.core import config_files

default_app_dir = "cheapchocolate"


def get_dir(param="cheapchocolate"):
    parent_param = "default_dirs"

    if param == default_app_dir:
        folder = "./" + param
    else:
        folder = config_files.get_param(
            parent_param=parent_param, param=param, default_app_dir=default_app_dir
        )
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder


def get_mails(param):
    parent_param = "mails"
    return config_files.get_param(
        parent_param=parent_param, param=param, default_app_dir=default_app_dir
    )


def load_config(force_default=False):
    config_file_name = "config.yaml"
    config_params = config_files.create_and_read_config_file(
        file_name=config_file_name,
        default_app_dir=default_app_dir,
        force_default=force_default,
    )

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params


def get_files(param):
    parent_param = "default_files"
    return config_files.get_param(
        parent_param=parent_param, param=param, default_app_dir=default_app_dir
    )


def get_param(parent_param, param):
    return config_files.get_param(
        parent_param=parent_param, param=param, default_app_dir=default_app_dir
    )


def get_mail_folders():
    mail_folders = get_files(param="mail_folders")
    return config_files.create_and_read_config_file(
        file_name=mail_folders,
        default_app_dir=default_app_dir,
    )


def add_mail_folder(mail_folder):
    mail_folders = get_files(param="mail_folders")
    data = {mail_folder: {"days_to_fetch": get_mails("days_to_fetch")}}
    _append_config_file(data, file_name=mail_folders)


def overwrite_config_file(data, file_name):
    config_files.overwrite_config_file(data, file_name, default_app_dir=default_app_dir)


def _append_config_file(data, file_name):
    config_files.append_config_file(data, file_name, default_app_dir=default_app_dir)


get_mail_folders()
