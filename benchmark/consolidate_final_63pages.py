import csv
import json
from pathlib import Path
from typing import Any


RESULTS_DIR = Path("results")

DOCLING_PATH = (
    RESULTS_DIR
    / "docling_batched_63pages_results.json"
)

CACHED_PATH = (
    RESULTS_DIR
    / "cached_benchmark_results.json"
)

HYBRID_PATH = (
    RESULTS_DIR
    / "hybrid_results.json"
)

BENCHMARK_PATH = (
    RESULTS_DIR
    / "benchmark_results.json"
)

FINAL_JSON_PATH = (
    RESULTS_DIR
    / "final_63page_benchmark_results.json"
)

FINAL_CSV_PATH = (
    RESULTS_DIR
    / "final_63page_benchmark_comparison.csv"
)


UNSUPPORTED = "N/A/Unsupported"
NOT_MEASURED = "N/A/Not measured"


def load_json(
    path: Path,
) -> Any:

    if not path.exists():
        raise FileNotFoundError(
            f"Required result file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_parser(
    results: list[dict],
    parser_name: str,
) -> dict:

    for result in results:

        if (
            result.get("parser")
            == parser_name
        ):
            return result

    raise ValueError(
        f"Parser result not found: {parser_name}"
    )


def get_performance(
    benchmark_results: list[dict],
    parser_name: str,
) -> dict:

    result = find_parser(
        benchmark_results,
        parser_name,
    )

    return {
        "execution_time_seconds": (
            result.get(
                "execution_time_seconds"
            )
        ),
        "seconds_per_page": (
            result.get(
                "processing_time_per_page_seconds"
            )
        ),
        "throughput_pages_per_second": (
            result.get(
                "throughput_pages_per_second"
            )
        ),
        "peak_memory_mb": (
            result.get(
                "peak_memory_mb"
            )
        ),
        "average_cpu_percent": (
            result.get(
                "average_cpu_percent"
            )
        ),
    }


def build_docling(
    result: dict,
) -> dict:

    execution_time = result.get(
        "execution_time_seconds"
    )

    page_count = 63

    seconds_per_page = (
        round(
            execution_time / page_count,
            3,
        )
        if execution_time
        else NOT_MEASURED
    )

    throughput = (
        round(
            page_count / execution_time,
            3,
        )
        if execution_time
        else NOT_MEASURED
    )

    return {
        "parser": "docling",
        "display_name": "Docling",
        "version": "2.115.0",
        "status": "Success",
        "page_count": page_count,
        "execution_mode": (
            "10-page batched execution"
        ),
        "performance": {
            "execution_time_seconds": (
                execution_time
            ),
            "seconds_per_page": (
                seconds_per_page
            ),
            "throughput_pages_per_second": (
                throughput
            ),
            # Do not reuse profiler measurements
            # from the failed single-call execution.
            "peak_memory_mb": NOT_MEASURED,
            "average_cpu_percent": NOT_MEASURED,
        },
        "text_quality": result.get(
            "text_quality",
            {},
        ),
        "table_quality": result.get(
            "table_quality",
            {},
        ),
        "image_quality": result.get(
            "image_quality",
            {},
        ),
        "layout_quality": result.get(
            "layout_quality",
            {},
        ),
        "robustness": result.get(
            "robustness",
            {},
        ),
    }


def build_standard_parser(
    parser_name: str,
    display_name: str,
    version: str,
    quality_result: dict,
    performance_result: dict,
) -> dict:

    return {
        "parser": parser_name,
        "display_name": display_name,
        "version": version,
        "status": "Success",
        "page_count": 63,
        "execution_mode": (
            "Standard local parser execution"
        ),
        "performance": performance_result,
        "text_quality": quality_result.get(
            "text_quality",
            {},
        ),
        "table_quality": quality_result.get(
            "table_quality",
            {},
        ),
        "image_quality": quality_result.get(
            "image_quality",
            {},
        ),
        "layout_quality": quality_result.get(
            "layout_quality",
            {},
        ),
        "robustness": quality_result.get(
            "robustness",
            {},
        ),
    }


def build_hybrid(
    result: dict,
) -> dict:

    image_quality = dict(
        result.get(
            "image_quality",
            {},
        )
    )

    # The repaired 63-page ground truth contains
    # 62 valid reference image bounding boxes.
    #
    # Hybrid still cannot be spatially evaluated
    # because its Markdown output does not contain
    # comparable PDF-coordinate image boxes.
    image_quality[
        "valid_reference_bboxes"
    ] = 62

    return {
        "parser": "hybrid",
        "display_name": "Hybrid Approach",
        "version": (
            "Internal / external pipeline"
        ),
        "status": "Success",
        "page_count": 63,
        "execution_mode": (
            "External website pipeline; "
            "downloaded Markdown evaluated locally"
        ),
        "performance": {
            "execution_time_seconds": (
                NOT_MEASURED
            ),
            "seconds_per_page": (
                NOT_MEASURED
            ),
            "throughput_pages_per_second": (
                NOT_MEASURED
            ),
            "peak_memory_mb": (
                NOT_MEASURED
            ),
            "average_cpu_percent": (
                NOT_MEASURED
            ),
        },
        "text_quality": result.get(
            "text_quality",
            {},
        ),
        "table_quality": result.get(
            "table_quality",
            {},
        ),
        "image_quality": image_quality,
        "layout_quality": result.get(
            "layout_quality",
            {},
        ),
        "robustness": result.get(
            "robustness",
            {},
        ),
    }


