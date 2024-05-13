import os
import random
import shutil

from saradomin import log


def delete_directory_if_exists(dir_path):
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            log.debug(f"Directory '{dir_path}' deleted successfully.")
        except OSError as e:
            log.warning(f"Error: {dir_path} : {e.strerror}")


def create_dir(dir_path) -> None:
    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def create_file_if_not_exists(path_to_file: str) -> None:
    # Check if the directory exists, and create it if it doesn't
    directory = os.path.dirname(path_to_file)
    create_dir(directory)

    # Check if the file exists, and create it if it doesn't
    if not os.path.exists(path_to_file):
        with open(path_to_file, "w") as file:
            pass  # Create an empty file


def find_r1_r2_files(dir_path: str) -> tuple[str, str]:
    r1_file, r2_file = None, None

    for file in os.listdir(dir_path):
        full_path = os.path.join(dir_path, file)

        if "_R1" in file:
            r1_file = full_path

        elif "_R2" in file:
            r2_file = full_path

    return r1_file, r2_file


def add_txt_extension(file_path: str) -> str:
    file_name: str = os.path.basename(file_path)
    name_parts: list[str] = file_name.split(".", 1)
    return name_parts[0] + ".txt"


def find_all_valid_pairs_file(dir_path: str) -> str:
    for file in os.listdir(dir_path):
        if file.endswith(".allValidPairs"):
            full_path = os.path.join(dir_path, file)
            return full_path


def get_position_feature(read_vector_schema: list[str], feature_name: str) -> int:
    position_from_start = read_vector_schema.index(feature_name)
    position_from_end = len(read_vector_schema) - position_from_start - 1
    return position_from_end


def get_key_from_value(d, val) -> any:
    for key, value in d.items():
        if value == val:
            return key
    return None  # Return None or an appropriate value if the value isn't found


def insert_before_extension(path: str, desired_insert: str) -> str:
    """Insert '_test' before the '.txt' extension in the file path."""
    name, ext = os.path.splitext(path)
    return f"{name}{desired_insert}{ext}"


def copy_file_skip_hash_lines(source_path: str, destination_path: str, buffer_size=1024 * 1024):
    """
    Copy a file from source_path to destination_path, skipping lines at the beginning that start with '#'.

    Parameters:
    - source_path: Path to the source file.
    - destination_path: Path to the destination file where the copy will be saved.
    - buffer_size: Size of the buffer to use while copying, in bytes. Default is 1MB for binary mode.
    """
    with open(source_path, "r") as source_file, open(destination_path, "w") as destination_file:
        # Skip lines starting with '#'
        for line in source_file:
            if not line.startswith("#"):
                destination_file.write(line)
                break

        # After the first non-'#' line, copy the rest of the file as is
        while True:
            chunk = source_file.read(buffer_size)
            if not chunk:
                break  # End of file reached
            destination_file.write(chunk)


def append_file_to_another(source_path1: str, source_path2: str, buffer_size=1024 * 1024):
    """
    Append the content of the second file to the end of the first file.

    Parameters:
    - source_path1: Path to the first file which will also be the destination file.
    - source_path2: Path to the second source file.
    - buffer_size: Size of the buffer to use while copying, in bytes. Default is 1MB for binary mode.
    """
    # Open the first file in append mode to add content to its end
    with open(source_path1, "ab") as destination_file:
        # Read and append content from the second file
        with open(source_path2, "rb") as source_file2:
            while True:
                chunk = source_file2.read(buffer_size)
                if not chunk:
                    break  # End of file reached
                destination_file.write(chunk)


def delete_file(file_path: str) -> None:
    """
    Delete a file at the specified path.

    Parameters:
    - file_path: Path to the file you want to delete.
    """
    # Check if file exists
    if os.path.exists(file_path):
        # Delete the file
        os.remove(file_path)
        log.debug(f"File '{file_path}' has been deleted.")
    else:
        log.debug(f"The file '{file_path}' does not exist.")


