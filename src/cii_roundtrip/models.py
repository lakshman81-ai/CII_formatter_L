from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class VersionBlock(BaseModel):
    major_version: str
    minor_version: str
    codepage: str
    title_lines: List[str]

class ControlBlock(BaseModel):
    num_elements: int
    num_nozzles: int
    num_hangers: int
    num_nodes: int
    num_reducers: int
    num_flanges: int

    # Aux Counts
    bend_aux: int
    rigid_aux: int
    expjoint_aux: int
    restraint_aux: int
    displ_aux: int
    force_aux: int
    uniform_aux: int
    wind_aux: int
    offset_aux: int
    allowable_aux: int
    intersection_aux: int
    vertical_axis_flag: int
    equipment_aux: int

class ElementBlock(BaseModel):
    elmt_id: int
    rel: List[float] # 98 items
    string_name: str
    line_number: str
    color_line: List[float]
    iel: List[int] # 18 items

    # Original strings for exact re-serialization optimization
    raw_rel_strings: List[str] = []
    raw_iel_strings: List[str] = []

    # EXACT LINE CACHES for zero-byte match
    exact_rel_lines: List[str] = []
    exact_string_name_line: str = ""
    exact_line_number_line: str = ""
    exact_color_line: str = ""
    exact_iel_lines: List[str] = []

class Hanger(BaseModel):
    stiffness: float
    allow_var: float
    rigid_disp: float
    space: float
    cold_load_1: float
    hot_load_1: float
    op_load: float
    max_travel: float
    multi_opt: float
    hardware_wt: float
    ceff: float
    tag: str
    guid: str

class HangerControl(BaseModel):
    default_table: int
    def_var: float
    def_rig: float
    def_mxtravel: float
    def_shtspr: float
    def_mul: float
    def_oper: int
    act_cld: int
    num_hgr_lds: int
    actual: int
    multi_opts: int

class ParsedCII(BaseModel):
    version: Optional[VersionBlock] = None
    control: Optional[ControlBlock] = None
    elements: List[ElementBlock] = []
    aux_data: Dict[str, List[Any]] = {} # e.g. "BEND": [ [v1..v15], ... ]
    miscel_1: Dict[str, Any] = {}
    units: Dict[str, Any] = {}
    coords: List[Dict[str, Any]] = []

    # Raw representation to aid bytewise-matching
    raw_sections: Dict[str, List[str]] = {}