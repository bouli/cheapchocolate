import yaml
import os

def get_dir(param="cheapchocolate"):
    parent_param = 'default_dirs'

    if param == "cheapchocolate":
        folder = "./" + param
    else:
        folder = get_param(parent_param, param)
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder

def get_mails(param):
    parent_param = 'mails'
    return get_param(parent_param, param)

def load_config(force_default=False):
    customize_folder = "cheapchocolate"
    if not os.path.exists(customize_folder):
        os.mkdir(customize_folder)

    config_file = "config.yaml"
    config_file = os.path.join(customize_folder, config_file)
    if force_default or not os.path.exists(config_file):
        with open(config_file, "+w") as f:
            config_params = _default_config()
            f.write(yaml.safe_dump(config_params))
    else:
        with open(config_file, "r") as f:
            config_params = yaml.safe_load(f.read())

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params


def get_param(parent_param, param):
    default_dirs = load_config()[parent_param]
    if param in default_dirs:
        return default_dirs[param]
    else:
        raise Exception(f"{param} do not exist in your params {parent_param}.")

def _default_config():
    return {
                "default_dirs": {
                    "mailbox": "./mailbox",
                },
                "mails": {
                    "days_to_fetch" : 1
                }
            }
