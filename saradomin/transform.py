import os
import ast
from datetime import datetime

from . import common

__all__ = ["transform_data_to_vectors"]


def create_file_header(
    path_to_file: str,
    read_vector_schema: list[str],
    version: list[int],
) -> None:
    mapping = {'A': "000", 'C': "001", 'G': "010", 'T': "011", 'N': "100"}
    header_: str = (
        "#HEADER#\n"
        f"#DATE={datetime.utcnow().isoformat()}\n"
        f"#pre_processing_version={version}\n"
        f"#{mapping}\n"
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
    uid_counter: int = 0
    with open(fastq_read_path, 'r') as fastq_file, open(output_file_path, 'a') as output_file:
        for line in fastq_file:
            if line.startswith('@'):
                read_id = line.split()[0][1:]  # Remove the '@' character
                sequence_line = next(fastq_file).strip()  # Nucleotide sequence
                next(fastq_file)  # Skip the '+' line
                quality_line = next(fastq_file).strip()  # PHRED quality scores

                # Update read_id_counter
                read_id_counter[read_id] = uid_counter
                uid_counter += 1
                # One-hot encode the entire sequence
                encoded_sequence = one_hot_encode_sequence(sequence_line)
                read_vector = encoded_sequence + [0] * (len(read_vector_schema) - 1)
                # Calculate the average PHRED score for the read
                average_phred_score = calculate_average_phred(quality_line)
                pos_phred_from_end = (len(read_vector) - 1) - common.get_position_feature(read_vector_schema, "PHRED_SCORE")
                read_vector[pos_phred_from_end] = average_phred_score

                pos_uid_from_end = (len(read_vector) - 1) - common.get_position_feature(read_vector_schema, "UID")
                read_vector[pos_uid_from_end] = read_id_counter[read_id]
                output_file.write(str(read_vector) + '\n')


def insert_valid_pair(line_vector: list, valid_pair_pos: int, genomic_distance_pos: int, genomic_distance: int) -> None:
    line_vector[valid_pair_pos] = 1
    line_vector[genomic_distance_pos] = genomic_distance


def insert_all_valid_pairs(hic_pro_valid_pairs_path: str,
                           output_file_path: str,
                           read_vector_schema: str,
                           read_id_counter: dict[str, int]) -> None:  # TODO Profile this function is slow
    valid_pairs_dict: dict[str, dict] = {}
    with open(hic_pro_valid_pairs_path, 'r') as valid_pairs_file:
        for line in valid_pairs_file:
            columns = line.strip().split('\t')

            read_id: str = columns[0]
            genomic_distance = columns[-5]  # Fifth element from the end
            valid_pairs_dict[read_id] = {"genomic_distance": genomic_distance}


    uid_index_from_end: int = common.get_position_feature(read_vector_schema, "UID")
    genomic_distance_index_from_end: int = common.get_position_feature(read_vector_schema, "GENOMIC_DISTANCE")
    valid_pair_index_from_end: int = common.get_position_feature(read_vector_schema, "VALID_PAIR")
    temp_file_path: str = output_file_path + ".tmp"
    with open(output_file_path, 'r') as o_file, open(temp_file_path, "w") as temp_file:
        for line in o_file:
            if line.startswith('#'):
                temp_file.write(line)
                continue
            line_list = ast.literal_eval(line)
            uid: int = int(line_list[len(line_list) - 1 - uid_index_from_end])

            uid_str: str = common.get_key_from_value(read_id_counter, uid)
            if uid_str in valid_pairs_dict:
                insert_valid_pair(line_list,
                                  (len(line_list) - 1) - valid_pair_index_from_end,
                                  (len(line_list) - 1) - genomic_distance_index_from_end,
                                  valid_pairs_dict[uid_str]["genomic_distance"])
            temp_file.write(str(line_list) + '\n')

    os.replace(temp_file_path, output_file_path)


def split_file(original_file, new_file, train_data_percentage: float) -> None:

    with open(original_file, 'r') as file:
        lines = file.readlines()

    total_lines = len(lines)
    split_index = int(total_lines * train_data_percentage)

    with open(original_file, 'w') as file:
        for line in lines[:split_index]:
            file.write(line)

    with open(new_file, 'w') as file:
        for line in lines[split_index:]:
            file.write(line)


def transform_one_read(fastq_read_path: str,
                       hic_pro_valid_pairs_path: str,
                       output_file_path: str,
                       read_vector_schema: list[str],
                       read_id_counter: dict[str, int],
                       version: list[int]) -> None:
    common.create_file_if_not_exists(output_file_path)
    create_file_header(output_file_path, read_vector_schema, version)

    save_fastq(fastq_read_path, output_file_path, read_vector_schema, read_id_counter)

    insert_all_valid_pairs(hic_pro_valid_pairs_path, output_file_path, read_vector_schema, read_id_counter)


def transform_data_to_vectors(fastq_dir: str,
                              hic_pro_dir: str,
                              output_dir: str,
                              train_data_percentage: float,
                              version_: list[int],
                              ) -> None:
    read_vector_schema: list = ["NUCLEOTIDE", "PHRED_SCORE", "GENOMIC_DISTANCE", "VALID_PAIR", "UID"]
    for entry in os.listdir(fastq_dir):
        fastq_pair_dir_path = os.path.join(fastq_dir, entry)
        fastq_r1_path, fastq_r2_path = common.find_r1_r2_files(fastq_pair_dir_path)
        valid_pairs_path: str = common.find_all_valid_pairs_file(f"{hic_pro_dir}/{entry}")

        read_id_counter: dict[str, int] = {}
        output_r1_path: str = f"{output_dir}/{entry}/{common.add_txt_extension(fastq_r1_path)}"
        output_r2_path: str = f"{output_dir}/{entry}/{common.add_txt_extension(fastq_r2_path)}"
        transform_one_read(fastq_r1_path,
                           valid_pairs_path,
                           output_r1_path,
                           read_vector_schema,
                           read_id_counter,
                           version_)
        transform_one_read(fastq_r2_path,
                           valid_pairs_path,
                           output_r2_path,
                           read_vector_schema,
                           read_id_counter,
                           version_)
        test_r1_path: str = common.insert_test_before_extension(output_r1_path)
        test_r2_path: str = common.insert_test_before_extension(output_r2_path)

        split_file(output_r1_path, test_r1_path, train_data_percentage)
        split_file(output_r2_path, test_r2_path, train_data_percentage)




