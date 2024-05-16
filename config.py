FASTQ_READ_1 = "./test_data/fastq/hg19/HIC_HEAD_R1.fastq"
FASTQ_READ_2 = "./test_data/fastq/hg19/HIC_HEAD_R2.fastq"
OUTPUT_DIR = "./output"

KMER = 3

TRAIN_DATA_PERCENTAGE = 0.9
NEGATIVE_TRAIN_SAMPLES = 0.5
NEGATIVE_TEST_SAMPLES = 0.5


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
