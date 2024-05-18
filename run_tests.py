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
    r1_path: str = test_config.FASTQ_READ_1
    r2_path: str = test_config.FASTQ_READ_2
    output_dir_path: str = test_config.OUTPUT_DIR

    # if path are relative convert for abs
    if not os.path.isabs(r1_path):
        r1_path = os.path.abspath(r1_path)
    if not os.path.isabs(output_dir_path):
        output_dir_path = os.path.abspath(output_dir_path)

    # set env vars
    os.environ["FASTQ_READ_1"] = r1_path
    os.environ["FASTQ_READ_2"] = r2_path
    os.environ["OUTPUT_DIR"] = output_dir_path

    os.environ["KMER"] = str(test_config.KMER)
    os.environ["TRAIN_DATA_FRACTION"] = str(test_config.TRAIN_DATA_FRACTION)
    os.environ["NEGATIVE_TRAIN_SAMPLES"] = str(test_config.NEGATIVE_TRAIN_SAMPLES)
    os.environ["NEGATIVE_TEST_SAMPLES"] = str(test_config.NEGATIVE_TEST_SAMPLES)

    run()  # script

    suite = unittest.TestSuite()

    check_paths_exist([test_config.FASTQ_READ_1, test_config.FASTQ_READ_2])

    test_class = test_output_factory(
        r1_path,
        r2_path,
        output_dir_path,
        test_config.KMER,
        test_config.TRAIN_DATA_FRACTION,
        test_config.NEGATIVE_TRAIN_SAMPLES,
        test_config.NEGATIVE_TEST_SAMPLES,
    )
    tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
    suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
