#!/usr/bin/env python3
"""
convert_docx_to_pdf.py
Convert one or more .docx files to .pdf using LibreOffice.

Usage:
    python convert_docx_to_pdf.py file.docx                  # single file
    python convert_docx_to_pdf.py *.docx                     # multiple files
    python convert_docx_to_pdf.py file.docx -o /output/dir   # custom output dir
    python convert_docx_to_pdf.py /docs/ -o /pdfs/           # whole directory
"""

import argparse
import subprocess
import sys
import shutil
from pathlib import Path


def convert(docx_path: Path, output_dir: Path) -> Path | None:
    """Convert a single .docx file to PDF. Returns output path on success."""
    output_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(output_dir), str(docx_path)],
        capture_output=True,
        text=True,
    )

    pdf_path = output_dir / (docx_path.stem + ".pdf")

    if result.returncode == 0 and pdf_path.exists():
        return pdf_path

    # soffice sometimes drops the PDF in the source dir; move it if so
    fallback = docx_path.parent / (docx_path.stem + ".pdf")
    if fallback.exists():
        dest = output_dir / fallback.name
        shutil.move(str(fallback), str(dest))
        return dest

    print(f"  [ERROR] {docx_path.name}: {result.stderr.strip() or 'unknown error'}")
    return None


def collect_inputs(paths: list[str]) -> list[Path]:
    """Expand directories and glob patterns into a list of .docx files."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("**/*.docx")))
        elif path.suffix.lower() == ".docx" and path.exists():
            files.append(path)
        else:
            print(f"  [SKIP] Not a .docx file or doesn't exist: {p}")
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Convert .docx files to PDF via LibreOffice."
    )
    parser.add_argument(
        "inputs", nargs="+",
        help=".docx file(s) or directory containing .docx files",
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Directory to write PDFs (default: same folder as each source file)",
    )
    args = parser.parse_args()

    files = collect_inputs(args.inputs)
    if not files:
        print("No .docx files found.")
        sys.exit(1)

    print(f"Converting {len(files)} file(s)...\n")
    ok, fail = 0, 0

    for docx in files:
        out_dir = Path(args.output_dir) if args.output_dir else docx.parent
        print(f"  {docx.name}  →  ", end="", flush=True)
        result = convert(docx, out_dir)
        if result:
            print(result)
            ok += 1
        else:
            fail += 1

    print(f"\nDone. {ok} converted, {fail} failed.")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()