import unittest
import os

from . import common


def test_output_factory(input_dir_path: str, output_dir_path: str):
    def _init(self, methodName="runTest"):
        TestOutputFiles.__init__(self, methodName, input_dir_path, output_dir_path)

    return type(f"TestModelData", (TestOutputFiles,), {"__init__": _init})


class TestOutputFiles(unittest.TestCase):
    def __init__(self, methodName: str, input_dir_path: str, output_dir_path: str):
        super(TestOutputFiles, self).__init__(methodName)
        self.input_dir_path = input_dir_path
        self.output_dir_path = output_dir_path
        self.sub_dirs = ["train", "test"]

    def test_output_structure(self):
        """In each directory must be 2 directories with name train and test. In each of them must be 2 files."""
        # Directories to check within the output directory

        for sub_dir in self.sub_dirs:
            # Build the path to the subdirectory
            dir_path = os.path.join(self.output_dir_path, sub_dir)

            # Check if the subdirectory exists
            self.assertTrue(os.path.exists(dir_path), f"{sub_dir} directory does not exist at {dir_path}")
            self.assertTrue(os.path.isdir(dir_path), f"{sub_dir} is not a directory")

            # List files in the subdirectory
            files = os.listdir(dir_path)

            # Check if there are exactly 2 files in the directory
            self.assertEqual(
                len(files), 2, f"There should be exactly 2 files in the {sub_dir} directory, but found {len(files)}"
            )

    def test_right_transformed_train(self):
        """In train directories read Trios(uid, seq, score) must be correctly transformed"""
        input_entries = os.listdir(self.input_dir_path)
        input_files = [
            os.path.join(self.input_dir_path, entry)
            for entry in input_entries
            if os.path.isfile(os.path.join(self.input_dir_path, entry))
        ]

        read_1_input = input_files.pop(0) if "_R1" in input_files[0] else input_files[1]
        read_2_input = input_files[0]

        train_dir = f"{self.output_dir_path}/train"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        read_1_output = file_paths[0]
        read_2_output = file_paths[1]

        # 1. read
        file_input = common.read_input_file(read_1_input)
        file_output = common.read_output_file(read_1_output)

        for key in file_output.keys():
            self.assertEqual(file_input[key][0], file_output[key][0], msg=f"Seq in read {key} are not equal")
            self.assertEqual(file_input[key][1], file_output[key][1], msg=f"Score in read {key} are not equal")

        # 2. read
        file_input = common.read_input_file(read_2_input)
        file_output = common.read_output_file(read_2_output)
        for key in file_output.keys():
            self.assertEqual(file_input[key][0], file_output[key][0], msg=f"Seq in read {key} are not equal")
            self.assertEqual(file_input[key][1], file_output[key][1], msg=f"Score in read {key} are not equal")

    def test_right_transformed_test(self):
        """In test directories read Trios(uid, seq, score) must be correctly transformed"""
        input_entries = os.listdir(self.input_dir_path)
        input_files = [
            os.path.join(self.input_dir_path, entry)
            for entry in input_entries
            if os.path.isfile(os.path.join(self.input_dir_path, entry))
        ]

        read_1_input = input_files.pop(0) if "_R1" in input_files[0] else input_files[1]
        read_2_input = input_files[0]

        train_dir = f"{self.output_dir_path}/test"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        read_1_output = file_paths[0]
        read_2_output = file_paths[1]

        # 1. read
        file_input = common.read_input_file(read_1_input)
        file_output = common.read_output_file(read_1_output)

        for key in file_output.keys():
            self.assertEqual(file_input[key][0], file_output[key][0], msg=f"Seq in read {key} are not equal")
            self.assertEqual(file_input[key][1], file_output[key][1], msg=f"Score in read {key} are not equal")

        # 2. read
        file_input = common.read_input_file(read_2_input)
        file_output = common.read_output_file(read_2_output)
        for key in file_output.keys():
            self.assertEqual(file_input[key][0], file_output[key][0], msg=f"Seq in read {key} are not equal")
            self.assertEqual(file_input[key][1], file_output[key][1], msg=f"Score in read {key} are not equal")

    def test_all_uids_train(self):
        """In train directory, both reads must contain same uids"""
        train_dir = f"{self.output_dir_path}/train"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        read_1_output = file_paths[0]
        read_2_output = file_paths[1]

        read_1_uids = common.get_read_uid_from_output(read_1_output)
        read_2_uids = common.get_read_uid_from_output(read_2_output)

        for item in read_1_uids:
            self.assertTrue(item in read_2_uids, msg=f"item {item} in reads_1 not in reads_2")

    def test_all_uids_test(self):
        """In test directory, both reads must contain same uids"""
        train_dir = f"{self.output_dir_path}/test"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        read_1_output = file_paths[0]
        read_2_output = file_paths[1]

        read_1_uids = common.get_read_uid_from_output(read_1_output)
        read_2_uids = common.get_read_uid_from_output(read_2_output)

        for item in read_1_uids:
            self.assertTrue(item in read_2_uids, msg=f"uid {item} in reads_1 not in reads_2")

    def test_read_uid_scope(self):
        """Cannot happen that some read uid from train scope is in test scope or vice versa"""
        train_dir = f"{self.output_dir_path}/train"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        train_read_1_output = file_paths[0]
        train_read_2_output = file_paths[1]

        train_dir = f"{self.output_dir_path}/test"
        entries = os.listdir(train_dir)
        file_paths = [
            os.path.join(train_dir, entry) for entry in entries if os.path.isfile(os.path.join(train_dir, entry))
        ]
        test_read_1_output = file_paths[0]
        test_read_2_output = file_paths[1]

        train_read_1_uids = common.get_read_uid_from_output(train_read_1_output)
        test_read_2_uids = common.get_read_uid_from_output(test_read_2_output)

        for item in train_read_1_uids:
            self.assertTrue(item not in test_read_2_uids, msg=f"uid {item} in train is in test")
