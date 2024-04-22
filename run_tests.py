import unittest
import os

from saradomin.main import run

from tests import test_config
from tests.test_output import test_output_factory


def check_paths_exist(paths: list[str]) -> None:
    """
    Checks if the given paths exist. Prints a message for each path indicating whether it exists.
    """
    for path in paths:
        if not os.path.exists(path) and os.path.isdir(path):
            raise f"Tests cannot be started cuz {path} is not dir"


if __name__ == "__main__":
    fastq_dir_path: str = test_config.FASTQ_DIR
    output_dir_path: str = test_config.OUTPUT_DIR

    # if path are relative convert for abs
    if not os.path.isabs(fastq_dir_path):
        fastq_dir_path = os.path.abspath(fastq_dir_path)
    if not os.path.isabs(output_dir_path):
        output_dir_path = os.path.abspath(output_dir_path)

    # set env vars
    os.environ["FASTQ_DIR"] = fastq_dir_path
    os.environ["OUTPUT_DIR"] = output_dir_path

    run()  # script

    suite = unittest.TestSuite()

    check_paths_exist([test_config.FASTQ_DIR])

    test_class = test_output_factory(fastq_dir_path, output_dir_path)
    tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
    suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
