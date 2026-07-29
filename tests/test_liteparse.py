from pathlib import Path

from liteparse import LiteParse

pdf_path = "benchmark_dataset/PDF_Benchmarking_Tester.pdf"

parser = LiteParse(
    output_format="markdown",
    quiet=True
)

result = parser.parse(pdf_path)

print(result.text[:1000])

output_path = Path("outputs/liteparse/output.md")
output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(
    result.text,
    encoding="utf-8"
)

print(f"\nSaved to {output_path}")