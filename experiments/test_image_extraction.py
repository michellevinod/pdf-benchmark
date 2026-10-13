from liteparse import LiteParse

parser = LiteParse(
    extract_images=True,
)

result = parser.parse(
    "benchmark_dataset/PDF_BenchmarkTester_63Pages.pdf"
)

print("Images extracted:", len(result.images))

for image in result.images[:10]:
    print("-" * 40)
    print("Page:", image.page)
    print("ID:", image.id)
    print("Format:", image.format)
    print("Size:", image.width, "x", image.height)
    print("BBox:", image.bbox)