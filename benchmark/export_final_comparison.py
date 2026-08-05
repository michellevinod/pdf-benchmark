import csv
import json
from pathlib import Path


INPUT_PATH = Path(
    "results/final_benchmark_results.json"
)

OUTPUT_PATH = Path(
    "results/final_benchmark_comparison.csv"
)


def load_results() -> dict:
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main():

    data = load_results()

    rows = []

    for result in data["parsers"]:

        performance = result.get(
            "performance",
            {},
        )

        text = result.get(
            "text_quality",
            {},
        )

        table = result.get(
            "table_quality",
            {},
        )

        image = result.get(
            "image_quality",
            {},
        )

        layout = result.get(
            "layout_quality",
            {},
        )

        rows.append(
            {
                "parser": result["parser"],

                # Performance
                "execution_time_seconds": performance.get(
                    "execution_time_seconds"
                ),
                "seconds_per_page": performance.get(
                    "processing_time_per_page_seconds"
                ),
                "throughput_pages_per_second": performance.get(
                    "throughput_pages_per_second"
                ),
                "peak_memory_mb": performance.get(
                    "peak_memory_mb"
                ),

                # Text
                "character_error_rate": text.get(
                    "character_error_rate"
                ),
                "word_error_rate": text.get(
                    "word_error_rate"
                ),
                "normalized_edit_similarity": text.get(
                    "normalized_edit_similarity"
                ),
                "text_coverage_percent": text.get(
                    "text_coverage_percent"
                ),

                # Tables
                "table_f1_score": table.get(
                    "table_f1_score"
                ),
                "table_coverage_percent": table.get(
                    "table_coverage_percent"
                ),
                "teds_score": table.get(
                    "teds_score"
                ),

                # Images
                "image_f1_score": image.get(
                    "image_f1_score"
                ),
                "image_mean_iou": image.get(
                    "mean_iou"
                ),

                # Layout
                "layout_precision": layout.get(
                    "layout_precision"
                ),
                "layout_recall": layout.get(
                    "layout_recall"
                ),
                "layout_f1_score": layout.get(
                    "layout_f1_score"
                ),
                "layout_mean_iou": layout.get(
                    "mean_iou"
                ),
            }
        )

    if not rows:
        raise ValueError(
            "No parser results found."
        )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    print("=" * 60)
    print("Final Benchmark Comparison Export")
    print("=" * 60)
    print(
        f"Parsers exported : {len(rows)}"
    )
    print(
        f"Saved            : {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()