from types import ModuleType
from os.path import isfile
import os

import config
import log

from . import struct as st
from .common import create_file_if_not_exists
from .transform import transform_data_to_vectors


__version__ = [0, 1, 0]
__last_update__ = "2023-10-25T20:00:00"


def compile_config(app_config: ModuleType, path: str):
    try:
        with open(path, "rb") as rnf:
            exec(compile(rnf.read(), "config.py", "exec"), app_config.__dict__)
    except OSError as e:
        print(f"File at {path} could not be loaded because of error: {e}")
        raise e from e


def load_config() -> ModuleType:
    """
    Load local config.py.
    If exists config.py in /etc/saradomin/ then overrides parameters in local config.py.
    :return: configuration file
    """
    app_config: ModuleType = config
    path: str = "/etc/saradomin/config.py"

    if not isfile(path):
        return app_config
    if isfile(path):
        compile_config(app_config, path)
    return app_config


def parse_namespace(config_: ModuleType) -> st.Config:
    """
    Parse configuration file file to dict.
    :param: config_ configuration file
    :return: parsed configuration file
    """
    parsed: dict[str, any] = {}
    for key, value in config_.__dict__.items():
        if not key.startswith("__"):
            parsed[key] = value
    return st.Config(**parsed)


def run():
    print("------ Start  -------")
    config_: ModuleType = load_config()
    parsed_config: st.Config = parse_namespace(config_)

    print("============ Setting Up Logger ============")
    if parsed_config.LOG_CONFIG["handlers"].get("file", None):
        file_path: str = parsed_config.LOG_CONFIG["handlers"]["file"].get("filename")
        create_file_if_not_exists(file_path)
    log.set_up_logger(parsed_config.LOG_CONFIG)

    transform_data_to_vectors(parsed_config.FASTQ_DIR,
                              parsed_config.HIC_ALL_PAIRS_DIR,
                              parsed_config.OUTPUT_DIR,
                              parsed_config.PERCENTAGE_OF_TEST_DATA,
                              __version__)

