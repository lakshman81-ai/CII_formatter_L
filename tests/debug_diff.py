import os
import sys
import copy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.serializer import serialize_to_cii
from src.cii_roundtrip.comparator import compare_files

def run_debug():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, "SAMPLE 2", "BENCHMARK.CII")

    p = Parser(test_file, n1_allocation=2000)
    data = p.parse()

    # Duplicate exactly
    data2 = copy.deepcopy(data)

    out_cii = "test_raw_serializer.cii"
    serialize_to_cii(data2, out_cii)

    report = compare_files(test_file, out_cii)
    print(f"Byte diff (pure serialize): {report['byte_diff_count']}, Lines diff: {report['line_diff_count']}")

    for mism in report['mismatch_samples'][:5]:
        print(f"Line {mism['line']}:")
        print(f"  Orig: '{mism['orig_snippet']}'")
        print(f"  Gen : '{mism['gen_snippet']}'")

if __name__ == "__main__":
    run_debug()