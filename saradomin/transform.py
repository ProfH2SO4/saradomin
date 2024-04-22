import os, shutil
import ast
import random
import tempfile
from datetime import datetime

from . import common
from .profiler import profiler
from . import log

__all__ = ["transform_data_to_vectors"]


def create_file_header(
    path_to_file: str,
    read_vector_schema: list[str],
    version: list[int],
) -> None:
    mapping = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
    header_: str = (
        "#HEADER#\n"
        f"#DATE={datetime.utcnow().isoformat()}\n"
        f"#pre_processing_version={version}\n"
        f"#mapping: {mapping}\n"
        f"#schema=1.row UID\t2.row {read_vector_schema[0]}\t3.row {read_vector_schema[1]} \n"
        "####END####\n"
    )
    with open(path_to_file, "w") as f:
        f.write(header_)


def encode_sequence(sequence: str):
    """One-hot encode the entire nucleotide sequence."""
    mapping = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
    encoded_sequence = []
    for nucleotide in sequence:
        encoded_sequence.append(mapping.get(nucleotide.upper(), "100"))  # Extend to flatten the one-hot encoding
    return encoded_sequence


def convert_ascii_score_to_int(quality_string: str) -> list[int]:
    score: list[int] = [ord(q) for q in quality_string]  # Convert ASCII to PHRED score
    return score


@profiler
def save_fastq(fastq_read_path: str, output_file_path: str, read_id_counter: dict[str, int]) -> None:
    """
    Saves a modified FASTQ read to a specified output file.
    The saved values looks like this:
    0
    [4, 0, 1 ,3]
    [35, 60, 60]
    :param fastq_read_path: Path to the input FASTQ file from which reads are processed.
    :param output_file_path: Path to the output file where processed reads are to be saved.
    :param read_id_counter: A dictionary mapping read identifiers to their new occurrence count after processing.
    :return: None. Outputs are written directly to the specified file.
    """
    uid_counter: int = 0
    with open(fastq_read_path, "r") as fastq_file, open(output_file_path, "a") as output_file:
        for line in fastq_file:
            if line.startswith("@"):
                read_id = line.split()[0][1:]  # Remove the '@' character
                sequence_line = next(fastq_file).strip()  # Nucleotide sequence
                next(fastq_file)  # Skip the '+' line
                quality_line = next(fastq_file).strip()  # PHRED quality scores

                if read_id not in read_id_counter:
                    read_id_counter[read_id] = uid_counter
                    uid_counter += 1
                # encode the entire sequence
                encoded_sequence = encode_sequence(sequence_line)
                score: list[int] = convert_ascii_score_to_int(quality_line)

                output_file.write(f"{read_id_counter[read_id]}\n")
                output_file.write(f"{str(encoded_sequence)}\n")
                output_file.write(f"{str(score)}\n")


def insert_valid_pair(line_vector: list, valid_pair_pos: int, genomic_distance_pos: int, genomic_distance: int) -> None:
    line_vector[valid_pair_pos] = 1
    line_vector[genomic_distance_pos] = genomic_distance


def insert_all_valid_pairs(
    hic_pro_valid_pairs_path: str, output_file_path: str, read_vector_schema: str, read_id_counter: dict[str, int]
) -> None:  # TODO Profile this function is slow
    valid_pairs_dict: dict[str, dict] = {}
    with open(hic_pro_valid_pairs_path, "r") as valid_pairs_file:
        for line in valid_pairs_file:
            columns = line.strip().split("\t")

            read_id: str = columns[0]
            genomic_distance = columns[-5]  # Fifth element from the end
            valid_pairs_dict[read_id] = {"genomic_distance": genomic_distance}

    uid_index_from_end: int = common.get_position_feature(read_vector_schema, "UID")
    genomic_distance_index_from_end: int = common.get_position_feature(read_vector_schema, "GENOMIC_DISTANCE")
    valid_pair_index_from_end: int = common.get_position_feature(read_vector_schema, "VALID_PAIR")
    temp_file_path: str = output_file_path + ".tmp"
    with open(output_file_path, "r") as o_file, open(temp_file_path, "w") as temp_file:
        for line in o_file:
            if line.startswith("#"):
                temp_file.write(line)
                continue
            line_list = ast.literal_eval(line)
            uid: int = int(line_list[len(line_list) - 1 - uid_index_from_end])

            uid_str: str = common.get_key_from_value(read_id_counter, uid)
            if uid_str in valid_pairs_dict:
                insert_valid_pair(
                    line_list,
                    (len(line_list) - 1) - valid_pair_index_from_end,
                    (len(line_list) - 1) - genomic_distance_index_from_end,
                    valid_pairs_dict[uid_str]["genomic_distance"],
                )
            temp_file.write(str(line_list) + "\n")

    os.replace(temp_file_path, output_file_path)


