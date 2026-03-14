import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.cii_roundtrip.parser import Parser

def test_full_parse_benchmark():
    # Use robust relative path resolution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, "SAMPLE 2", "BENCHMARK.CII")

    p = Parser(test_file, n1_allocation=2000)
    data = p.parse()

    assert data.control is not None
    assert data.version is not None

    assert data.control.num_elements == 22
    assert len(data.elements) == 22

    assert data.elements[0].elmt_id == 1
    assert data.elements[0].rel[0] == 10.0
    assert data.elements[0].rel[1] == 20.0
    assert data.elements[0].iel[1] == 1  # Rigid pointer
    assert data.elements[0].iel[3] == 0  # Restraint pointer
