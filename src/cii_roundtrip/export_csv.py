import pandas as pd
from typing import List, Tuple, Dict, Any
from .models import ParsedCII
from .inference import extract_guid_for_restraint

def get_starting_coords(data: ParsedCII) -> Tuple[float, float, float]:
    if data.coords and len(data.coords) > 0:
        return (data.coords[0].get("x", 0.0), data.coords[0].get("y", 0.0), data.coords[0].get("z", 0.0))
    return (0.0, 0.0, 0.0)

def generate_custom_csv(data: ParsedCII, export_path: str = "custom_pipeline_export.csv") -> pd.DataFrame:
    """
    Instruction for AI: Generate the highly specific 41-column CSV format.
    """

    # Define the exact 41 columns requested by the user
    columns = [
        "#", "CSV SEQ NO", "Type", "TEXT", "PIPELINE-REFERENCE", "REF NO.", "BORE",
        "EP1 COORDS", "EP2 COORDS", "CP COORDS", "BP COORDS", "SKEY", "SUPPORT COOR",
        "SUPPORT GUID", "CA 1", "CA 2", "CA 3", "CA 4", "CA 5", "CA 6", "CA 7",
        "CA 8", "CA 9", "CA 10", "CA 97", "CA 98", "Fixing Action", "LEN 1", "AXIS 1",
        "LEN 2", "AXIS 2", "LEN 3", "AXIS 3", "BRLEN", "DELTA_X", "DELTA_Y", "DELTA_Z",
        "DIAMETER", "WALL_THICK", "BEND_PTR", "RIGID_PTR", "INT_PTR"
    ]

    # Extend schema to guarantee NO DATA LOSS for full round-trip reconstruction
    for i in range(53):
        columns.append(f"REL_{i+1}")
    for i in range(18):
        columns.append(f"IEL_{i+1}")

    rows = []
    running_idx = 1
    seq_idx = 1

    # Starting coordinates (From #$ COORDS if available, else 0,0,0)
    current_x, current_y, current_z = get_starting_coords(data)

    # Pre-calculate lookaheads for CA 97, 98, Fixing Action
    to_node_map = {}
    for el in data.elements:
        to_node = el.rel[1] if len(el.rel) > 1 else 0
        to_node_map[el.rel[0]] = el # map from_node to element for fast lookup

    for idx, el in enumerate(data.elements):
        row = {col: "" for col in columns}

        # REL Array parsing (Items 3,4,5 = DX, DY, DZ | Item 6 = OD | Item 7 = Thk)
        from_node = el.rel[0] if len(el.rel) > 0 else 0
        to_node = el.rel[1] if len(el.rel) > 1 else 0
        dx = el.rel[2] if len(el.rel) > 2 else 0
        dy = el.rel[3] if len(el.rel) > 3 else 0
        dz = el.rel[4] if len(el.rel) > 4 else 0
        diameter = el.rel[5] if len(el.rel) > 5 else 0
        wall_thk = el.rel[6] if len(el.rel) > 6 else 0

        # IEL Array Pointers (1=Bend, 2=Rigid, 4=Restraint, 11=Intersection, 14=Flange)
        # 0-based indices: 0, 1, 3, 10, 13
        bend_ptr = el.iel[0] if len(el.iel) > 0 else 0
        rigid_ptr = el.iel[1] if len(el.iel) > 1 else 0
        rest_ptr = el.iel[3] if len(el.iel) > 3 else 0
        int_ptr = el.iel[10] if len(el.iel) > 10 else 0
        flange_ptr = el.iel[13] if len(el.iel) > 13 else 0

        # Coordinate Calculations
        ep1 = (current_x, current_y, current_z)
        current_x += dx
        current_y += dy
        current_z += dz
        ep2 = (current_x, current_y, current_z)

        # Type & TEXT determination
        comp_type = "Pipe"
        if bend_ptr > 0: comp_type = "Bend"
        elif int_ptr > 0: comp_type = "Tee"
        elif flange_ptr > 0: comp_type = "Flange"
        elif rest_ptr > 0: comp_type = "Support"

        # Axis and Length Calculations
        if dx != 0:
            row["LEN 1"] = abs(dx)
            row["AXIS 1"] = "East" if dx > 0 else "West"
        if dy != 0:
            row["LEN 2"] = abs(dy)
            row["AXIS 2"] = "Up" if dy > 0 else "Down"
        if dz != 0:
            row["LEN 3"] = abs(dz)
            row["AXIS 3"] = "North" if dz > 0 else "South"

        # Assign basic values
        row["#"] = running_idx
        row["CSV SEQ NO"] = seq_idx
        row["Type"] = comp_type
        # Add OD to TEXT
        row["TEXT"] = f"{comp_type} {from_node}-{to_node}, OD: {diameter}"
        row["PIPELINE-REFERENCE"] = el.line_number
        row["BORE"] = diameter
        row["DIAMETER"] = diameter
        row["WALL_THICK"] = wall_thk
        row["DELTA_X"] = dx
        row["DELTA_Y"] = dy
        row["DELTA_Z"] = dz

        # Format tuples cleanly avoiding parenthesis for pure CSV coords usually requested
        row["EP1 COORDS"] = f"({ep1[0]},{ep1[1]},{ep1[2]})"
        row["EP2 COORDS"] = f"({ep2[0]},{ep2[1]},{ep2[2]})"

        cpx = (ep1[0] + ep2[0]) / 2
        cpy = (ep1[1] + ep2[1]) / 2
        cpz = (ep1[2] + ep2[2]) / 2
        row["CP COORDS"] = f"({cpx},{cpy},{cpz})"

        # Raw Pointers
        row["BEND_PTR"] = bend_ptr
        row["RIGID_PTR"] = rigid_ptr
        row["INT_PTR"] = int_ptr

        # Lookahead Logic (CA 97, CA 98, Fixing Action)
        # Find the element where FROM node == current TO node
        next_el = to_node_map.get(to_node)

        if next_el:
            n_bend_ptr = next_el.iel[0] if len(next_el.iel) > 0 else 0
            n_flange_ptr = next_el.iel[13] if len(next_el.iel) > 13 else 0
            n_int_ptr = next_el.iel[10] if len(next_el.iel) > 10 else 0

            if n_bend_ptr > 0:
                row["CA 97"] = str(seq_idx)
            if n_flange_ptr > 0:
                row["CA 98"] = str(seq_idx)
            if n_int_ptr > 0:
                row["Fixing Action"] = str(seq_idx)

        # Extract Support GUID if Restraint Pointer exists
        if rest_ptr > 0:
            restraint_block = data.aux_data.get("RESTRANT", [])
            row["SUPPORT GUID"] = extract_guid_for_restraint(rest_ptr, restraint_block)
            row["SUPPORT COOR"] = row["EP2 COORDS"]

        # Append pure arrays
        for i in range(53):
            row[f"REL_{i+1}"] = el.rel[i] if i < len(el.rel) else 0.0
        for i in range(18):
            row[f"IEL_{i+1}"] = el.iel[i] if i < len(el.iel) else 0

        # Run Counters
        running_idx += 1
        seq_idx += 1

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(export_path, index=False)
    return df
