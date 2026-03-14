import os
import sys
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.export_csv import generate_custom_csv

def test_custom_csv_export():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, "SAMPLE 2", "BENCHMARK.CII")

    p = Parser(test_file, n1_allocation=2000)
    data = p.parse()

    df = generate_custom_csv(data, export_path="test_export.csv")

    assert len(df) == 22
    expected_cols = [
        "#", "CSV SEQ NO", "Type", "TEXT", "PIPELINE-REFERENCE", "REF NO.", "BORE",
        "EP1 COORDS", "EP2 COORDS", "CP COORDS", "BP COORDS", "SKEY", "SUPPORT COOR",
        "SUPPORT GUID", "CA 1", "CA 2", "CA 3", "CA 4", "CA 5", "CA 6", "CA 7",
        "CA 8", "CA 9", "CA 10", "CA 97", "CA 98", "Fixing Action", "LEN 1", "AXIS 1",
        "LEN 2", "AXIS 2", "LEN 3", "AXIS 3", "BRLEN", "DELTA_X", "DELTA_Y", "DELTA_Z",
        "DIAMETER", "WALL_THICK", "BEND_PTR", "RIGID_PTR", "INT_PTR"
    ]
    for i in range(53): expected_cols.append(f"REL_{i+1}")
    for i in range(18): expected_cols.append(f"IEL_{i+1}")

    assert list(df.columns) == expected_cols

    # Check the first row calculations
    assert df.iloc[0]["DELTA_Y"] == 104.775
    assert df.iloc[0]["LEN 2"] == 104.775
    assert df.iloc[0]["AXIS 2"] == "Up"

    # Check the running coordinates
    # Starts at 12954.000, 2743.200, -14630.399 (from coords block)
    # Element 1 adds dy=104.775
    assert df.iloc[0]["EP1 COORDS"] == "(12954.0,2743.2,-14630.399)"
    assert df.iloc[0]["EP2 COORDS"] == "(12954.0,2847.975,-14630.399)"

    os.remove("test_export.csv")
