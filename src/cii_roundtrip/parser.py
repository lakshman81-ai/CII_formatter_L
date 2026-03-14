import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from .logger import Logger
from .models import ParsedCII, VersionBlock, ControlBlock, ElementBlock
from .fortran_utils import parse_fortran_reals, parse_fortran_ints, parse_fortran_string

class Parser:
    def __init__(self, filepath: str, n1_allocation: int = 2000):
        self.filepath = Path(filepath)
        self.n1_allocation = n1_allocation
        self.log = Logger(feature="parser")
        self.data = ParsedCII()

        # Internal state
        self.lines: List[str] = []
        self.idx = 0

        # Calculate N-proportions per specs
        self.n2 = self.n1_allocation // 2
        self.n3 = self.n1_allocation // 3
        self.n4 = self.n1_allocation // 4
        self.n5 = self.n1_allocation // 5
        self.n6 = int(self.n1_allocation / 13.33)

        self.log.event(f"File Opened: {self.filepath}")
        self.log.memory(f"Allocated N1={self.n1_allocation}, N2={self.n2}, N3={self.n3}, N4={self.n4}, N5={self.n5}, N6={self.n6}")

    def load(self):
        try:
            with open(self.filepath, 'r', encoding='latin-1') as f:
                self.lines = f.readlines()
            self.log.info(f"Loaded {len(self.lines)} lines from file.")
        except Exception as e:
            self.log.error(f"Failed to read file: {e}")
            raise

    def parse(self) -> ParsedCII:
        self.load()
        while self.idx < len(self.lines):
            line = self.lines[self.idx].strip()

            if line.startswith("#$"):
                if line.startswith("#$ VERSION"):
                    self._parse_version()
                elif line.startswith("#$ CONTROL"):
                    self._parse_control()
                elif line.startswith("#$ ELEMENTS"):
                    self._parse_elements()
                elif line.startswith("#$ AUX_DATA"):
                    self._parse_aux_data()
                elif line.startswith("#$ MISCEL_1"):
                    self._parse_miscel_1()
                elif line.startswith("#$ UNITS"):
                    self._parse_units()
                elif line.startswith("#$ COORDS"):
                    self._parse_coords()
                else:
                    self.log.warn(f"Unknown block marker {line} at line {self.idx}")
                    self.idx += 1
            else:
                self.idx += 1
        return self.data

    def _parse_version(self):
        self.log.parse(f"Reading #$ VERSION block using FORTRAN format (2X, 2G13.6, I8)...")
        self.idx += 1

        # Line 1: versions
        if self.idx < len(self.lines):
            line1 = self.lines[self.idx]
            # format (2X, 2G13.6, I8) -> skip 2 chars, 13 chars, 13 chars, 8 chars
            if len(line1) >= 28:
                major_version = line1[2:15].strip()
                minor_version = line1[15:28].strip()
                codepage = line1[28:36].strip()

                title_lines = []
                self.idx += 1
                while self.idx < len(self.lines) and not self.lines[self.idx].strip().startswith("#$"):
                    # 2X, A75
                    text = self.lines[self.idx][2:77] if len(self.lines[self.idx]) > 2 else ""
                    title_lines.append(text)
                    self.idx += 1

                self.log.parse(f"Extracted Job Title using format (2X, A75). {len(title_lines)} lines found.")

                self.data.version = VersionBlock(
                    major_version=major_version,
                    minor_version=minor_version,
                    codepage=codepage,
                    title_lines=title_lines
                )
                return
        self.idx += 1

    def _parse_control(self):
        self.log.parse("Reading #$ CONTROL block...")
        self.idx += 1

        if self.idx < len(self.lines):
            line1 = self.lines[self.idx]
            ints1, _ = parse_fortran_ints(line1)
            self.idx += 1
            line2 = self.lines[self.idx]
            ints2, _ = parse_fortran_ints(line2)
            self.idx += 1
            line3 = self.lines[self.idx]
            ints3, _ = parse_fortran_ints(line3)
            self.idx += 1
            line4 = self.lines[self.idx]
            ints4, _ = parse_fortran_ints(line4)
            self.idx += 1

            # Combine them to extract the properties
            all_ints = ints1 + ints2 + ints3 + ints4

            # According to specs:
            # line 1 (6): NUMELT, NUMNOZ, NOHGRS, NONAM, NORED, NUMFLG
            # line 2-4 (14): Bend_Aux, Rigid_Aux, ExpJoint_Aux, Restraint_Aux, Displ_Aux, Force_Aux, Uniform_Aux, Wind_Aux, Offset_Aux, Allowable_Aux, Intersection_Aux, IZUP_Flag, Equipment_Aux
            if len(all_ints) >= 19:
                self.data.control = ControlBlock(
                    num_elements=all_ints[0],
                    num_nozzles=all_ints[1],
                    num_hangers=all_ints[2],
                    num_nodes=all_ints[3],
                    num_reducers=all_ints[4],
                    num_flanges=all_ints[5],

                    bend_aux=all_ints[6],
                    rigid_aux=all_ints[7],
                    expjoint_aux=all_ints[8],
                    restraint_aux=all_ints[9],
                    displ_aux=all_ints[10],
                    force_aux=all_ints[11],
                    uniform_aux=all_ints[12],
                    wind_aux=all_ints[13],
                    offset_aux=all_ints[14],
                    allowable_aux=all_ints[15],
                    intersection_aux=all_ints[16],
                    vertical_axis_flag=all_ints[17],
                    equipment_aux=all_ints[18]
                )
                self.log.parse(f"Processed Control Block. Elements expected: {self.data.control.num_elements}")

    def _parse_elements(self):
        num_elements = self.data.control.num_elements if self.data.control else 0
        self.log.parse(f"Reached #$ ELEMENTS. Processing {num_elements} records.")
        self.idx += 1

        elements = []
        for el_idx in range(num_elements):
            if self.idx >= len(self.lines):
                break

            rel = []
            rel_strings = []

            # 9 lines of REAL data (53 elements formatted 2X, 6G13.6)
            for _ in range(9):
                line = self.lines[self.idx]
                r, s = parse_fortran_reals(line)
                rel.extend(r)
                rel_strings.extend(s)
                self.idx += 1

            # String Data: Element Name
            string_name = parse_fortran_string(self.lines[self.idx])
            self.idx += 1

            # String Data: Line Number
            line_number = parse_fortran_string(self.lines[self.idx])
            self.idx += 1

            # Color Data (2X, 6G13.6)
            color_r, color_s = parse_fortran_reals(self.lines[self.idx])
            self.idx += 1

            # Pointers Data (3 lines of 2X, 6I13, total 18 values)
            iel = []
            iel_strings = []
            for _ in range(3):
                i_vals, i_strs = parse_fortran_ints(self.lines[self.idx])
                iel.extend(i_vals)
                iel_strings.extend(i_strs)
                self.idx += 1

            # Validate basic parameters
            if len(rel) >= 53:
                from_node = rel[0]
                to_node = rel[1]
                dx, dy, dz = rel[2], rel[3], rel[4]

                # Check for zero/missing values as required
                if from_node == 0.0 or to_node == 0.0:
                    self.log.warn(f"Missing To/From fields on element {el_idx+1}. This is explicitly an error per spec.")

                self.log.state(f"Element {el_idx+1} -> From Node: {from_node}, To Node: {to_node}, DX: {dx}, DY: {dy}")

                el_block = ElementBlock(
                    elmt_id=el_idx+1,
                    rel=rel,
                    string_name=string_name,
                    line_number=line_number,
                    color_line=color_r,
                    iel=iel,
                    raw_rel_strings=rel_strings,
                    raw_iel_strings=iel_strings
                )
                elements.append(el_block)
            else:
                self.log.warn(f"Not enough REL data for element {el_idx+1}. Expected 53+, got {len(rel)}")

        self.data.elements = elements

    def _parse_aux_data(self):
        self.log.parse("Reading #$ AUX_DATA block...")
        self.idx += 1

        # Continue reading until next major block
        while self.idx < len(self.lines) and not self.lines[self.idx].strip().startswith("#$ MISCEL_1"):
            line = self.lines[self.idx].strip()

            if line.startswith("#$"):
                aux_type = line[2:].strip()
                self.log.parse(f"Processing Aux subsection: {aux_type}")
                self.idx += 1
                self.data.aux_data[aux_type] = []

                # We simply read rows of floats until another `#$` line
                # Note: true implementation needs specific counts per aux type,
                # but to be robust to varying neutral files we read all floats
                # until the next header, preserving lines exactly.
                while self.idx < len(self.lines) and not self.lines[self.idx].strip().startswith("#$"):
                    # Just grab line
                    data_line = self.lines[self.idx]

                    # Distinguish between REAL format and STRING format
                    # e.g., Restraints have Strings
                    if "unassigned" in data_line.lower() or "    " + str(10) in data_line or len(data_line.strip()) == 0:
                        # Strings/Labels
                        self.data.aux_data[aux_type].append({"type": "string", "raw": data_line.replace('\n','')})
                    else:
                        r, s = parse_fortran_reals(data_line)
                        if r:
                            self.data.aux_data[aux_type].append({"type": "reals", "values": r, "raw": s})
                        else:
                            self.data.aux_data[aux_type].append({"type": "raw", "raw": data_line.replace('\n','')})
                    self.idx += 1
            else:
                self.idx += 1

    def _parse_miscel_1(self):
        self.log.parse("Reading #$ MISCEL_1 block...")
        self.idx += 1

        # Read until Units
        self.data.raw_sections["MISCEL_1"] = []
        while self.idx < len(self.lines) and not self.lines[self.idx].strip().startswith("#$ UNITS"):
            self.data.raw_sections["MISCEL_1"].append(self.lines[self.idx])
            self.idx += 1

    def _parse_units(self):
        self.log.parse("Reading #$ UNITS block...")
        self.idx += 1
        self.data.raw_sections["UNITS"] = []
        while self.idx < len(self.lines) and not self.lines[self.idx].strip().startswith("#$ COORDS") and self.idx < len(self.lines):
            self.data.raw_sections["UNITS"].append(self.lines[self.idx])
            self.idx += 1

    def _parse_coords(self):
        self.log.parse("Reading #$ COORDS block...")
        self.idx += 1

        self.data.raw_sections["COORDS"] = []
        if self.idx < len(self.lines):
            line = self.lines[self.idx]
            self.data.raw_sections["COORDS"].append(line)

            nxyz, _ = parse_fortran_ints(line)
            count = nxyz[0] if nxyz else 0
            self.log.parse(f"Found {count} coordinate definitions.")
            self.idx += 1

            for _ in range(count):
                if self.idx < len(self.lines):
                    l = self.lines[self.idx]
                    self.data.raw_sections["COORDS"].append(l)
                    # Format (2X, I13, 3F13.4)
                    i_val, _ = parse_fortran_ints(l[:15])
                    r_val, _ = parse_fortran_reals(l[15:])
                    if i_val and len(r_val) >= 3:
                        self.data.coords.append({
                            "node": i_val[0],
                            "x": r_val[0],
                            "y": r_val[1],
                            "z": r_val[2]
                        })
                self.idx += 1