def flatten_result(
    result: dict,
) -> dict:

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

    return {
        "parser": result.get(
            "display_name"
        ),
        "version": result.get(
            "version"
        ),
        "page_count": result.get(
            "page_count"
        ),
        "execution_mode": result.get(
            "execution_mode"
        ),

        # Performance
        "execution_time_seconds": (
            performance.get(
                "execution_time_seconds"
            )
        ),
        "seconds_per_page": (
            performance.get(
                "seconds_per_page"
            )
        ),
        "throughput_pages_per_second": (
            performance.get(
                "throughput_pages_per_second"
            )
        ),
        "peak_memory_mb": (
            performance.get(
                "peak_memory_mb"
            )
        ),
        "average_cpu_percent": (
            performance.get(
                "average_cpu_percent"
            )
        ),

        # Text
        "character_error_rate": (
            text.get(
                "character_error_rate"
            )
        ),
        "word_error_rate": (
            text.get(
                "word_error_rate"
            )
        ),
        "normalized_edit_similarity": (
            text.get(
                "normalized_edit_similarity"
            )
        ),
        "text_coverage_percent": (
            text.get(
                "text_coverage_percent"
            )
        ),

        # Tables
        "extracted_table_count": (
            table.get(
                "extracted_table_count"
            )
        ),
        "table_precision": (
            table.get(
                "table_precision"
            )
        ),
        "table_recall": (
            table.get(
                "table_recall"
            )
        ),
        "table_f1_score": (
            table.get(
                "table_f1_score"
            )
        ),
        "table_coverage_percent": (
            table.get(
                "table_coverage_percent"
            )
        ),
        "teds_score": (
            table.get(
                "teds_score"
            )
        ),

        # Images
        "extracted_image_count": (
            image.get(
                "extracted_image_count"
            )
        ),
        "image_f1_score": (
            image.get(
                "image_f1_score"
            )
        ),
        "image_mean_iou": (
            image.get(
                "mean_iou"
            )
        ),

        # Layout
        "extracted_layout_blocks": (
            layout.get(
                "extracted_block_count"
            )
        ),
        "layout_precision": (
            layout.get(
                "layout_precision"
            )
        ),
        "layout_recall": (
            layout.get(
                "layout_recall"
            )
        ),
        "layout_f1_score": (
            layout.get(
                "layout_f1_score"
            )
        ),
        "layout_mean_iou": (
            layout.get(
                "mean_iou"
            )
        ),
    }


def main():

    docling_result = load_json(
        DOCLING_PATH
    )

    cached_results = load_json(
        CACHED_PATH
    )

    hybrid_result = load_json(
        HYBRID_PATH
    )

    benchmark_results = load_json(
        BENCHMARK_PATH
    )

    liteparse_quality = find_parser(
        cached_results,
        "liteparse",
    )

    pymupdf_quality = find_parser(
        cached_results,
        "pymupdf4llm",
    )

    liteparse_performance = get_performance(
        benchmark_results,
        "liteparse",
    )

    pymupdf_performance = get_performance(
        benchmark_results,
        "pymupdf4llm",
    )

    final_results = [
        build_docling(
            docling_result
        ),
        build_standard_parser(
            parser_name="liteparse",
            display_name="LiteParse",
            version="2.10.0",
            quality_result=liteparse_quality,
            performance_result=(
                liteparse_performance
            ),
        ),
        build_standard_parser(
            parser_name="pymupdf4llm",
            display_name="PyMuPDF4LLM",
            version="1.28.0",
            quality_result=pymupdf_quality,
            performance_result=(
                pymupdf_performance
            ),
        ),
        build_hybrid(
            hybrid_result
        ),
    ]

    consolidated = {
        "metadata": {
            "description": (
                "Final consolidated 63-page "
                "PDF benchmarking results."
            ),
            "benchmark_document": (
                "PDF_BenchmarkTester_63Pages.pdf"
            ),
            "page_count": 63,
            "reference_table_count": 48,
            "reference_image_count": 62,
            "reference_layout_block_count": 1656,
            "methodology": {
                "quality": (
                    "All four approaches are evaluated "
                    "against the same finalized 63-page "
                    "ground truth using the common "
                    "benchmark metric implementations."
                ),
                "docling_performance": (
                    "Docling performance uses successful "
                    "10-page batched execution because "
                    "the 63-page single-call run encountered "
                    "std::bad_alloc during preprocessing."
                ),
                "standard_performance": (
                    "LiteParse and PyMuPDF4LLM performance "
                    "uses their successful locally profiled "
                    "63-page parser executions."
                ),
                "hybrid_performance": (
                    "Hybrid performance is not reported "
                    "because the pipeline was executed "
                    "externally and was not measured using "
                    "the benchmark's local profiler."
                ),
                "unsupported_metrics": (
                    "N/A/Unsupported indicates that the "
                    "available parser output does not provide "
                    "the comparable information required by "
                    "that metric. It must not be interpreted "
                    "as a score of zero."
                ),
            },
        },
        "parsers": final_results,
    }

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FINAL_JSON_PATH.write_text(
        json.dumps(
            consolidated,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows = [
        flatten_result(result)
        for result in final_results
    ]

    fieldnames = list(
        rows[0].keys()
    )

    with FINAL_CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print("=" * 60)
    print("Final 63-Page Benchmark Consolidation")
    print("=" * 60)

    print(
        f"Approaches : {len(final_results)}"
    )

    print(
        f"JSON       : {FINAL_JSON_PATH}"
    )

    print(
        f"CSV        : {FINAL_CSV_PATH}"
    )

    print("\nIncluded:")

    for result in final_results:

        print(
            f"  - {result['display_name']}"
        )


if __name__ == "__main__":
    main()