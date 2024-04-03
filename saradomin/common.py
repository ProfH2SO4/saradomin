import os

from saradomin import log


def create_file_if_not_exists(path_to_file: str) -> None:
    # Check if the directory exists, and create it if it doesn't
    directory = os.path.dirname(path_to_file)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Check if the file exists, and create it if it doesn't
    if not os.path.exists(path_to_file):
        with open(path_to_file, "w") as file:
            pass  # Create an empty file


def find_r1_r2_files(dir_path: str) -> tuple[str, str]:
    r1_file, r2_file = None, None

    for file in os.listdir(dir_path):
        full_path = os.path.join(dir_path, file)

        if '_R1' in file:
            r1_file = full_path

        elif '_R2' in file:
            r2_file = full_path

    return r1_file, r2_file


def add_txt_extension(file_path: str) -> str:
    file_name: str = os.path.basename(file_path)
    name_parts: list[str] = file_name.split('.', 1)
    return name_parts[0] + '.txt'


def find_all_valid_pairs_file(dir_path: str) -> str:
    for file in os.listdir(dir_path):
        if file.endswith('.allValidPairs'):
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
    with open(source_path, 'r') as source_file, open(destination_path, 'w') as destination_file:
        # Skip lines starting with '#'
        for line in source_file:
            if not line.startswith('#'):
                destination_file.write(line)
                break

        # After the first non-'#' line, copy the rest of the file as is
        while True:
            chunk = source_file.read(buffer_size)
            if not chunk:
                break  # End of file reached
            destination_file.write(chunk)


def append_file_to_another(source_path1: str, source_path2: str, buffer_size=1024*1024):
    """
    Append the content of the second file to the end of the first file.

    Parameters:
    - source_path1: Path to the first file which will also be the destination file.
    - source_path2: Path to the second source file.
    - buffer_size: Size of the buffer to use while copying, in bytes. Default is 1MB for binary mode.
    """
    # Open the first file in append mode to add content to its end
    with open(source_path1, 'ab') as destination_file:
        # Read and append content from the second file
        with open(source_path2, 'rb') as source_file2:
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

