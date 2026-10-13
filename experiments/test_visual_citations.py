from liteparse import LiteParse, search_items

PDF_PATH = "benchmark_dataset/PDF_BenchmarkTester_63Pages.pdf"

# Pick a phrase that definitely exists in your benchmark PDF.
SEARCH_PHRASE = "Safety"

parser = LiteParse()

print("Parsing PDF...")

result = parser.parse(PDF_PATH)

print(f"Searching for: {SEARCH_PHRASE}\n")

found = False

for page in result.pages:

    matches = search_items(
        page.text_items,
        SEARCH_PHRASE,
    )

    if not matches:
        continue

    found = True

    print("=" * 60)
    print(f"Page {page.page_num}")
    print("=" * 60)

    for i, match in enumerate(matches, start=1):

        print(f"Match {i}")
        print(f"Text   : {match.text}")
        print(f"x      : {match.x}")
        print(f"y      : {match.y}")
        print(f"width  : {match.width}")
        print(f"height : {match.height}")
        print()

if not found:
    print("Phrase not found.")