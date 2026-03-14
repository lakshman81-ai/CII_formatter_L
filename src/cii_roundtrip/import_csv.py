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

        # If we have a base CII, attempt to map back to the exact element to preserve raw caching
        # This guarantees 1:1 byte matching for unmodified elements.
        string_name = ""
        # The line number comes from PIPELINE-REFERENCE, but if it wasn't modified in the CSV
        # we'd want to preserve exactly how it was to avoid spacing differences. We'll default
        # to the exact original strings if the numerical REL/IEL didn't change and the text didn't change.
        color_line = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        raw_rel = []
        raw_iel = []
        exact_rel_lines = []
        exact_string_name_line = ""
        exact_line_number_line = ""
        exact_color_line = ""
        exact_iel_lines = []

        pipe_ref = str(row["PIPELINE-REFERENCE"]) if "PIPELINE-REFERENCE" in df.columns and pd.notna(row["PIPELINE-REFERENCE"]) else ""

        if base_cii_data is not None and idx < len(base_cii_data.elements):
            orig_el = base_cii_data.elements[idx]

            # Check if any numerical values actually changed from the base data.
            # Note: Pandas read_csv can sometimes parse floats with slight precision
            # differences (e.g. 10.0 vs 10.0). We use a small epsilon for float comparison.
            rel_changed = False
            for i, val in enumerate(rel):
                orig_val = orig_el.rel[i] if i < len(orig_el.rel) else 0.0
                if abs(val - orig_val) > 1e-5:
                    rel_changed = True
                    break

            iel_changed = False
            for i, val in enumerate(iel):
                orig_val = orig_el.iel[i] if i < len(orig_el.iel) else 0
                if val != orig_val:
                    iel_changed = True
                    break

            if not rel_changed:
                raw_rel = orig_el.raw_rel_strings
                exact_rel_lines = orig_el.exact_rel_lines
                rel = orig_el.rel # ensure exact precision representation matches

            if not iel_changed:
                raw_iel = orig_el.raw_iel_strings
                exact_iel_lines = orig_el.exact_iel_lines

            string_name = orig_el.string_name
            exact_string_name_line = orig_el.exact_string_name_line

            # If the pipe_ref string hasn't semantically changed, keep exact original formatting
            if pipe_ref.strip() == orig_el.line_number.strip():
                pipe_ref = orig_el.line_number
                exact_line_number_line = orig_el.exact_line_number_line

            color_line = orig_el.color_line
            exact_color_line = orig_el.exact_color_line

        el_block = ElementBlock(
            elmt_id=int(idx) + 1,
            rel=rel,
            string_name=string_name,
            line_number=pipe_ref,
            color_line=color_line,
            iel=iel,
            raw_rel_strings=raw_rel,
            raw_iel_strings=raw_iel,
            exact_rel_lines=exact_rel_lines,
            exact_string_name_line=exact_string_name_line,
            exact_line_number_line=exact_line_number_line,
            exact_color_line=exact_color_line,
            exact_iel_lines=exact_iel_lines
        )
        elements.append(el_block)

    data.elements = elements

    # Update control block if exists
    if data.control:
        data.control.num_elements = len(elements)

    return data
