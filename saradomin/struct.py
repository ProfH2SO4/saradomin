from dataclasses import dataclass, fields


@dataclass(slots=True)
class Config:
    FASTQ_READ_1: str
    FASTQ_READ_2: str
    OUTPUT_DIR: str
    KMER: int
    TRAIN_DATA_PERCENTAGE: int
    NEGATIVE_TRAIN_SAMPLES: float
    NEGATIVE_TEST_SAMPLES: float
    LOG_CONFIG: dict

    def __init__(self, **kwargs):
        cls_fields = {f.name for f in fields(self)}
        for key in kwargs:
            if key in cls_fields:
                setattr(self, key, kwargs[key])
