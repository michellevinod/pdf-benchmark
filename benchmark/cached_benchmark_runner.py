import json
from pathlib import Path

from benchmark.ground_truth_loader import GroundTruthLoader
from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.report_generator import ReportGenerator
from benchmark.robustness_metrics import RobustnessMetrics
from benchmark.table_metrics import TableMetrics
from benchmark.text_metrics import TextMetrics
from normalization.normalizer_factory import NormalizerFactory
from validation.schema_validator import SchemaValidator


class CachedBenchmarkRunner:
    """
    Evaluates existing parser outputs without rerunning
    the expensive PDF parsers.

    Workflow:
        output.json
        -> normalization
        -> schema validation
        -> normalized.json
        -> evaluation against frozen ground truth
        -> JSON / CSV reports
    """

    def __init__(
        self,
        pdf_path: str,
    ):
        self.pdf_path = pdf_path

        self.parsers = [
            "docling",
            "liteparse",
            "pymupdf4llm",
        ]

    def run(self):

        print("=" * 60)
        print("Cached PDF Benchmark Started")
        print("=" * 60)

        benchmark_results = []

        # -------------------------------------------------
        # Load frozen JSON ground truth ONCE
        # -------------------------------------------------

        ground_truth_path = Path(
            "benchmark_dataset/ground_truth_63pages.json"
        )

        ground_truth_document = GroundTruthLoader.load(
            ground_truth_path
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
        # Evaluate each cached parser output
        # -------------------------------------------------

        for parser_name in self.parsers:

            print(
                f"\nEvaluating cached {parser_name}..."
            )

            output_dir = (
                Path("outputs")
                / parser_name
            )

            json_path = (
                output_dir
                / "output.json"
            )

            normalized_path = (
                output_dir
                / "normalized.json"
            )

            if not json_path.exists():

                result = {
                    "parser": parser_name,
                    "status": "Failed",
                    "error": (
                        f"Cached parser output not found: "
                        f"{json_path}"
                    ),
                }

                benchmark_results.append(
                    result
                )

                print(
                    f"{parser_name}: Failed"
                )

                continue

            try:

                # -----------------------------------------
                # Load existing raw parser output
                # -----------------------------------------

                with json_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    raw_json = json.load(
                        file
                    )

                # -----------------------------------------
                # Re-run normalization only
                # -----------------------------------------

                normalizer = (
                    NormalizerFactory.get_normalizer(
                        parser_name
                    )
                )

                normalized_document = (
                    normalizer.normalize(
                        raw_json
                    )
                )

                # -----------------------------------------
                # Validate normalized schema
                # -----------------------------------------

                SchemaValidator.validate(
                    normalized_document
                )

                # -----------------------------------------
                # Save refreshed normalized output
                # -----------------------------------------

                normalized_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                normalized_path.write_text(
                    json.dumps(
                        normalized_document,
                        indent=4,
                        ensure_ascii=False,
                        default=str,
                    ),
                    encoding="utf-8",
                )

                result = {
                    "parser": parser_name,
                    "status": "Success",
                }

                # -----------------------------------------
                # TEXT
                # -----------------------------------------

                result.update(
                    TextMetrics.evaluate(
                        normalized_document,
                        reference_pages,
                    )
                )

                # -----------------------------------------
                # TABLES + TEDS
                # -----------------------------------------

                result.update(
                    TableMetrics.evaluate(
                        normalized_document,
                        reference_tables,
                        reference_table_count,
                    )
                )

                # -----------------------------------------
                # IMAGES
                # -----------------------------------------

                result.update(
                    ImageMetrics.evaluate(
                        normalized_document,
                        reference_images,
                        reference_image_count,
                    )
                )

                # -----------------------------------------
                # LAYOUT
                # -----------------------------------------

                result.update(
                    LayoutMetrics.evaluate(
                        normalized_document,
                        reference_layout_blocks,
                        reference_layout_count,
                    )
                )

                # -----------------------------------------
                # ROBUSTNESS
                # -----------------------------------------

                result.update(
                    RobustnessMetrics.evaluate(
                        normalized_document,
                    )
                )

                benchmark_results.append(
                    result
                )

                print(
                    f"{parser_name}: Success"
                )

            except Exception as exc:

                result = {
                    "parser": parser_name,
                    "status": "Failed",
                    "error": str(exc),
                }

                benchmark_results.append(
                    result
                )

                print(
                    f"{parser_name}: Failed"
                )

                print(
                    f"Error: {exc}"
                )

        # -------------------------------------------------
        # Save cached reports
        # -------------------------------------------------

        Path("results").mkdir(
            parents=True,
            exist_ok=True,
        )

        ReportGenerator.save_json(
            benchmark_results,
            "results/cached_benchmark_results.json",
        )

        ReportGenerator.save_csv(
            benchmark_results,
            "results/cached_benchmark_results.csv",
        )

        # -------------------------------------------------
        # Console summary
        # -------------------------------------------------

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Cached Benchmark Completed"
        )

        print(
            "=" * 60
        )

        for result in benchmark_results:

            print(
                "\n"
                + "-"
                * 60
            )

            print(
                f"Parser : {result['parser']}"
            )

            print(
                f"Status : {result['status']}"
            )

            if result["status"] != "Success":

                print(
                    f"Error  : {result.get('error')}"
                )

                continue

            table_quality = result.get(
                "table_quality",
                {},
            )

            layout_statistics = result.get(
                "layout_statistics",
                {},
            )

            print(
                "Tables : "
                f"{table_quality.get('extracted_table_count', 'N/A')}"
            )

            print(
                "TEDS   : "
                f"{table_quality.get('teds_score', 'N/A')}"
            )

            print(
                "Layout : "
                f"{layout_statistics.get('layout_block_count', 'N/A')}"
            )


if __name__ == "__main__":

    runner = CachedBenchmarkRunner(
        pdf_path=(
            "benchmark_dataset/"
            "PDF_Benchmarking_Tester.pdf"
        ),
    )

    runner.run()