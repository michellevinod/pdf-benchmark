import json
from pathlib import Path

from benchmark.ground_truth_loader import GroundTruthLoader
from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.robustness_metrics import RobustnessMetrics
from benchmark.table_metrics import TableMetrics
from benchmark.text_metrics import TextMetrics
from validation.schema_validator import SchemaValidator


GROUND_TRUTH_PATH = Path(
    "benchmark_dataset/ground_truth_63pages.json"
)

NORMALIZED_PATH = Path(
    "outputs/hybrid/normalized.json"
)

RESULT_PATH = Path(
    "results/hybrid_results.json"
)


def main():

    print("=" * 60)
    print("Hybrid Approach Evaluation")
    print("=" * 60)

    # -------------------------------------------------
    # Load 63-page ground truth
    # -------------------------------------------------

    ground_truth_document = GroundTruthLoader.load(
        GROUND_TRUTH_PATH
    )

    reference_pages = (
        GroundTruthLoader.get_page_texts(
            ground_truth_document
        )
    )

    reference_tables = (
        GroundTruthLoader.get_reference_tables(
            ground_truth_document
        )
    )

    reference_images = (
        GroundTruthLoader.get_reference_images(
            ground_truth_document
        )
    )

    reference_layout_blocks = (
        GroundTruthLoader.get_reference_layout_blocks(
            ground_truth_document
        )
    )

    reference_table_count = (
        GroundTruthLoader.get_table_count(
            ground_truth_document
        )
    )

    reference_image_count = (
        GroundTruthLoader.get_image_count(
            ground_truth_document
        )
    )

    reference_layout_count = (
        GroundTruthLoader.get_layout_count(
            ground_truth_document
        )
    )

    # -------------------------------------------------
    # Load Hybrid normalized output
    # -------------------------------------------------

    if not NORMALIZED_PATH.exists():
        raise FileNotFoundError(
            f"Hybrid normalized output not found: "
            f"{NORMALIZED_PATH}"
        )

    with NORMALIZED_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        normalized_document = json.load(
            file
        )

    # -------------------------------------------------
    # Validate common schema
    # -------------------------------------------------

    SchemaValidator.validate(
        normalized_document
    )

    result = {
        "parser": "hybrid",
        "display_name": "Hybrid Approach",
        "status": "Success",
        "evaluation_corpus_pages": 63,
        "ground_truth": str(
            GROUND_TRUTH_PATH
        ),
    }

    # -------------------------------------------------
    # TEXT
    # -------------------------------------------------

    result.update(
        TextMetrics.evaluate(
            normalized_document,
            reference_pages,
        )
    )

    # -------------------------------------------------
    # TABLES + TEDS
    # -------------------------------------------------

    result.update(
        TableMetrics.evaluate(
            normalized_document,
            reference_tables,
            reference_table_count,
        )
    )

    # -------------------------------------------------
    # IMAGES
    # -------------------------------------------------

    result.update(
        ImageMetrics.evaluate(
            normalized_document,
            reference_images,
            reference_image_count,
        )
    )

    # -------------------------------------------------
    # LAYOUT
    # -------------------------------------------------

    result.update(
        LayoutMetrics.evaluate(
            normalized_document,
            reference_layout_blocks,
            reference_layout_count,
        )
    )

    # -------------------------------------------------
    # ROBUSTNESS
    # -------------------------------------------------

    result.update(
        RobustnessMetrics.evaluate(
            normalized_document,
        )
    )

    # -------------------------------------------------
    # Save result
    # -------------------------------------------------

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULT_PATH.write_text(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    # -------------------------------------------------
    # Console summary
    # -------------------------------------------------

    print("\nEvaluation completed successfully.")

    text_quality = result.get(
        "text_quality",
        {}
    )

    table_quality = result.get(
        "table_quality",
        {}
    )

    image_quality = result.get(
        "image_quality",
        {}
    )

    layout_quality = result.get(
        "layout_quality",
        {}
    )

    print("\nTEXT")
    print(
        "CER      :",
        text_quality.get(
            "character_error_rate"
        ),
    )
    print(
        "WER      :",
        text_quality.get(
            "word_error_rate"
        ),
    )
    print(
        "Similarity:",
        text_quality.get(
            "normalized_edit_similarity"
        ),
    )
    print(
        "Coverage :",
        text_quality.get(
            "text_coverage_percent"
        ),
    )

    print("\nTABLE")
    print(
        "Reference:",
        table_quality.get(
            "reference_table_count"
        ),
    )
    print(
        "Extracted:",
        table_quality.get(
            "extracted_table_count"
        ),
    )
    print(
        "F1       :",
        table_quality.get(
            "table_f1_score"
        ),
    )
    print(
        "TEDS     :",
        table_quality.get(
            "teds_score"
        ),
    )

    print("\nIMAGE")
    print(
        "F1       :",
        image_quality.get(
            "image_f1_score"
        ),
    )

    print("\nLAYOUT")
    print(
        "F1       :",
        layout_quality.get(
            "layout_f1_score"
        ),
    )

    print(
        "\nSaved:",
        RESULT_PATH,
    )


if __name__ == "__main__":
    main()