@profiler
def split_file(
    original_file: str, new_file: str, train_data_percentage: float, training_id_counter: [str, int]
) -> None:
    """
    Split file into training and testing data. The data are split based on  number of reads.
    In this case One read takes a 3 lines in file 1. read_id, 2. Sequence 3. score.
    The file is split as following: ((sum(lines) - header lines) // 3) * train_data_percentage == number_of_reads * train_data_percentage + len(header_lines)
    :param original_file:
    :param new_file: (testing file)
    :param train_data_percentage:
    :return: None, create new testing file
    """
    log.debug(f"splitting {original_file}, train_data_percentage {train_data_percentage}")
    header_lines: list[str] = []

    # Read the original file to extract header lines and determine the split index
    with open(original_file, "r") as file:
        for line in file:
            if line.startswith("####END####"):
                header_lines.append(line)
                break
            header_lines.append(line)

    # Use a temporary file to store the first part
    temp_file = original_file + ".tmp"

    # Process the original file line by line, preserving headers in both files
    with open(original_file, "r") as file, open(temp_file, "w") as temp, open(new_file, "w") as new_f:
        # Write header lines to both files
        for header in header_lines:
            temp.write(header)
            new_f.write(header)

        # Skip header lines already read
        _ = [next(file) for _ in range(len(header_lines))]

        # Split the remaining lines between the original (temp) and new file
        it = iter(enumerate(file, start=len(header_lines)))
        for i, line in it:
            if int(line.strip()) in training_id_counter.values():
                # Write the current and the next two lines to temp
                temp.write(line)
                temp.write(next(it)[1])  # Write next line
                temp.write(next(it)[1])  # Write the line after next
            else:
                new_f.write(line)
                new_f.write(next(it)[1])  # Write next line
                new_f.write(next(it)[1])  # Write the line after next

    # Replace the original file with the temporary file containing the first part
    shutil.move(temp_file, original_file)


@profiler
def shuffle_data_in_file(file_path: str, right_pair_percentage: float):
    index_file = file_path + ".idx"
    temp_file = file_path + ".tmp"

    # Indexing Phase
    with open(file_path, "r") as file, open(index_file, "w") as idx:
        pos = file.tell()
        line = file.readline()
        while line:
            if not line.startswith("#") and not line.startswith("####END####"):
                idx.write(f"{pos}\n")
                file.readline()  # Skip next 2 lines belonging to the same block
                file.readline()
            pos = file.tell()
            line = file.readline()

    # Shuffling Phase with right_pair_percentage consideration
    with open(index_file, "r") as idx:
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
    with open(file_path, "r") as file, open(temp_file, "w") as out:
        # Write the header
        for line in file:
            if not line.startswith("#"):
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


def transform_one_read(
    fastq_read_path: str,
    output_file_path: str,
    read_vector_schema: list[str],
    read_id_counter: dict[str, int],
    version: list[int],
) -> None:
    """
    Processes a single FASTQ read, transforming it according to a specified schema, and writes the output to a file.
    It updates the read_id_counter dictionary to keep track of read identifiers.

    :param fastq_read_path: Path to the FASTQ file containing the read to be processed.
    :param output_file_path: Path to the file where the transformed read output will be written.
    :param read_vector_schema: A list of strings defining the schema for each read.
    :param read_id_counter: A dictionary mapping read identifiers to their occurrence count,
    used to track how many times each read is processed.
    :param version: A list of integers specifying the version of script.
    :return: None. The function writes the processed read directly to the output file path specified.
    """
    common.create_file_if_not_exists(output_file_path)
    create_file_header(output_file_path, read_vector_schema, version)
    save_fastq(fastq_read_path, output_file_path, read_id_counter)


def shuffle_triples_in_file(file_path: str):
    """
    Shuffle triples in a file and overwrite the original file with the shuffled data.

    Parameters:
    - file_path: Path to the file whose triples are to be shuffled.
    """
    triples = []

    # Read the file and group lines into triples
    with open(file_path, "r") as file:
        triple = []
        for line in file:
            triple.append(line)
            if len(triple) == 3:  # Check if the triple is complete
                triples.append(triple)
                triple = []

        # Handle case where the last group might not be a complete triple
        if triple:
            triples.append(triple)

    # Shuffle the triples
    random.shuffle(triples)

    # Overwrite the original file with shuffled triples
    with open(file_path, "w") as file:
        for triple in triples:
            for line in triple:
                file.write(line)


def shuffle_triples_in_file_keep_header(file_path: str):
    """
    Shuffle triples in a file, keeping header lines intact at the beginning, and overwrite the original file with the shuffled data.

    Parameters:
    - file_path: Path to the file whose triples are to be shuffled.
    """
    headers = []
    triples = []
    triple = []

    # Read the file, keep headers, and group the rest into triples
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith("#"):
                # Store headers separately
                headers.append(line)
            else:
                # Group the rest into triples
                triple.append(line)
                if len(triple) == 3:
                    triples.append(triple)
                    triple = []

        # Handle case where the last group might not be a complete triple
        if triple:
            triples.append(triple)

    # Shuffle the triples
    random.shuffle(triples)

    # Overwrite the original file with headers and shuffled triples
    with open(file_path, "w") as file:
        # Write headers back first
        for header in headers:
            file.write(header)
        # Write shuffled triples
        for triple in triples:
            for line in triple:
                file.write(line)


