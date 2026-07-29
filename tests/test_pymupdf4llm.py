from pathlib import Path

import pymupdf4llm

pdf_path = "benchmark_dataset/PDF_Benchmarking_Tester.pdf"

markdown = pymupdf4llm.to_markdown(pdf_path)

print(markdown[:1000])

output_path = Path("outputs/pymupdf4llm/output.md")
output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(
    markdown,
    encoding="utf-8"
)

print(f"\nSaved to {output_path}")