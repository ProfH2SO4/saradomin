from dataclasses import dataclass, fields


@dataclass(slots=True)
class Config:
    FASTQ_DIR: str
    OUTPUT_DIR: str
    ADD_HIC_OUTPUT: bool
    TRAIN_DATA_PERCENTAGE: int
    KEEP_CORRECT_TRAIN_PAIR: float  # decimal
    KEEP_CORRECT_TEST_PAIR: float
    LOG_CONFIG: dict

    def __init__(self, **kwargs):
        cls_fields = {f.name for f in fields(self)}
        for key in kwargs:
            if key in cls_fields:
                setattr(self, key, kwargs[key])
