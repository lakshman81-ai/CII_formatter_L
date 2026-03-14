import re
from typing import List, Tuple
from pydantic import ValidationError

def parse_fortran_reals(line: str) -> Tuple[List[float], List[str]]:
    """
    Parses a FORTRAN (2X, 6G13.6) string.
    Returns the parsed floats and their exact raw string representations.
    """
    if len(line) < 2:
        return [], []

    # Skip the first 2 spaces (2X)
    data_portion = line[2:]

    # 6 columns of 13 characters
    chunk_size = 13
    chunks = [data_portion[i:i+chunk_size] for i in range(0, len(data_portion), chunk_size)]

    # Fortran format ensures exactly 6 chunks per line if fully padded.
    # However, sometimes trailing spaces are omitted in text files. We process up to 6 chunks.
    # If the file is strictly fixed-width, we keep empty chunks as 0.0 to prevent horizontal shifts.

    floats = []
    raw_strings = []
    for chunk in chunks:
        raw_strings.append(chunk)
        if chunk.strip() == "":
            floats.append(0.0)
        else:
            try:
                val = float(chunk.replace('D', 'E')) # Handle old FORTRAN D-exponents
                floats.append(val)
            except ValueError:
                floats.append(0.0)

    return floats, raw_strings

def parse_fortran_ints(line: str) -> Tuple[List[int], List[str]]:
    """
    Parses a FORTRAN (2X, 6I13) string.
    Returns the parsed integers and their exact raw string representations.
    """
    if len(line) < 2:
        return [], []

    data_portion = line[2:]
    chunk_size = 13
    chunks = [data_portion[i:i+chunk_size] for i in range(0, len(data_portion), chunk_size)]

    ints = []
    raw_strings = []
    for chunk in chunks:
        raw_strings.append(chunk)
        if chunk.strip() == "":
            ints.append(0)
        else:
            try:
                val = int(chunk)
                ints.append(val)
            except ValueError:
                ints.append(0)

    return ints, raw_strings

def parse_fortran_string(line: str) -> str:
    """
    Parses FORTRAN string format (7X, I5, 1X, A500)
    We will just grab the A500 part robustly.
    """
    if len(line) < 13:
        return ""
    # Usually length indicator is at pos 7..12
    return line[13:].strip()
