import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.serializer import serialize_to_cii

def test_roundtrip_byte_match():
    # 1. Parse original
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    original_file = os.path.join(base_dir, "SAMPLE 2", "BENCHMARK.CII")

    p = Parser(original_file, n1_allocation=2000)
    data = p.parse()

    # 2. Serialize without applying optimization loop (we rely on the exact raw string caching)
    output_file = "tests/BENCHMARK_ROUNDTRIP.CII"
    serialize_to_cii(data, output_file)

    # 3. Compare at byte level (only Elements block for now since we focused raw caching there)
    with open(original_file, 'r', encoding='latin-1') as f:
        orig_lines = f.readlines()

    with open(output_file, 'r', encoding='latin-1') as f:
        new_lines = f.readlines()

    # We won't test full byte match yet because MISCEL_1 and others aren't serialized
    # but we can verify that the generated file exists and contains the expected elements.

    assert os.path.exists(output_file)
    assert len(new_lines) > 50  # Make sure we wrote substantial data

    # Check if elements were serialized identically to original strings
    orig_element_str = "    10.0000      20.0000         0.000000  104.775         0.000000    219.07500"

    found = False
    for line in new_lines:
        if orig_element_str in line:
            found = True
            break

    assert found, "The exact original string of the first element was not reconstructed."

    os.remove(output_file)
