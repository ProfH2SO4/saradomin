from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    FASTQ_DIR: str
    HIC_ALL_PAIRS_DIR: str
    OUTPUT_DIR: str
    PERCENTAGE_OF_TEST_DATA: int
    RANDOM_SPLIT: bool
    LOG_CONFIG: dict