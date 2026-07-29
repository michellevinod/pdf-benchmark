from liteparse import LiteParse

parser = LiteParse(
    output_format="markdown",
    quiet=True,
)

result = parser.parse("benchmark_dataset/PDF_Benchmarking_Tester.pdf")

print(type(result.pages))
print(len(result.pages))

page = result.pages[0]

print(type(page))
print(dir(page))