from pathlib import Path
from docling.document_converter import DocumentConverter

pdf_path = "benchmark_dataset/PDF_Benchmarking_Tester.pdf"

converter = DocumentConverter()

print("Converting PDF...")

result = converter.convert(pdf_path)

print("Conversion completed!")

# Export Markdown
markdown = result.document.export_to_markdown()

output_path = Path("outputs/docling/output.md")
output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(markdown, encoding="utf-8")

print(f"Markdown saved to: {output_path}")