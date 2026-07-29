from parsers.pymupdf4llm_parser import PyMuPDF4LLMParser

parser = PyMuPDF4LLMParser()

parser.parse(
    pdf_path="benchmark_dataset/PDF_Benchmarking_Tester.pdf",
    output_path="outputs/pymupdf4llm/output.md",
)

print("PyMuPDF4LLM extraction completed successfully!")