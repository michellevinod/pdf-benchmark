from liteparse import LiteParse

parser = LiteParse()

pages = parser.is_complex(
    "benchmark_dataset/PDF_BenchmarkTester_63Pages.pdf"
)

for page in pages:
    print(
        f"Page {page.page_number}"
    )
    print(
        f"Needs OCR: {page.needs_ocr}"
    )
    print(
        f"Reasons: {page.reasons}"
    )
    print("-" * 40)