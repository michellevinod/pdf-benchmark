import json
from pathlib import Path


RESULTS_DIR = Path("results")

PERFORMANCE_PATH = RESULTS_DIR / "benchmark_results.json"
QUALITY_PATH = RESULTS_DIR / "cached_benchmark_results.json"
OCR_PATH = RESULTS_DIR / "paddleocr_v6_results.json"

OUTPUT_PATH = RESULTS_DIR / "final_benchmark_results.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():

    performance_results = load_json(
        PERFORMANCE_PATH
    )

    quality_results = load_json(
        QUALITY_PATH
    )

    paddleocr_results = load_json(
        OCR_PATH
    )

    performance_by_parser = {
        result["parser"]: result
        for result in performance_results
    }

    final_results = []

    for quality in quality_results:

        parser_name = quality["parser"]

        performance = performance_by_parser.get(
            parser_name,
            {},
        )

        consolidated = {
            "parser": parser_name,
            "status": quality.get(
                "status",
                "Unknown",
            ),

            "performance": {
                "execution_time_seconds": performance.get(
                    "execution_time_seconds"
                ),
                "processing_time_per_page_seconds": performance.get(
                    "processing_time_per_page_seconds"
                ),
                "throughput_pages_per_second": performance.get(
                    "throughput_pages_per_second"
                ),
                "memory_used_mb": performance.get(
                    "memory_used_mb"
                ),
                "peak_memory_mb": performance.get(
                    "peak_memory_mb"
                ),
                "average_cpu_percent": performance.get(
                    "average_cpu_percent"
                ),
                "output_size_kb": performance.get(
                    "output_size_kb"
                ),
            },

            "text_statistics": quality.get(
                "text_statistics",
                {},
            ),

            "text_quality": quality.get(
                "text_quality",
                {},
            ),

            "table_statistics": quality.get(
                "table_statistics",
                {},
            ),

            "table_quality": quality.get(
                "table_quality",
                {},
            ),

            "image_statistics": quality.get(
                "image_statistics",
                {},
            ),

            "image_quality": quality.get(
                "image_quality",
                {},
            ),

            "layout_statistics": quality.get(
                "layout_statistics",
                {},
            ),

            "layout_quality": quality.get(
                "layout_quality",
                {},
            ),
        }

        final_results.append(
            consolidated
        )

    final_output = {
        "parsers": final_results,
        "paddleocr_v6": paddleocr_results,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            final_output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("=" * 60)
    print("Final Benchmark Consolidation")
    print("=" * 60)

    for result in final_results:

        performance = result["performance"]

        print()
        print(
            f"Parser      : {result['parser']}"
        )
        print(
            f"Execution   : "
            f"{performance['execution_time_seconds']} sec"
        )
        print(
            f"Throughput  : "
            f"{performance['throughput_pages_per_second']} pages/sec"
        )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()