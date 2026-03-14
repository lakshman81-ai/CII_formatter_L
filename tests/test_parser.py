import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.cii_roundtrip.fortran_utils import parse_fortran_reals, parse_fortran_ints

def test_parse_fortran_reals():
    line = "    10.0000      20.0000         0.000000  104.775         0.000000    219.07500"
    floats, raw = parse_fortran_reals(line)
    assert len(floats) == 6
    assert floats[0] == 10.0
    assert floats[3] == 104.775
    assert len(raw) == 6
    assert raw[0] == "  10.0000    "

def test_parse_fortran_ints():
    line = "              0            1            0            0            1            0"
    ints, raw = parse_fortran_ints(line)
    assert len(ints) == 6
    assert ints[1] == 1
    assert len(raw) == 6
    assert raw[1] == "            1"
