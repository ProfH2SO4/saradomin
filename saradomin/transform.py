import os
from datetime import datetime

from . import common

__all__ = ["transform_data_to_vectors"]


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


def one_hot_encode_sequence(sequence: str):
    """One-hot encode the entire nucleotide sequence."""
    mapping = {'A': "000", 'C': "001", 'G': "010", 'T': "011", 'N': "100"}
    encoded_sequence = []
    for nucleotide in sequence:
        encoded_sequence.append(mapping.get(nucleotide.upper(), "100"))  # Extend to flatten the one-hot encoding
    return encoded_sequence


def calculate_average_phred(quality_string: str) -> float:
    """Calculate the average PHRED quality score for the read."""
    total_score = sum(ord(q) - 33 for q in quality_string)  # Convert ASCII to PHRED score
    average_score = total_score / len(quality_string)
    return round(average_score, 2)


def save_fastq(fastq_read_path: str,
               output_file_path: str,
               read_vector_schema: list[str],
               read_id_counter: dict[str, int]) -> None:
    with open(fastq_read_path, 'r') as fastq_file, open(output_file_path, 'a') as output_file:
        for line in fastq_file:
            if line.startswith('@'):
                read_id = line.split()[0][1:]  # Remove the '@' character
                sequence_line = next(fastq_file).strip()  # Nucleotide sequence
                next(fastq_file)  # Skip the '+' line
                quality_line = next(fastq_file).strip()  # PHRED quality scores

                # Update read_id_counter
                read_id_counter[read_id] = read_id_counter.get(read_id, 0) + 1

                # One-hot encode the entire sequence
                encoded_sequence = one_hot_encode_sequence(sequence_line)
                read_vector = encoded_sequence + [0] * (len(read_vector_schema) - 1)
                # Calculate the average PHRED score for the read
                average_phred_score = calculate_average_phred(quality_line)
                pos_phred_from_end = (len(read_vector) - 1) - common.get_position_feature(read_vector_schema, "PHRED_SCORE")
                read_vector[pos_phred_from_end] = average_phred_score

                pos_uid_from_end = (len(read_vector) - 1) - common.get_position_feature(read_vector_schema, "UID")
                read_vector[pos_uid_from_end] = read_id_counter[read_id]
                output_file.write(str(read_vector))

                
def insert_all_valid_pairs(hic_pro_valid_pairs_path: str,
                           output_file_path: str,
                           read_vector_schema: str,
                           read_id_counter: dict[str, int]) -> None:
    valid_pairs_dict = {}
    with open(hic_pro_valid_pairs_path, 'r') as valid_pairs_file:
        for line in valid_pairs_file:
            columns = line.strip().split('\t')

            read_id: str = columns[0]
            genomic_distance = columns[-5]  # Fifth element from the end
            valid_pairs_dict[read_id] = {"genomic_distance": genomic_distance}
            read_id_counter[read_id] = read_id_counter.get(read_id, 0) + 1

    uid_index_from_end = common.get_position_feature(read_vector_schema, "UID")

    with open(output_file_path, 'r') as o_file:
        for line in o_file:
            if line.startswith('#'):
                continue
            line_list = eval(line.strip())
            uid = line_list[uid_index_from_end]

            if uid in read_id_counter:
                if uid in valid_pairs_dict:
                    pass


def transform_one_read(fastq_read_path: str,
                       hic_pro_valid_pairs_path: str,
                       output_file_path: str,
                       read_vector_schema: list[str],
                       version: list[int]) -> None:
    common.create_file_if_not_exists(output_file_path)
    create_file_header(output_file_path, read_vector_schema, version)

    read_id_counter: dict[str, int] = {}
    save_fastq(fastq_read_path, output_file_path, read_vector_schema, read_id_counter)

    insert_all_valid_pairs(hic_pro_valid_pairs_path, output_file_path, read_vector_schema, read_id_counter)

def transform_data_to_vectors(fastq_dir: str,
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
        transform_one_read(fastq_r1_p,
                           valid_pairs_path,
                      f"{output_dir}/{common.add_txt_extension(fastq_r1_p)}",
                           read_vector_schema,
                           version_)
        transform_one_read(fastq_r2_p,
                           valid_pairs_path,
                      f"{output_dir}/{common.add_txt_extension(fastq_r2_p)}",
                           read_vector_schema,
                           version_)






