import unittest
import os

from . import common


def is_valid_sequence(seq):
    """Checks if the sequence contains only valid nucleotide characters."""
    return all(c in "ACGTNX" for c in seq)


def test_output_factory(
    r1_path: str,
    r2_path: str,
    output_dir_path: str,
    kmer: int,
    train_data_fraction: float,
    negative_train_samples: float,
    negative_test_samples: float,
):
    def _init(self, methodName="runTest"):
        TestOutputFiles.__init__(
            self,
            methodName,
            r1_path,
            r2_path,
            output_dir_path,
            kmer,
            train_data_fraction,
            negative_train_samples,
            negative_test_samples,
        )

    return type(f"TestModelData", (TestOutputFiles,), {"__init__": _init})


class TestOutputFiles(unittest.TestCase):  # TODO needs refactor
    def __init__(
        self,
        methodName: str,
        r1_path: str,
        r2_path: str,
        output_dir_path: str,
        kmer: int,
        train_data_fraction: float,
        negative_train_samples: float,
        negative_test_samples: float,
    ):
        super(TestOutputFiles, self).__init__(methodName)
        self.r1_path = r1_path
        self.r2_path = r2_path
        self.output_dir_path = output_dir_path
        self.kmer = kmer
        self.train_data_fraction = train_data_fraction
        self.negative_train_samples = negative_train_samples
        self.negative_test_samples = negative_test_samples
        self.output_train_file = common.get_first_file_path(f"{output_dir_path}/train")
        self.output_test_file = common.get_first_file_path(f"{output_dir_path}/test")
        self.read_separator = "[SEP]"

    def test_if_all_reads_in_output(self):
        input_sequence_r1 = common.read_input_file(self.r1_path)
        input_sequence_r2 = common.read_input_file(self.r2_path)

        # load only lines ending with 1
        train_correct_pairs = 0
        test_correct_pairs = 0
        with open(self.output_train_file, "r") as f1:
            next(f1)  # header
            for line in f1:
                stripped_line = line.strip()
                if int(stripped_line[-1]) == 1:
                    train_correct_pairs += 1
        with open(self.output_test_file, "r") as f2:
            next(f2)  # header
            for line in f2:
                stripped_line = line.strip()
                if int(stripped_line[-1]) == 1:
                    test_correct_pairs += 1
        # + 1 cuz header
        self.assertEqual(
            len(input_sequence_r1),
            train_correct_pairs + test_correct_pairs + 1,
            msg=f"train_correct_pairs {train_correct_pairs} test_correct_pairs {test_correct_pairs}",
        )

    def test_train_structure(self):
        input_sequence_r1 = common.read_input_file(self.r1_path)
        input_sequence_r2 = common.read_input_file(self.r2_path)

        # load only lines ending with 1
        r1_outputs: list[str] = []
        r2_outputs: list[str] = []
        with open(self.output_train_file, "r") as f1:
            next(f1)  # header
            for line in f1:
                stripped_line = line.strip()
                if int(stripped_line[-1]) == 1:
                    r1_output, r2_output = common.process_line(self.read_separator, stripped_line)
                    r1_outputs.append(r1_output)
                    r2_outputs.append(r2_output)
        used_indices_r1 = set()  # Set to track used indices from input_sequence_r1
        used_indices_r2 = set()
        for output_pos in range(len(r1_outputs)):
            found = False  # Flag to check if i_r1 is found at the beginning of any string in r1_outputs
            for pos_r1 in range(len(input_sequence_r1)):
                # Check if i_r1 is at the beginning, only appears once at the start, and has not been used yet
                if r1_outputs[output_pos].startswith(input_sequence_r1[pos_r1]) and pos_r1 not in used_indices_r1:
                    if r2_outputs[output_pos].startswith(input_sequence_r2[pos_r1]) and pos_r1 not in used_indices_r2:
                        used_indices_r1.add(pos_r1)  # Mark this pos_r1 as used
                        used_indices_r2.add(pos_r1)
                        break
        self.assertEqual(used_indices_r1, used_indices_r2)

    def test_train_row_structure(self):
        with open(self.output_train_file, "r") as f1:
            next(f1)  # Skip the header
            for line_number, line in enumerate(f1, start=2):  # Start counting from line 2
                parts = line.strip().split()

                # Assert that the separator is present
                self.assertIn(
                    self.read_separator, parts, f"Separator '{self.read_separator}' not found in line {line_number}"
                )

                # Find the index of the separator and assert structure
                sep_index = parts.index(self.read_separator)
                self.assertNotEqual(sep_index, 0, f"Separator is the first element in line {line_number}")
                self.assertNotEqual(
                    sep_index, len(parts) - 1, f"Separator is the last element before the integer in line {line_number}"
                )

                # Check sequences before the separator
                self.assertTrue(
                    all(is_valid_sequence(seq) for seq in parts[:sep_index]),
                    f"Invalid nucleotide sequence before separator in line {line_number}",
                )

                # Check sequences after the separator and before the last element
                self.assertTrue(
                    all(is_valid_sequence(seq) for seq in parts[sep_index + 1 : -1]),
                    f"Invalid nucleotide sequence after separator in line {line_number}",
                )

                # Assert the last element is an integer
                self.assertTrue(parts[-1].isdigit(), f"Last element in line {line_number} is not an integer")

    def test_output_reads_test(self):
        input_sequence_r1 = common.read_input_file(self.r1_path)
        input_sequence_r2 = common.read_input_file(self.r2_path)

        # load only lines ending with 1
        r1_outputs: list[str] = []
        r2_outputs: list[str] = []
        with open(self.output_test_file, "r") as f1:
            next(f1)  # header
            for line in f1:
                stripped_line = line.strip()
                if int(stripped_line[-1]) == 1:
                    r1_output, r2_output = common.process_line(self.read_separator, stripped_line)
                    r1_outputs.append(r1_output)
                    r2_outputs.append(r2_output)
        used_indices_r1 = set()  # Set to track used indices from input_sequence_r1
        used_indices_r2 = set()
        for output_pos in range(len(r1_outputs)):
            found = False  # Flag to check if i_r1 is found at the beginning of any string in r1_outputs
            for pos_r1 in range(len(input_sequence_r1)):
                # Check if i_r1 is at the beginning, only appears once at the start, and has not been used yet
                if r1_outputs[output_pos].startswith(input_sequence_r1[pos_r1]) and pos_r1 not in used_indices_r1:
                    if r2_outputs[output_pos].startswith(input_sequence_r2[pos_r1]) and pos_r1 not in used_indices_r2:
                        used_indices_r1.add(pos_r1)  # Mark this pos_r1 as used
                        used_indices_r2.add(pos_r1)
                        break
        self.assertEqual(used_indices_r1, used_indices_r2)

    def test_row_structure_test(self):
        with open(self.output_test_file, "r") as f1:
            next(f1)  # Skip the header
            for line_number, line in enumerate(f1, start=2):  # Start counting from line 2
                parts = line.strip().split()

                # Assert that the separator is present
                self.assertIn(
                    self.read_separator, parts, f"Separator '{self.read_separator}' not found in line {line_number}"
                )

                # Find the index of the separator and assert structure
                sep_index = parts.index(self.read_separator)
                self.assertNotEqual(sep_index, 0, f"Separator is the first element in line {line_number}")
                self.assertNotEqual(
                    sep_index, len(parts) - 1, f"Separator is the last element before the integer in line {line_number}"
                )

                # Check sequences before the separator
                self.assertTrue(
                    all(is_valid_sequence(seq) for seq in parts[:sep_index]),
                    f"Invalid nucleotide sequence before separator in line {line_number}",
                )

                # Check sequences after the separator and before the last element
                self.assertTrue(
                    all(is_valid_sequence(seq) for seq in parts[sep_index + 1 : -1]),
                    f"Invalid nucleotide sequence after separator in line {line_number}",
                )

                # Assert the last element is an integer
                self.assertTrue(parts[-1].isdigit(), f"Last element in line {line_number} is not an integer")