def shuffle_triples_preserve_headers(file_path1: str, file_path2: str):
    def extract_headers_and_write_temp(file_path):
        headers = []
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
        with open(file_path, "r") as f:
            for line in f:
                if line.startswith("#"):
                    headers.append(line)
                else:
                    temp_file.write(line)
        temp_file.close()
        return headers, temp_file.name

    def count_triples(temp_file_path):
        with open(temp_file_path, "r") as f:
            line_count = sum(1 for _ in f)
        return line_count // 3

    def shuffle_and_rewrite(temp_file_path, indices, file_path, headers):
        with open(temp_file_path, "r") as temp_f, open(file_path, "w") as out_f:
            triples = [next(temp_f) + next(temp_f) + next(temp_f) for _ in range(len(indices))]
            # Write headers back first
            out_f.writelines(headers)
            # Write shuffled triples
            for i in indices:
                out_f.write(triples[i])

    # Step 1: Extract headers and write lines to temp files, skipping lines starting with '#'
    headers1, temp_file_path1 = extract_headers_and_write_temp(file_path1)
    headers2, temp_file_path2 = extract_headers_and_write_temp(file_path2)

    # Step 2: Count triples and shuffle indices
    num_triples = count_triples(temp_file_path1)  # Assuming both files have the same number of lines after headers
    indices = list(range(num_triples))
    random.shuffle(indices)

    # Step 3: Shuffle and rewrite triples along with headers to the original files
    shuffle_and_rewrite(temp_file_path1, indices, file_path1, headers1)
    shuffle_and_rewrite(temp_file_path2, indices, file_path2, headers2)

    # Clean up initial temp files
    os.remove(temp_file_path1)
    os.remove(temp_file_path2)


@profiler
def transform_data_to_vectors(
    fastq_dir: str,
    output_dir: str,
    train_data_fraction: float,
    keep_correct_train_pair: float,  # CORRECT_TRAIN_PAIR_PERCENTAGE
    keep_correct_test_pair: float,
    version_: list[int],
) -> None:
    """
    Transforms sequence data from FASTQ files into vector representations suitable for machine learning models.
    The function splits the data into training and testing datasets based
    on specified percentages and filters the pairs of sequences by correctness.

    :param fastq_dir: Path to the directory containing the FASTQ files.
    :param output_dir: Directory where the transformed vector output will be stored.
    :param train_data_fraction: Percentage of the total data to be used as training data.
    :param keep_correct_train_pair: Percentage of correct pairs to keep in the training dataset.
    :param keep_correct_test_pair: Percentage of correct pairs to keep in the testing dataset.
    :param version_: A list of integers specifying the version of the processing algorithm or tools used.
    :return: None. The function writes the output directly to the specified directory.
    """
    read_vector_schema: list = ["NUCLEOTIDE", "SCORE"]

    if not common.is_directory(fastq_dir):
        return
    train_dir: str = f"{output_dir}/train"
    test_dir: str = f"{output_dir}/test"
    file_r1_name: str = "READ_1.txt"
    file_r2_name: str = "READ_2.txt"
    common.create_dir(train_dir)
    common.create_dir(test_dir)
    fastq_r1_path, fastq_r2_path = common.find_r1_r2_files(fastq_dir)

    read_id_counter: dict[str, int] = {}
    train_output_r1_path: str = f"{train_dir}/{file_r1_name}"
    train_output_r2_path: str = f"{train_dir}/{file_r2_name}"
    transform_one_read(fastq_r1_path, train_output_r1_path, read_vector_schema, read_id_counter, version_)
    transform_one_read(fastq_r2_path, train_output_r2_path, read_vector_schema, read_id_counter, version_)
    test_r1_path: str = common.insert_before_extension(f"{test_dir}/{file_r1_name}", "_test")
    test_r2_path: str = common.insert_before_extension(f"{test_dir}/{file_r2_name}", "_test")

    training_id_counter: dict[str, int]
    test_id_counter: dict[str, int]
    training_id_counter, test_id_counter = common.copy_keys_by_fraction(read_id_counter, train_data_fraction)

    split_file(train_output_r1_path, test_r1_path, train_data_fraction, training_id_counter)
    split_file(train_output_r2_path, test_r2_path, train_data_fraction, training_id_counter)

    train_shuffled_output_r2_path: str = common.insert_before_extension(train_output_r2_path, "_shuffled")
    test_shuffled_output_r2_path: str = common.insert_before_extension(test_r2_path, "_shuffled")

    train_read_ids_to_shuffle: list[int] = common.get_shuffled_values_only(training_id_counter, keep_correct_train_pair)
    test_read_ids_to_shuffle: list[int] = common.get_shuffled_values_only(test_id_counter, keep_correct_test_pair)

    common.shuffle_selected_reads(train_read_ids_to_shuffle, train_output_r2_path, train_shuffled_output_r2_path)
    common.delete_file(train_output_r2_path)

    common.shuffle_selected_reads(test_read_ids_to_shuffle, test_r2_path, test_shuffled_output_r2_path)
    common.delete_file(test_r2_path)