def is_directory(path: str) -> bool:
    """
    Check if the given path is a directory.

    Parameters:
    - path: The path to check.

    Returns:
    - True if the path is a directory, False otherwise.
    """
    return os.path.isdir(path)


def copy_keys_by_fraction(original_dict: dict, fraction: float) -> tuple[dict, dict]:
    """
    Copies a specified percentage of keys from the original dictionary to a new dictionary by reference.

    :param original_dict: The dictionary from which to copy keys.
    :param fraction: The fraction of keys to copy (between 0 and 1).
    :return: A new dictionary containing the specified percentage of keys from the original dictionary.
    """
    if not (0 <= fraction <= 1):
        raise ValueError("Percentage must be between 0 and 1")

    num_keys_to_copy = int(len(original_dict) * fraction)
    new_dict = {}
    other_dict = {}
    for i, (key, value) in enumerate(original_dict.items()):
        if i < num_keys_to_copy:
            new_dict[key] = value
        else:
            other_dict[key] = value
    return new_dict, other_dict


def get_shuffled_values_only(d, fraction_fixed):
    """
    Returns a list of integers from a dictionary, containing only those values that are shuffled,
    based on the specified fraction that should remain fixed.

    :param d: Dictionary of string keys and integer values.
    :param fraction_fixed: Fraction of the values to remain in fixed positions (between 0 and 1).
    :return: A list of integers that are shuffled, excluding the fixed fraction.
    """
    if not (0 <= fraction_fixed <= 1):
        raise ValueError("Fraction must be between 0 and 1")

    # Convert dictionary to a list of values
    values = list(d.values())
    total_values = len(values)
    num_fixed = int(total_values * fraction_fixed)

    # Indices of values that should be shuffled
    shuffle_indices = list(range(num_fixed, total_values))

    # Extract values to shuffle
    values_to_shuffle = [values[i] for i in shuffle_indices]
    random.shuffle(values_to_shuffle)

    return values_to_shuffle


def shuffle_selected_reads(to_shuffle: list[int], file_path: str, output_path: str) -> None:
    """
    Shuffles specified groups of lines (each group is three lines) in a large file based on a list of read headers.
    It writes the shuffled result to a new file.

    :param to_shuffle: List of integers representing read headers that should be shuffled.
    :param file_path: Path to the input file containing the data.
    :param output_path: Path to the output file where shuffled data will be written.
    """
    # Position index for reads
    read_positions = []

    # Read the file and index positions of reads to shuffle
    with open(file_path, "r") as file:
        while True:
            line_pos = file.tell()
            line = file.readline()
            if not line:
                break  # End of file

            if line.startswith("#") or line.strip() == "":
                continue  # Skip headers and empty lines

            read_id = int(line.split()[0])
            seq = file.readline()
            score = file.readline()

            # Store the position and content of each read group
            if read_id in to_shuffle:
                read_positions.append((line_pos, line, seq, score))

    # Shuffle the positions to reorder them
    shuffled_positions = random.sample(read_positions, len(read_positions))

    # Now create a map from original positions to shuffled read data
    position_map = {pos[0]: data for pos, data in zip(read_positions, shuffled_positions)}

    # Write the shuffled result to a new file
    with open(file_path, "r") as infile, open(output_path, "w") as outfile:
        infile.seek(0)
        current_pos = infile.tell()
        line = infile.readline()

        while line:
            if line.startswith("#"):
                # Write headers and other metadata directly
                outfile.write(line)
                current_pos = infile.tell()
                line = infile.readline()
                continue

            if current_pos in position_map:
                # Write the shuffled data
                data = position_map[current_pos]
                outfile.write(data[1])  # Read ID line
                outfile.write(data[2])  # Sequence line
                outfile.write(data[3])  # Score line
                # Skip the next two lines in the input file since they're already written
                infile.readline()
                infile.readline()
            else:
                # Write lines that are not part of any group directly
                outfile.write(line)
                line = infile.readline()
                outfile.write(line)
                line = infile.readline()
                outfile.write(line)

            current_pos = infile.tell()
            line = infile.readline()
