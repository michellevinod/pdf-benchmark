from parsers.docling_parser import DoclingParser

parser = DoclingParser()

parser.parse(
    pdf_path="benchmark_dataset/PDF_Benchmarking_Tester.pdf",
    output_path="outputs/docling/output.md",
)

print("Docling extraction completed successfully!")