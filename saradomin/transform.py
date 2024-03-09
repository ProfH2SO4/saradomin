import os
from datetime import datetime

from . import common

__all__ = ["turn_data_to_vectors"]


def create_file_header(
    path_to_file: str,
    read_vector_schema: list[str],
    version: list[int],
) -> None:
    header_: str = (
        "#HEADER#\n"
        f"#DATE={datetime.utcnow().isoformat()}\n"
        f"#pre_processing_version={version}\n"
        f"#read_schema={read_vector_schema}\n"
        "####END####\n"
    )
    with open(path_to_file, "w") as f:
        f.write(header_)


def save_fastq(fastq_read_path: str, output_dir_path: str) -> None:
    pass

def turn_one_read(fastq_read: str,
                  hic_pro_valid_pairs: str,
                  output_file: str,
                  read_schema: list[str],
                  version: list[int]) -> None:
    common.create_file_if_not_exists(output_file)
    create_file_header(output_file, read_schema, version)



def turn_data_to_vectors(fastq_dir: str,
                         hic_pro_dir: str,
                         output_dir: str,
                         test_data_percentage: float,
                         version_: list[int],
                         ) -> None:
    read_vector_schema: list = ["NUCLEOTIDE", "PHRED_SCORE", "GENOMIC_DISTANCE", "VALID_PAIR", "UID"]
    for entry in os.listdir(fastq_dir):
        fastq_pair_dir_path = os.path.join(fastq_dir, entry)
        fastq_r1_p, fastq_r2_p = common.find_r1_r2_files(fastq_pair_dir_path)
        valid_pairs_path: str = common.find_all_valid_pairs_file(f"{hic_pro_dir}/{entry}")
        turn_one_read(fastq_r1_p,
                      valid_pairs_path,
                      f"{output_dir}/{common.add_txt_extension(fastq_r1_p)}",
                      read_vector_schema, version_)
        turn_one_read(fastq_r2_p,
                      valid_pairs_path,
                      f"{output_dir}/{common.add_txt_extension(fastq_r2_p)}",
                      read_vector_schema, version_)






