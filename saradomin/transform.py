import os, shutil
import ast
import random
from datetime import datetime

from . import common
from .profiler import profiler

__all__ = ["transform_data_to_vectors"]


def create_file_header(
        path_to_file: str,
        read_vector_schema: list[str],
        version: list[int],
) -> None:
    mapping = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
    header_: str = (
        "#HEADER#\n"
        f"#DATE={datetime.utcnow().isoformat()}\n"
        f"#pre_processing_version={version}\n"
        f"#{mapping}\n"
        f"#row_schema={read_vector_schema}\tUID\n"
        "####END####\n"
    )
    with open(path_to_file, "w") as f:
        f.write(header_)


def encode_sequence(sequence: str):
    """One-hot encode the entire nucleotide sequence."""
    mapping = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
    encoded_sequence = []
    for nucleotide in sequence:
        encoded_sequence.append(mapping.get(nucleotide.upper(), "100"))  # Extend to flatten the one-hot encoding
    return encoded_sequence


def convert_ascii_score_to_int(quality_string: str) -> list[int]:
    score: list[int] = [ord(q) for q in quality_string]  # Convert ASCII to PHRED score
    return score


@profiler
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

                if read_id not in read_id_counter:
                    read_id_counter[read_id] = uid_counter
                    uid_counter += 1
                # One-hot encode the entire sequence
                encoded_sequence = encode_sequence(sequence_line)
                score: list[int] = convert_ascii_score_to_int(quality_line)

                output_file.write(f"{read_id_counter[read_id]}\n")
                output_file.write(f"{str(encoded_sequence)}\n")
                output_file.write(f"{str(score)}\n")


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


@profiler
def split_file(original_file, new_file, train_data_percentage: float) -> None:
    header_lines = []

    # Read the original file to extract header lines and determine the split index
    with open(original_file, 'r') as file:
        for line in file:
            if line.startswith('####END####'):
                header_lines.append(line)
                break
            header_lines.append(line)
        total_lines = sum(1 for _ in file) + len(header_lines)  # Adjust total_lines to include headers
    split_index = int(total_lines * train_data_percentage)

    if split_index % 3 != 0:  # Adjust to avoid splitting a trio
        split_index += 3 - (split_index % 3)

    # Use a temporary file to store the first part
    temp_file = original_file + '.tmp'

    # Process the original file line by line, preserving headers in both files
    with open(original_file, 'r') as file, open(temp_file, 'w') as temp, open(new_file, 'w') as new_f:
        # Write header lines to both files
        for header in header_lines:
            temp.write(header)
            new_f.write(header)

        # Skip header lines already read
        _ = [next(file) for _ in range(len(header_lines))]

        # Split the remaining lines between the original (temp) and new file
        for i, line in enumerate(file, start=len(header_lines)):
            if i < split_index:
                temp.write(line)
            else:
                new_f.write(line)

    # Replace the original file with the temporary file containing the first part
    shutil.move(temp_file, original_file)


@profiler
def shuffle_data_in_file(file_path: str, right_pair_percentage: float):
    index_file = file_path + '.idx'
    temp_file = file_path + '.tmp'

    # Indexing Phase
    with open(file_path, 'r') as file, open(index_file, 'w') as idx:
        pos = file.tell()
        line = file.readline()
        while line:
            if not line.startswith('#') and not line.startswith('####END####'):
                idx.write(f"{pos}\n")
                file.readline()  # Skip next 2 lines belonging to the same block
                file.readline()
            pos = file.tell()
            line = file.readline()

    # Shuffling Phase with right_pair_percentage consideration
    with open(index_file, 'r') as idx:
        indices = idx.readlines()
        # Calculate the cutoff for the number of triads to remain in place
        cutoff = int(len(indices) * right_pair_percentage)
        # Separate the indices to shuffle and to keep
        to_keep = indices[:cutoff]
        to_shuffle = indices[cutoff:]
        random.shuffle(to_shuffle)
        # Combine back, keeping the specified percentage in original position
        indices = to_keep + to_shuffle

    # Reconstruction Phase
    with open(file_path, 'r') as file, open(temp_file, 'w') as out:
        # Write the header
        for line in file:
            if not line.startswith('#'):
                break
            out.write(line)

        # Write the data blocks based on the adjusted indices
        for index in indices:
            file.seek(int(index))
            for _ in range(3):  # Write each block of 3 lines
                out.write(file.readline())

    # Replace the original file with the shuffled data
    shutil.move(temp_file, file_path)
    os.remove(index_file)  # Clean up the index file


def transform_one_read(fastq_read_path: str,
                       hic_pro_valid_pairs_path: str,
                       output_file_path: str,
                       read_vector_schema: list[str],
                       read_id_counter: dict[str, int],
                       add_hic_output: bool,
                       version: list[int]) -> None:
    common.create_file_if_not_exists(output_file_path)
    create_file_header(output_file_path, read_vector_schema, version)

    save_fastq(fastq_read_path, output_file_path, read_vector_schema, read_id_counter)
    if add_hic_output:
        insert_all_valid_pairs(hic_pro_valid_pairs_path, output_file_path, read_vector_schema, read_id_counter)


@profiler
def transform_data_to_vectors(fastq_dir: str,
                              hic_pro_dir: str,
                              output_dir: str,
                              add_hic_output: bool,
                              train_data_percentage: float,
                              right_pair_percentage: float,
                              version_: list[int],
                              ) -> None:
    # read_vector_schema: list = ["NUCLEOTIDE", "PHRED_SCORE", "GENOMIC_DISTANCE", "VALID_PAIR", "UID"]
    read_vector_schema: list = ["NUCLEOTIDE", "PHRED_SCORE"]
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
                           add_hic_output,
                           version_)
        transform_one_read(fastq_r2_path,
                           valid_pairs_path,
                           output_r2_path,
                           read_vector_schema,
                           read_id_counter,
                           add_hic_output,
                           version_)
        test_r1_path: str = common.insert_test_before_extension(output_r1_path)
        test_r2_path: str = common.insert_test_before_extension(output_r2_path)


        shuffle_data_in_file(output_r2_path, right_pair_percentage)

        split_file(output_r1_path, test_r1_path, train_data_percentage)
        split_file(output_r2_path, test_r2_path, train_data_percentage)
