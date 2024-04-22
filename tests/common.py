from saradomin.transform import encode_sequence, convert_ascii_score_to_int


def get_read_uid_from_output(filename) -> list[int]:
    uids: list[int] = []
    with open(filename, "r") as file:
        # Skip header lines starting with '#'
        lines = [line.strip() for line in file if not line.startswith("#")]

    for i in range(len(lines)):
        if lines[i].isdigit():  # Check if the line contains UID
            uid = int(lines[i])
            uids.append(uid)
    return uids


def read_output_file(filename):
    data = {}
    with open(filename, "r") as file:
        # Skip header lines starting with '#'
        lines = [line.strip() for line in file if not line.startswith("#")]

    # Parse the data
    i = 0
    while i < len(lines):
        if lines[i].isdigit():  # Check if the line contains UID
            uid = int(lines[i])
            nucleotides = eval(lines[i + 1])  # Convert string representation of list to list
            scores = eval(lines[i + 2])
            data[uid] = [nucleotides, scores]
            i += 3  # Move to the next UID
        else:
            i += 1  # Increment index to continue through the list

    return data


def read_input_file(fastq_read_path: str) -> dict:
    """
    Saves a modified FASTQ read to a specified output file.
    The saved values looks like this:
    0
    [4, 0, 1 ,3]
    [35, 60, 60]
    """
    read_id_counter: dict[int, str] = {}
    uid_counter: int = 0
    with open(fastq_read_path, "r") as fastq_file:
        for line in fastq_file:
            if line.startswith("@"):
                read_id = line.split()[0][1:]  # Remove the '@' character
                sequence_line = next(fastq_file).strip()  # Nucleotide sequence
                next(fastq_file)  # Skip the '+' line
                quality_line = next(fastq_file).strip()  # PHRED quality scores

                if read_id not in read_id_counter.values():
                    read_id_counter[uid_counter] = []
                    # encode the entire sequence
                    read_id_counter[uid_counter].append(encode_sequence(sequence_line))
                    read_id_counter[uid_counter].append(convert_ascii_score_to_int(quality_line))
                    uid_counter += 1

                if read_id in read_id_counter.values():
                    # encode the entire sequence
                    read_id_counter[uid_counter].append(encode_sequence(sequence_line))
                    read_id_counter[uid_counter].append(convert_ascii_score_to_int(quality_line))

    return read_id_counter
