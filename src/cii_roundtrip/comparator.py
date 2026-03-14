import hashlib
from typing import Tuple, Dict, Any, List

def _sha256(filepath: str) -> str:
    """Computes SHA-256 of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def compare_files(orig_filepath: str, gen_filepath: str) -> Dict[str, Any]:
    """
    Performs a character-by-character and line-by-line comparison between
    the original CAESAR-II file and the generated file.

    Produces structured diagnostics suitable for JSON output.
    """
    orig_sha = _sha256(orig_filepath)
    gen_sha = _sha256(gen_filepath)

    exact_match = (orig_sha == gen_sha)

    with open(orig_filepath, 'r', encoding='latin-1') as f1, open(gen_filepath, 'r', encoding='latin-1') as f2:
        orig_lines = f1.readlines()
        gen_lines = f2.readlines()

    line_diff_count = abs(len(orig_lines) - len(gen_lines))
    byte_diff_count = 0
    mismatches = []

    mismatch_histogram = {
        "whitespace": 0,
        "precision": 0,
        "exponent": 0,
        "sign": 0,
        "missing_lines": line_diff_count,
        "other": 0
    }

    min_lines = min(len(orig_lines), len(gen_lines))

    for line_idx in range(min_lines):
        l1 = orig_lines[line_idx]
        l2 = gen_lines[line_idx]

        if l1 != l2:
            line_diff_count += 1

            # Character offset diffs
            char_diffs = []
            min_len = min(len(l1), len(l2))

            for char_idx in range(min_len):
                if l1[char_idx] != l2[char_idx]:
                    byte_diff_count += 1
                    char_diffs.append(char_idx)

                    # Heuristics for mismatch type
                    c1, c2 = l1[char_idx], l2[char_idx]
                    if c1.isspace() or c2.isspace():
                        mismatch_histogram["whitespace"] += 1
                    elif c1 in '+-' or c2 in '+-':
                        mismatch_histogram["sign"] += 1
                    elif c1 in 'eEdD' or c2 in 'eEdD':
                        mismatch_histogram["exponent"] += 1
                    elif c1.isdigit() and c2.isdigit():
                        mismatch_histogram["precision"] += 1
                    else:
                        mismatch_histogram["other"] += 1

            # Length mismatch bytes
            byte_diff_count += abs(len(l1) - len(l2))

            mismatches.append({
                "line": line_idx + 1,
                "diff_positions": char_diffs,
                "orig_snippet": l1.strip(),
                "gen_snippet": l2.strip()
            })

    return {
        "exact_match": exact_match,
        "original_sha256": orig_sha,
        "generated_sha256": gen_sha,
        "byte_diff_count": byte_diff_count,
        "line_diff_count": line_diff_count,
        "mismatches_histogram": mismatch_histogram,
        "mismatch_samples": mismatches[:20]  # Just top 20 for the JSON report
    }
