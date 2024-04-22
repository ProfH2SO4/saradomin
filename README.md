# Saradomin: Hi-C Architect for Neural Networks

## Introduction

The Saradomin project is designed to facilitate the processing of Hi-C Fastq data,
transforming raw sequencing reads into structured datasets suitable for neural network models.

## Table of Contents
- [Project goal](#project-goal)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Structure of output file](#structure-of-output-file)

## Project goal

**Objective:** Transform Hi-C data for use in neural network (NN) models, ensuring the data is optimally formatted for training and validation purposes.

**Key Tasks:**

1. **Data Transformation:** Convert raw Hi-C data into a format suitable for neural network processing. This includes normalizing interaction frequencies and structuring the data into input features that a NN can efficiently process.

2. **Dataset Division:** Split the transformed Hi-C data into training and testing subsets. Ensure that each subset is representative of the overall data characteristics to maintain model reliability across different data points.

3. **Customization of Reads Pair Disruption:** Introduce a configurable disruption ratio for paired-end reads within the Hi-C data. This involves selectively altering the linkage of read pairs to simulate varying degrees of disruption, which is crucial for training the model to handle real-world variations and anomalies in Hi-C data.

**Outcome:** A well-prepared dataset that allows a neural network to learn from both undisturbed and artificially disrupted Hi-C interactions, thereby enhancing the model's robustness and applicability to real-world biological data analysis.

## Installation

### Prerequisites
- Python 3.10 or higher

### Environment Setup
We recommend using a Python virtual environment for dependency management:

1. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   Navigate to the project's root directory and run:
   ```bash
   pip3 install -r requirements.txt
   ```

## Getting Started

### Preparing Your Data
You can use snippet of HiC data in `test_data` or download whole [HiC dataset](https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=SRP050102)


## Configuration

Tailor Saradomin to your project needs by adjusting its configuration:

1. **Custom Configuration parameters File:**
   Pass environment variable. E.g Create `.env` file. (Parameters in .env overrides `config.py`)

2. **Local Configuration:**
   For quick adjustments, modify the `config.py` file in the root directory. This approach is recommended for temporary changes or small-scale projects.

### Structure of Output File
The data file is structured into two distinct sections: the header and the data content.

#### Header
The header section encapsulates critical metadata about the file, including the date of creation
and the schema of the read.

```plaintext
#HEADER#
#DATE=2024-04-22T12:47:59.038200
#pre_processing_version=[0, 1, 0]
#mapping: {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
#schema=1.row UID	2.row NUCLEOTIDE	3.row SCORE
####END####
```

#### Data Content
The Read has always 3 lines in file 1. uid 2. Sequence 3. Score
Each nucleotide is mapped to specific number.
The score(Quality score) is represented by ASCII number.


```plaintext
1
[2, 3]
[66, 66]
```
