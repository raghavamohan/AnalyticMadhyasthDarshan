"""Rebuild the standalone Primer book and plan PDFs from their Markdown sources."""

import argparse
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
DOCUMENTS = {
    'book': ('build_primer_pdf.py', 'madhyasth-darshan-primer.pdf'),
    'plan': ('build_primer_plan_pdf.py', 'madhyasth-darshan-primer-book-plan-revised.pdf'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('documents', nargs='*', help='book and/or plan (default: both documents)')
    parser.add_argument('--font-dir', type=Path, help='Directory containing Georgia and Mangal font files')
    parser.add_argument('--vendor', type=Path, help='Optional directory of installed Python dependencies')
    parser.add_argument('--output-dir', type=Path, default=HERE, help='PDF output directory (default: Primer)')
    args = parser.parse_args()
    documents = args.documents or list(DOCUMENTS)
    for document in documents:
        if document not in DOCUMENTS:
            parser.error(f'unknown document {document!r}; choose book or plan')
    output_dir = args.output_dir.resolve()
    for document in dict.fromkeys(documents):
        script, filename = DOCUMENTS[document]
        command = [sys.executable, str(HERE / script), '--output', str(output_dir / filename)]
        for option, value in [('--font-dir', args.font_dir), ('--vendor', args.vendor)]:
            if value is not None:
                command.extend([option, str(value.resolve())])
        subprocess.run(command, check=True, cwd=HERE.parent)


if __name__ == '__main__':
    main()
