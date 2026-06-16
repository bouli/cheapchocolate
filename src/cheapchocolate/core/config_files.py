import os

import yaml


def create_and_read_config_file(
    file_name, default_app_dir, force_default=False, complete_file=True
):
    config_file = config_file_path(file_name, default_app_dir)
    default_config_params = _get_default_file(default_file=file_name)
    if force_default or not os.path.exists(config_file):
        overwrite_config_file(
            data=default_config_params,
            file_name=file_name,
            default_app_dir=default_app_dir,
        )
        config_params = default_config_params
    else:
        with open(config_file, "r") as f:
            config_params = yaml.safe_load(f.read())
        if complete_file:
            if complete_config_file(
                config_params=config_params,
                default_config_params=default_config_params,
                file_name=file_name,
                default_app_dir=default_app_dir,
            ):
                config_params = create_and_read_config_file(
                    file_name=file_name,
                    default_app_dir=default_app_dir,
                    force_default=force_default,
                )

    if config_params is None:
        config_params = create_and_read_config_file(
            file_name=file_name, default_app_dir=default_app_dir, force_default=True
        )
    return config_params


def complete_config_file(
    config_params, default_config_params, file_name, default_app_dir
):
    has_updated = False
    completed_config_params = _complete_missing_values(
        config_params=config_params,
        default_config_params=default_config_params,
    )
    if completed_config_params != config_params:
        has_updated = True
        overwrite_config_file(completed_config_params, file_name, default_app_dir)
    return has_updated


def _complete_missing_values(config_params, default_config_params):
    completed_config_params = dict(config_params)
    for key, default_value in default_config_params.items():
        if key not in completed_config_params:
            completed_config_params[key] = default_value
        elif isinstance(default_value, dict) and isinstance(
            completed_config_params[key], dict
        ):
            completed_config_params[key] = _complete_missing_values(
                config_params=completed_config_params[key],
                default_config_params=default_value,
            )
    return completed_config_params


def overwrite_config_file(data, file_name, default_app_dir):
    config_file = config_file_path(file_name, default_app_dir)
    with open(config_file, "+w") as f:
        f.write(yaml.safe_dump(data))


def append_config_file(data, file_name, default_app_dir):
    config_file = config_file_path(file_name, default_app_dir)
    # append
    with open(config_file, "+a") as f:
        yaml.dump(data, f, allow_unicode=True)
    # read
    with open(config_file, "r") as f:
        data = yaml.safe_load(f.read())
    # overwrite preventing repetition
    with open(config_file, "w") as f:
        yaml.dump(data, f, allow_unicode=True)


def get_param(parent_param, param, default_app_dir):
    default_dirs = create_and_read_config_file(
        file_name="config.yaml", default_app_dir=default_app_dir
    )[parent_param]

    if param in default_dirs:
        return default_dirs[param]
    else:
        raise Exception(f"{param} do not exist in your params {parent_param}.")


def config_file_exists(file_name, default_app_dir):
    return os.path.exists(config_file_path(file_name, default_app_dir))


def config_file_path(file_name, default_app_dir):
    _ensure_default_app_dir(default_app_dir)
    config_file = os.path.join(default_app_dir, file_name)
    return config_file


def _ensure_default_app_dir(default_app_dir):
    if not os.path.exists(default_app_dir):
        os.mkdir(default_app_dir)


def _get_default_file(default_file):
    default_files_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "default_files"
    )
    default_file = os.path.join(default_files_dir, default_file)
    with open(default_file, "r") as f:
        return yaml.safe_load(f.read())
