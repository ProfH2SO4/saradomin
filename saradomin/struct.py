from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    FASTQ_DIR: str
    HIC_ALL_PAIRS_DIR: str
    OUTPUT_DIR: str
    ADD_HIC_OUTPUT: bool
    TRAIN_DATA_PERCENTAGE: int
    RIGHT_PAIR_PERCENTAGE: float
    LOG_CONFIG: dict