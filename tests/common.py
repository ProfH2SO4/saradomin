import os


def process_line(splitter: str, line: str):
    # Remove the tab and following characters which are at the end
    line = line.rstrip().rsplit("\t", 1)[0]

    # Split the line by the specified splitter
    parts = line.split(splitter)

    # Assuming that each segment may have spaces between triplets, we clean and rejoin them
    def clean_and_join(part):
        # Split by spaces, filter empty strings if any, and join back without spaces
        return " ".join("".join(part.split()).split())

    # Process each part by cleaning spaces and joining as required
    r1 = clean_and_join(parts[0])
    r2 = clean_and_join(parts[1])

    return r1, r2


def get_first_file_path(directory):
    """
    This function takes a directory path as input and returns the full path of the first file found in that directory.
    If there are no files in the directory, it returns None.
    """
    # Check if the directory exists
    if not os.path.exists(directory):
        print("Directory does not exist.")
        return None

    # Iterate over the entries in the directory
    for entry in os.listdir(directory):
        # Construct the full path of the entry
        full_path = os.path.join(directory, entry)
        # Check if this entry is a file
        if os.path.isfile(full_path):
            return full_path

    # Return None if no files are found
    return None


def read_input_file(fastq_read_path: str) -> list[str]:
    """
    Saves a modified FASTQ read to a specified output file.
    The saved values looks like this:
    """
    read_sequences: list[str] = []
    with open(fastq_read_path, "r") as fastq_file:
        for line in fastq_file:
            if line.startswith("@"):
                read_id = line.split()[0][1:]  # Remove the '@' character
                sequence_line = next(fastq_file).strip()  # Nucleotide sequence
                next(fastq_file)  # Skip the '+' line
                quality_line = next(fastq_file).strip()  # PHRED quality scores
                read_sequences.append(sequence_line)
    return read_sequences
