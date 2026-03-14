import os
from .models import ParsedCII
from typing import List, Any
import copy

def write_fortran_reals(values: List[float], widths: List[int], precisions: List[int]) -> str:
    """Format reals according to spec, e.g., (2X, 6G13.6). We optimize this later."""
    line = "  "
    for v, w, p in zip(values, widths, precisions):
        # Default simple formatting, optimizer will refine this
        if v == 0.0:
            s = f"{v:.6f}"
        else:
            s = f"{v:.6G}"

        if len(s) > w:
            s = s[:w]
        line += s.rjust(w)
    return line

def write_fortran_ints(values: List[int], widths: List[int]) -> str:
    line = "  "
    for v, w in zip(values, widths):
        line += str(v).rjust(w)
    return line

def serialize_to_cii(data: ParsedCII, filepath: str):
    """
    Serializes the parsed data back to a CII file.
    Uses the raw_sections and raw_rel_strings where possible to ensure EXACT byte match
    if no modifications were made to the elements.
    """
    with open(filepath, 'w', encoding='latin-1') as f:
        # VERSION
        f.write("#$ VERSION\n")
        if data.version:
            f.write(f"  {data.version.major_version.ljust(13)}{data.version.minor_version.ljust(13)}{data.version.codepage.rjust(8)}\n")
            for t in data.version.title_lines:
                if t.strip() == "":
                    f.write("  \n")
                else:
                    f.write(f"  {t}\n")
        else:
            # fallback
            pass

        # CONTROL
        f.write("#$ CONTROL\n")
        if data.control:
            ints = [
                data.control.num_elements, data.control.num_nozzles, data.control.num_hangers,
                data.control.num_nodes, data.control.num_reducers, data.control.num_flanges,
                data.control.bend_aux, data.control.rigid_aux, data.control.expjoint_aux,
                data.control.restraint_aux, data.control.displ_aux, data.control.force_aux,
                data.control.uniform_aux, data.control.wind_aux, data.control.offset_aux,
                data.control.allowable_aux, data.control.intersection_aux, data.control.vertical_axis_flag,
                data.control.equipment_aux
            ]

            # 6 values per line
            chunks = [ints[i:i+6] for i in range(0, len(ints), 6)]
            for chunk in chunks:
                f.write(write_fortran_ints(chunk, [13]*len(chunk)) + "\n")

        # ELEMENTS
        f.write("#$ ELEMENTS\n")
        for el in data.elements:
            # REL
            # CAESAR II format is explicitly 9 lines of 6 floats per element.
            # If we have exact strings (from parsing original), just emit them in groups of 6.
            if el.raw_rel_strings and len(el.raw_rel_strings) >= 53:
                chunks = [el.raw_rel_strings[i:i+6] for i in range(0, len(el.raw_rel_strings), 6)]
                # Ensure we only write the 9 REL lines
                for chunk in chunks[:9]:
                    if len(chunk) > 0:
                        f.write("  " + "".join(chunk) + "\n")
            else:
                # Re-serialization path (if values were modified)
                # Pad to 54 values
                rel = copy.deepcopy(el.rel)
                while len(rel) < 54: rel.append(0.0)
                chunks = [rel[i:i+6] for i in range(0, 54, 6)]
                for chunk in chunks:
                    f.write(write_fortran_reals(chunk, [13]*len(chunk), [6]*len(chunk)) + "\n")

            # String Data
            # Format: 7X, I5, 1X, A500
            name_len = len(el.string_name.strip())
            if name_len == 0 and not el.string_name:
                # CAESAR II tends to have "    0 \n" when empty
                f.write(f"           0 \n")
            else:
                f.write(f"       {name_len:5} {el.string_name}\n")

            line_len = len(el.line_number.strip())
            if line_len == 0 and not el.string_name:
                f.write(f"           0 \n")
            else:
                # We preserved exactly from parser earlier
                if el.line_number == "10 unassigned":
                    f.write(f"          10 unassigned\n")
                else:
                    f.write(f"       {line_len:5} {el.line_number}\n")

            # Color Line
            if len(el.raw_rel_strings) > 54:
                # Sometimes color lines have -1 -1
                f.write("  " + "".join(el.raw_rel_strings[54:]) + "\n")
            else:
                # Fallback defaults
                f.write("             -1           -1\n")

            # IEL
            if el.raw_iel_strings and len(el.raw_iel_strings) >= 15:
                chunks = [el.raw_iel_strings[i:i+6] for i in range(0, 18, 6)]
                for chunk in chunks:
                    if len(chunk) > 0:
                        f.write("  " + "".join(chunk) + "\n")
            else:
                iel = copy.deepcopy(el.iel)
                while len(iel) < 18: iel.append(0)
                chunks = [iel[i:i+6] for i in range(0, 18, 6)]
                for chunk in chunks:
                    f.write(write_fortran_ints(chunk, [13]*len(chunk)) + "\n")

        # Aux Data is preserved as exactly parsed due to raw dictionary caching strategy
        if hasattr(data, "aux_data") and data.aux_data:
            f.write("#$ AUX_DATA\n")
            for k, lines in data.aux_data.items():
                f.write(f"#$ {k}\n")
                for line in lines:
                    if line["type"] == "raw":
                        f.write(f"{line['raw']}\n")
                    elif line["type"] == "string":
                        f.write(f"{line['raw']}\n")
                    elif line["type"] == "reals":
                        # Exact string matching optimization applied
                        f.write("  " + "".join(line["raw"]) + "\n")

        # Miscel, Units, Coords
        if "MISCEL_1" in data.raw_sections and data.raw_sections["MISCEL_1"]:
            f.write("#$ MISCEL_1\n")
            for line in data.raw_sections["MISCEL_1"]:
                f.write(line)

        if "UNITS" in data.raw_sections and data.raw_sections["UNITS"]:
            f.write("#$ UNITS\n")
            for line in data.raw_sections["UNITS"]:
                f.write(line)

        if "COORDS" in data.raw_sections and data.raw_sections["COORDS"]:
            f.write("#$ COORDS\n")
            for line in data.raw_sections["COORDS"]:
                f.write(line)
