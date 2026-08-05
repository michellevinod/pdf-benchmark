import json
from pathlib import Path

from benchmark.ground_truth_loader import GroundTruthLoader
from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.robustness_metrics import RobustnessMetrics
from benchmark.table_metrics import TableMetrics
from benchmark.text_metrics import TextMetrics


def main():

    normalized_path = Path(
        "outputs/docling/normalized_63pages_batched.json"
    )

    ground_truth_path = Path(
        "benchmark_dataset/ground_truth_63pages.json"
    )

    with normalized_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        normalized_document = json.load(file)

    ground_truth = GroundTruthLoader.load(
        ground_truth_path
    )

    reference_pages = (
        GroundTruthLoader.get_page_texts(
            ground_truth
        )
    )

    reference_tables = (
        GroundTruthLoader.get_reference_tables(
            ground_truth
        )
    )

    reference_images = (
        GroundTruthLoader.get_reference_images(
            ground_truth
        )
    )

    reference_layout = (
        GroundTruthLoader.get_reference_layout_blocks(
            ground_truth
        )
    )

    result = {
        "parser": "docling_batched",
        "status": "Success",
        "execution_mode": "10-page batches",
        "execution_time_seconds": (
            normalized_document
            .get("batching", {})
            .get("total_execution_time_seconds")
        ),
    }

    result.update(
        TextMetrics.evaluate(
            normalized_document,
            reference_pages,
        )
    )

    result.update(
        TableMetrics.evaluate(
            normalized_document,
            reference_tables,
            GroundTruthLoader.get_table_count(
                ground_truth
            ),
        )
    )

    result.update(
        ImageMetrics.evaluate(
            normalized_document,
            reference_images,
            GroundTruthLoader.get_image_count(
                ground_truth
            ),
        )
    )

    result.update(
        LayoutMetrics.evaluate(
            normalized_document,
            reference_layout,
            GroundTruthLoader.get_layout_count(
                ground_truth
            ),
        )
    )

    result.update(
        RobustnessMetrics.evaluate(
            normalized_document
        )
    )

    output_path = Path(
        "results/docling_batched_63pages_results.json"
    )

    output_path.write_text(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print("Batched Docling Evaluation")
    print("=" * 60)

    print(
        "\nTEXT\n",
        json.dumps(
            result.get("text_quality"),
            indent=2,
        ),
    )

    print(
        "\nTABLE\n",
        json.dumps(
            result.get("table_quality"),
            indent=2,
        ),
    )

    print(
        "\nIMAGE\n",
        json.dumps(
            result.get("image_quality"),
            indent=2,
        ),
    )

    print(
        "\nLAYOUT\n",
        json.dumps(
            result.get("layout_quality"),
            indent=2,
        ),
    )

    print(
        "\nSaved:",
        output_path,
    )


if __name__ == "__main__":
    main()