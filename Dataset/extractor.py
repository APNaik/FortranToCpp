import argparse
import os
from typing import Optional, List

import pandas as pd


def detect_cpp_column(columns: List[str]) -> Optional[str]:
    """
    Heuristically pick the column that likely contains C++ source code.
    Priority order by common names.
    """
    candidates = [
        "cpp", "cxx", "code_cpp", "cpp_code", "C++", "c++", "cpp_src",
        "predicted_cpp", "translated_cpp", "target_cpp", "output_cpp",
        "code", "source", "src",
    ]
    cols_lower = {c.lower(): c for c in columns}
    for name in candidates:
        if name.lower() in cols_lower:
            return cols_lower[name.lower()]
    # fallback: prefer any object/string dtype column
    return None


def get_first_row_code(df: pd.DataFrame, explicit_column: Optional[str] = None) -> tuple[str, str]:
    """
    Returns (column_name, code_string) from the first row.
    Raises ValueError if not found.
    """
    if df.empty:
        raise ValueError("The parquet file has no rows.")

    # If explicit column is provided, trust it.
    if explicit_column:
        if explicit_column not in df.columns:
            raise ValueError(f"Column '{explicit_column}' not found. Available columns: {list(df.columns)}")
        val = df.iloc[0][explicit_column]
        if pd.isna(val):
            raise ValueError(f"First row value in column '{explicit_column}' is NaN/empty.")
        return explicit_column, str(val)

    # Try heuristic detection
    col = detect_cpp_column(list(df.columns))
    if col is not None:
        val = df.iloc[0][col]
        if pd.notna(val) and isinstance(val, (str, bytes)):
            return col, val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else str(val)

    # As a last resort, scan columns for a long string that looks like C++
    row = df.iloc[0]
    best_col = None
    best_score = -1
    for c in df.columns:
        v = row[c]
        if pd.isna(v):
            continue
        s = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
        # simple heuristic: contains common C++ tokens and is longer than a threshold
        score = 0
        tokens = ["#include", "std::", "int main", ";", "::", "template", "using "]
        score += sum(tok in s for tok in tokens)
        score += int(len(s) > 50)
        if score > best_score:
            best_score = score
            best_col = c
            best_val = s
    if best_col is None or best_score <= 0:
        raise ValueError("Could not confidently detect a C++ code column. Provide --column explicitly.")
    return best_col, best_val


def _unescape_common(s: str) -> str:
    """Convert common escaped sequences (\\n, \\t, \\r, \\') to real characters.
    Avoid full unicode_escape to prevent over-decoding code content.
    """
    # First collapse Windows-style escaped newlines like "\\r\\n" to "\n"
    s = s.replace("\\r\\n", "\n")
    s = s.replace("\\n", "\n")
    s = s.replace("\\r", "\r")
    s = s.replace("\\t", "\t")
    s = s.replace("\\\\", "\\")
    return s


def _simple_format_cpp(code: str) -> str:
    """A lightweight C++ formatter: trims, normalizes blank lines, and indents by braces.
    Not a full parser, but good enough for auto-generated snippets.
    """
    # Normalize newlines
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    # Ensure includes are on their own lines
    code = code.replace("#include", "\n#include").lstrip("\n")
    # Split and clean lines
    raw_lines = [ln.rstrip() for ln in code.split("\n")]

    out_lines: list[str] = []
    indent = 0
    def emit_blank():
        if out_lines and out_lines[-1] != "":
            out_lines.append("")

    for ln in raw_lines:
        t = ln.strip()
        if not t:
            emit_blank()
            continue

        # includes and pragmas stay at col 0
        if t.startswith("#include") or t.startswith("#pragma"):
            out_lines.append(t)
            continue

        # dedent on closing brace first
        dedent_now = t.startswith("}") or t.startswith(");") and t == "};"
        if dedent_now:
            indent = max(0, indent - 1)

        out_lines.append(("    " * indent) + t)

        # adjust indent based on braces on the line
        # naive count, acceptable for generated code
        opens = t.count("{")
        closes = t.count("}")
        indent += max(0, opens - closes)

    # collapse multiple blank lines
    cleaned: list[str] = []
    for l in out_lines:
        if l == "" and (not cleaned or cleaned[-1] == ""):
            continue
        cleaned.append(l)

    return "\n".join(cleaned).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Extract first-row C++ code from a parquet and write to a .cpp file.")
    parser.add_argument("--parquet", default=os.path.join(os.path.dirname(__file__), "combined.parquet"),
                        help="Path to the parquet file (default: Dataset/combined.parquet)")
    parser.add_argument("--column", default=None, help="Column name that contains the C++ code (optional)")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "first_row.cpp"),
                        help="Output .cpp file path (default: Dataset/first_row.cpp)")
    args = parser.parse_args()

    df = pd.read_parquet(args.parquet)
    col, code = get_first_row_code(df, args.column)

    # Post-process: unescape common sequences and format
    code = _unescape_common(code)
    code = _simple_format_cpp(code)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(code)
    print(f"Wrote C++ code from column '{col}' to: {args.out}")


if __name__ == "__main__":
    main()
