from typing import Dict, Any, List
import pandas as pd
from .models import ParsedCII

def extract_guid_for_restraint(ptr: int, restraint_block: List[Dict[str, Any]]) -> str:
    """
    Extracts the Support GUID from the #$ RESTRANT block based on the 1-based pointer.
    The restraint block has 12 rows per restraint (2 lines x 6 iterations).
    The last two rows of each block of 12 hold the Tag and GUID respectively.
    """
    if not restraint_block:
        return ""

    # 0-based index of the restraint
    idx = ptr - 1

    # Each restraint takes 14 lines in our generic parsed block (12 lines of reals, 2 lines of strings)
    # Actually, in standard format: 12 lines of Reals + 2 lines of Strings = 14 items in the list.

    # Let's count items specifically for the restraint block structure.
    # The parser appends dictionaries.

    # Let's find the N-th string type in the block
    string_items = [item for item in restraint_block if item["type"] == "string"]

    # For each restraint pointer, there are 2 strings: Tag and GUID.
    # So the GUID for pointer N is at string index (N-1)*2 + 1
    guid_idx = (idx * 2) + 1

    if guid_idx < len(string_items):
        return string_items[guid_idx]["raw"].strip()

    return ""

def build_cii_table(data: ParsedCII) -> pd.DataFrame:
    """
    Generates a generic inference table mapping elements to REL and IEL pointers.
    This acts as the canonical data model representation.
    """
    rows = []

    # Optional Coords
    start_x, start_y, start_z = 0.0, 0.0, 0.0
    if data.coords and len(data.coords) > 0:
        start_x = data.coords[0].get("x", 0.0)
        start_y = data.coords[0].get("y", 0.0)
        start_z = data.coords[0].get("z", 0.0)

    for el in data.elements:
        row = {
            "elmt_id": el.elmt_id,
            "from_node": el.rel[0] if len(el.rel) > 0 else 0,
            "to_node": el.rel[1] if len(el.rel) > 1 else 0,
            "dx": el.rel[2] if len(el.rel) > 2 else 0,
            "dy": el.rel[3] if len(el.rel) > 3 else 0,
            "dz": el.rel[4] if len(el.rel) > 4 else 0,
            "diameter": el.rel[5] if len(el.rel) > 5 else 0,
            "wall_thk": el.rel[6] if len(el.rel) > 6 else 0,
            "string_name": el.string_name,
            "line_number": el.line_number,
        }

        # Pointers 1 to 15 (0-based 0 to 14)
        for i in range(min(15, len(el.iel))):
            row[f"aux_ptr_{i+1}"] = el.iel[i]

        rows.append(row)

    return pd.DataFrame(rows)
