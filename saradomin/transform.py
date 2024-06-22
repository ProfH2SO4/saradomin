import os, shutil
import ast
import random
import tempfile
from datetime import datetime

from . import common, validator
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


def divide_seq_to_kmer(seq: str, pad: str, kmer: int) -> str:
    # Initialize the result list
    result = []

    # Process the sequence in chunks of size `kmer`
    for i in range(0, len(seq), kmer):
        chunk = seq[i : i + kmer]

        # Check if the last chunk needs padding
        if len(chunk) < kmer:
            chunk += pad * (kmer - len(chunk))  # Pad the chunk to ensure it is of length `kmer`

        # Append the chunk to the result list
        result.append(chunk)

    # Join all chunks with space and return
    return " ".join(result)


def create_line(seq_1: str, sep: str, seq_2: str, pad: str, kmer: int) -> str:
    seq_1_kmer = divide_seq_to_kmer(seq_1, pad, kmer)
    seq_2_kmer = divide_seq_to_kmer(seq_2, pad, kmer)
    return f"{seq_1_kmer} {sep} {seq_2_kmer}\t1\n"


def get_first_file_seq(file_1_gen, file_2_gen):
    seq1: str = ""
    seq2: str = ""

    next(file_1_gen)
    seq1 = next(file_1_gen).strip()
    next(file_2_gen)
    seq2 = next(file_2_gen).strip()
    return seq1, seq2


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks"""
    args = [iter(iterable)] * n
    return zip(*args)


@profiler
def save_fastq(read_1_p: str, read_2_p: str, output_file_path: str, kmer: int) -> int:
    """
    Saves a modified FASTQ read to a specified output file.
    The saved values looks like this:
    AAA TTT SEP AAA TTT 1
    :param fastq_read_path: Path to the input FASTQ file from which reads are processed.
    :param output_file_path: Path to the output file where processed reads are to be saved.
    :param read_id_counter: A dictionary mapping read identifiers to their new occurrence count after processing.
    :return: None. Outputs are written directly to the specified file.
    """
    sep: str = "[SEP]"
    pad: str = "X"
    number_of_reads: int = 0
    header: str = "sequence\tlabel\n"
    with open(read_1_p, "r") as r1_file, open(read_2_p, "r") as r2_file, open(output_file_path, "a") as output_file:
        output_file.write(header)
        # Use zip to iterate over both files simultaneously
        for r1_lines, r2_lines in zip(grouper(r1_file, 4), grouper(r2_file, 4)):
            if not r1_lines or not r2_lines:
                # If either file ends, stop processing
                break
            # Extract sequence lines
            r1_seq = r1_lines[1].strip()
            r2_seq = r2_lines[1].strip()

            # Process the sequence lines
            line = create_line(r1_seq, sep, r2_seq, pad=pad, kmer=kmer)
            output_file.write(line)
            number_of_reads += 1
    return number_of_reads


@profiler
def split_file(original_file: str, new_file: str, train_data_percentage: float, number_of_reads: int) -> None:
    """
    Split file into training and testing data. The data are split based on  number of reads.
    :param original_file:
    :param new_file: (testing file)
    :param train_data_percentage:
    :return: None, create new testing file
    """
    log.debug(f"splitting {original_file}, train_data_percentage {train_data_percentage}")

    # Use a temporary file to store the first part
    temp_file = original_file + ".tmp"
    num_train_reads = int(train_data_percentage * number_of_reads)
    # Process the original file line by line, preserving headers in both files
    with open(original_file, "r") as file, open(temp_file, "w") as temp_f, open(new_file, "w") as new_f:
        for i, line in enumerate(file):
            if i < num_train_reads:
                temp_f.write(line)  # Write to temporary file (training data)
            else:
                new_f.write(line)  # Write to new file (testing data)
    os.rename(temp_file, original_file)


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


def transform_to_nn(
    read_1_p: str,
    read_2_p: str,
    output_file_path: str,
    kmer: int,
    version: list[int],
) -> int:
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
    return save_fastq(read_1_p, read_2_p, output_file_path, kmer)


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
    fastq_read_1: str,
    fastq_read_2: str,
    output_dir: str,
    kmer: int,
    train_data_fraction: float,
    negative_train_fraction: float,  # CORRECT_TRAIN_PAIR_PERCENTAGE
    negative_test_fraction: float,
    version_: list[int],
) -> None:
    """
    Transforms sequence data from FASTQ files into vector representations suitable for machine learning models.
    The function splits the data into training and testing datasets based
    on specified percentages and filters the pairs of sequences by correctness.

    :param fastq_dir: Path to the directory containing the FASTQ files.
    :param output_dir: Directory where the transformed vector output will be stored.
    :param train_data_fraction: Fraction of the total data to be used as training data.
    :param negative_test_fraction: Fraction of correct pairs to keep in the training dataset.
    :param negative_train_fraction: Fraction of correct pairs to keep in the testing dataset.
    :param version_: A list of integers specifying the version of the processing algorithm or tools used.
    :return: None. The function writes the output directly to the specified directory.
    """
    random.seed(5)
    if not validator.check_if_file_exists(fastq_read_1):
        log.info(f"Missing r1: {fastq_read_1}")
        return
    if not validator.check_if_file_exists(fastq_read_2):
        log.info(f"Missing r2: {fastq_read_2}")
        return
    train_dir: str = f"{output_dir}/train"
    test_dir: str = f"{output_dir}/test"
    common.delete_directory_if_exists(train_dir)
    common.delete_directory_if_exists(test_dir)
    # existing dirs were deleted
    file_r1_name: str = "train.tsv"
    common.create_dir(train_dir)
    common.create_dir(test_dir)

    train_file_path: str = f"{train_dir}/{file_r1_name}"
    number_of_reads: int = transform_to_nn(fastq_read_1, fastq_read_2, train_file_path, kmer, version_)

    test_path: str = f"{test_dir}/test.tsv"

    split_file(train_file_path, test_path, train_data_fraction, number_of_reads)

    common.create_negative_samples(train_file_path, negative_train_fraction)
    common.create_negative_samples(test_path, negative_test_fraction)
