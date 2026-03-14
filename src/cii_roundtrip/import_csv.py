import pandas as pd
from typing import Optional
from .models import ParsedCII, ElementBlock

def import_csv_to_cii(csv_path: str, base_cii_data: Optional[ParsedCII] = None) -> ParsedCII:
    """
    Reads a custom CSV file with REL_x and IEL_x columns back into a ParsedCII structure.
    If a base_cii_data is provided, it uses it for Control blocks and Aux blocks.
    Otherwise, it creates a minimal structure.
    """
    df = pd.read_csv(csv_path)

    if base_cii_data is None:
        data = ParsedCII()
    else:
        # Create a shallow copy, but we'll overwrite elements
        data = ParsedCII(
            version=base_cii_data.version,
            control=base_cii_data.control,
            elements=[],
            aux_data=base_cii_data.aux_data,
            miscel_1=base_cii_data.miscel_1,
            units=base_cii_data.units,
            coords=base_cii_data.coords,
            raw_sections=base_cii_data.raw_sections
        )

    elements = []

    for idx, row in df.iterrows():
        rel = []
        for i in range(53):
            col = f"REL_{i+1}"
            if col in df.columns:
                rel.append(float(row[col]))
            else:
                rel.append(0.0)

        iel = []
        for i in range(18):
            col = f"IEL_{i+1}"
            if col in df.columns:
                iel.append(int(row[col]))
            else:
                iel.append(0)

        # Basic text
        pipe_ref = str(row["PIPELINE-REFERENCE"]) if "PIPELINE-REFERENCE" in df.columns and pd.notna(row["PIPELINE-REFERENCE"]) else ""

        el_block = ElementBlock(
            elmt_id=int(idx) + 1,
            rel=rel,
            string_name="",
            line_number=pipe_ref,
            color_line=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            iel=iel,
            raw_rel_strings=[],
            raw_iel_strings=[]
        )
        elements.append(el_block)

    data.elements = elements

    # Update control block if exists
    if data.control:
        data.control.num_elements = len(elements)

    return data
