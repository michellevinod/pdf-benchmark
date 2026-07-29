from parsers.liteparse_parser import LiteParseParser

parser = LiteParseParser()

parser.parse(
    pdf_path="benchmark_dataset/PDF_Benchmarking_Tester.pdf",
    output_path="outputs/liteparse/output.md"
)

print("LiteParse extraction completed successfully!")