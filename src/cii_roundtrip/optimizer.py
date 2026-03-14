import copy
from typing import List, Tuple, Dict, Any
import numpy as np
from .models import ParsedCII
from .fortran_utils import parse_fortran_reals

def try_format(val: float, width: int, precision: int, use_exp: bool, exp_plus: bool, zeroes: str) -> str:
    """
    Attempts a specific FORTRAN formatting permutation.
    """
    if val == 0.0:
        if zeroes == "0.000000": return " 0.000000".rjust(width)
        elif zeroes == "0": return "0".rjust(width)
        else: return "0.0".rjust(width)

    if use_exp:
        # 1.23E+03
        s = f"{val:.{precision}E}"
        if not exp_plus:
            s = s.replace("E+", "E")
    else:
        # 1.23456
        s = f"{val:.{precision}f}"

    return s.rjust(width)[:width]

def optimize_column_format(original_strings: List[str], values: List[float]) -> dict:
    """
    Local search heuristic to find the best format parameters for a given column
    (e.g., REL[1] across all elements) to match the original byte-string exactly.
    """
    best_diff = float('inf')
    best_params = {}

    # Search space
    precisions = [0, 1, 2, 3, 4, 5, 6, 7]
    use_exps = [False, True]
    exp_pluses = [True, False]
    zero_styles = ["0.000000", "0", "0.0"]

    for p in precisions:
        for u_e in use_exps:
            for e_p in exp_pluses:
                for zs in zero_styles:
                    diff_score = 0
                    for s_orig, v in zip(original_strings, values):
                        # Pad s_orig to 13 just in case
                        s_orig_padded = s_orig.ljust(13)
                        s_gen = try_format(v, 13, p, u_e, e_p, zs)

                        # Char-by-char diff
                        diff_score += sum(1 for a, b in zip(s_orig_padded, s_gen) if a != b)

                    if diff_score < best_diff:
                        best_diff = diff_score
                        best_params = {
                            "precision": p,
                            "use_exp": u_e,
                            "exp_plus": e_p,
                            "zero_style": zs
                        }

                    if best_diff == 0:
                        return best_params, best_diff # Exact match found!

    return best_params, best_diff

def run_optimization_loop(data: ParsedCII) -> Tuple[ParsedCII, Dict[str, Any]]:
    """
    Runs the optimization loop over the elements' REL array to discover the canonical
    Fortran formatting rules for this specific .cii file, ensuring re-serialization
    results in a 0-byte diff where possible.
    """
    optimized_data = copy.deepcopy(data)

    report = {
        "status": "completed",
        "optimization_trace": []
    }

    if not optimized_data.elements:
        report["status"] = "no_elements"
        return optimized_data, report

    # Gather column data for the 53 REL fields
    num_fields = 53
    col_strings = [[] for _ in range(num_fields)]
    col_values = [[] for _ in range(num_fields)]

    for el in optimized_data.elements:
        for i in range(min(num_fields, len(el.rel))):
            col_values[i].append(el.rel[i])
            if i < len(el.raw_rel_strings):
                col_strings[i].append(el.raw_rel_strings[i])

    # Optimize per column
    col_formats = []
    total_col_diffs = 0
    for i in range(num_fields):
        if not col_strings[i]:
            col_formats.append(None)
            continue

        best_fmt, best_diff = optimize_column_format(col_strings[i], col_values[i])
        total_col_diffs += best_diff
        col_formats.append(best_fmt)

        report["optimization_trace"].append({
            "column": f"REL[{i+1}]",
            "best_params": best_fmt,
            "min_diff_achieved": best_diff
        })

    report["total_col_diffs_after_opt"] = total_col_diffs
    return optimized_data, report
