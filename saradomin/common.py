import os


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
    file_name = os.path.basename(file_path)

    name_parts = file_name.split('.', 1)

    if len(name_parts) > 1:
        new_file_name = name_parts[0] + '.txt' + '.' + name_parts[1]
    else:
        new_file_name = file_name + '.txt'
    return new_file_name


def find_all_valid_pairs_file(dir_path: str) -> str:
    for file in os.listdir(dir_path):
        if file.endswith('.allValidPairs'):
            full_path = os.path.join(dir_path, file)
            return full_path