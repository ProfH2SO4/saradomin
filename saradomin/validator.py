import os


def check_if_file_exists(path_to_file: str) -> bool:
    return os.path.exists(path_to_file)


def check_file_sizes_equal(file_path1: str, file_path2: str) -> bool:

    size1 = os.path.getsize(file_path1)
    size2 = os.path.getsize(file_path2)
    return size1 == size2
