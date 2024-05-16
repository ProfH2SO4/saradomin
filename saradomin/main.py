import os
from types import ModuleType
from os.path import isfile
from dataclasses import fields
from dotenv import load_dotenv

import config

from . import struct as st, log
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
    Load config variables
    Overrides .env params override config
    :return: configuration file
    """
    app_config: ModuleType = config

    load_dotenv()
    for field_info in fields(st.Config):
        env_value = os.getenv(field_info.name)
        if env_value is not None:
            field_type = type(getattr(app_config, field_info.name, field_info.default))
            setattr(app_config, field_info.name, field_type(env_value))
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
    log.info("------ START  -------")
    config_: ModuleType = load_config()
    parsed_config: st.Config = parse_namespace(config_)

    print("============ Setting Up Logger ============")
    if parsed_config.LOG_CONFIG["handlers"].get("file", None):
        file_path: str = parsed_config.LOG_CONFIG["handlers"]["file"].get("filename")
        create_file_if_not_exists(file_path)
    log.set_up_logger(parsed_config.LOG_CONFIG)

    transform_data_to_vectors(
        parsed_config.FASTQ_READ_1,
        parsed_config.FASTQ_READ_2,
        parsed_config.OUTPUT_DIR,
        parsed_config.KMER,
        parsed_config.TRAIN_DATA_PERCENTAGE,
        parsed_config.NEGATIVE_TRAIN_SAMPLES,
        negative_test_samples=parsed_config.NEGATIVE_TEST_SAMPLES,
        version_=__version__,
    )
    log.info("------ END  -------")
