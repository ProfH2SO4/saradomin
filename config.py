FASTQ_DIR = "./test_data/fastq/hg19"
OUTPUT_DIR = "./output"

ADD_HIC_OUTPUT = False  # Keep False


TRAIN_DATA_PERCENTAGE = 0.9
KEEP_CORRECT_TRAIN_PAIR = 0.5
KEEP_CORRECT_TEST_PAIR = 0.0

LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "SARADOMIN - %(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "./logs/default.txt",  # Specify the file path
        },
    },
    "loggers": {
        "default": {
            "level": "DEBUG",
            "handlers": ["console", "file"],  # Updated to use console handler
            "propagate": False,
        }
    },
    "disable_existing_loggers": False,
}
