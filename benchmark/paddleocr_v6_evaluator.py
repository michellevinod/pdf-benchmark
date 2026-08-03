import json
from pathlib import Path

from benchmark.ground_truth_loader import GroundTruthLoader
from benchmark.text_metrics import TextMetrics


class PaddleOCRV6Evaluator:
    """
    Evaluates cached PP-OCRv6 output against the same
    frozen ground truth used by the PDF parser benchmark.

    PP-OCRv6 is evaluated as an OCR-specific baseline.
    """

    def __init__(
        self,
        ground_truth_path: str = "benchmark_dataset/ground_truth.json",
        paddle_output_path: str = "outputs/paddleocr_v6/raw_results.json",
        result_path: str = "results/paddleocr_v6_results.json",
    ):
        self.ground_truth_path = Path(
            ground_truth_path
        )

        self.paddle_output_path = Path(
            paddle_output_path
        )

        self.result_path = Path(
            result_path
        )

        self.result_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load_paddle_output(
        self,
    ) -> dict:

        if not self.paddle_output_path.exists():
            raise FileNotFoundError(
                "PP-OCRv6 cached output not found: "
                f"{self.paddle_output_path}"
            )

        with self.paddle_output_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = json.load(
                file
            )

        pages = document.get(
            "pages",
            [],
        )

        if not isinstance(
            pages,
            list,
        ):
            raise ValueError(
                "PP-OCRv6 pages must be a list."
            )

        return document

    @staticmethod
    def _build_normalized_document(
        paddle_document: dict,
    ) -> dict:
        """
        Converts cached PP-OCRv6 output into the minimal
        normalized format expected by TextMetrics.
        """

        normalized_pages = []

        paddle_pages = paddle_document.get(
            "pages",
            [],
        )

        paddle_pages = sorted(
            paddle_pages,
            key=lambda page: page.get(
                "page_number",
                0,
            ),
        )

        for page in paddle_pages:

            if page.get(
                "status"
            ) == "Success":

                text = str(
                    page.get(
                        "text",
                        "",
                    )
                )

            else:
                text = ""

            normalized_pages.append(
                {
                    "page_number": page.get(
                        "page_number"
                    ),
                    "text": text,
                }
            )

        return {
            "pages": normalized_pages
        }

    @staticmethod
    def _calculate_ocr_statistics(
        paddle_document: dict,
    ) -> dict:

        pages = paddle_document.get(
            "pages",
            [],
        )

        successful_pages = [
            page
            for page in pages
            if page.get(
                "status"
            ) == "Success"
        ]

        failed_pages = [
            page
            for page in pages
            if page.get(
                "status"
            ) != "Success"
        ]

        total_regions = sum(
            int(
                page.get(
                    "text_line_count",
                    0,
                )
            )
            for page in successful_pages
        )

        all_scores = []

        for page in successful_pages:

            for score in page.get(
                "rec_scores",
                [],
            ):

                try:
                    all_scores.append(
                        float(score)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        average_confidence = (
            sum(all_scores)
            / len(all_scores)
            if all_scores
            else 0.0
        )

        minimum_confidence = (
            min(all_scores)
            if all_scores
            else 0.0
        )

        maximum_confidence = (
            max(all_scores)
            if all_scores
            else 0.0
        )

        pages_with_text_regions = sum(
            1
            for page in successful_pages
            if int(
                page.get(
                    "text_line_count",
                    0,
                )
            ) > 0
        )

        return {
            "successful_pages": len(
                successful_pages
            ),
            "failed_pages": len(
                failed_pages
            ),
            "detected_text_regions": (
                total_regions
            ),
            "pages_with_text_regions": (
                pages_with_text_regions
            ),
            "average_ocr_confidence": round(
                average_confidence,
                4,
            ),
            "minimum_ocr_confidence": round(
                minimum_confidence,
                4,
            ),
            "maximum_ocr_confidence": round(
                maximum_confidence,
                4,
            ),
        }

    @staticmethod
    def _get_performance_metrics(
        paddle_document: dict,
    ) -> dict:

        summary = paddle_document.get(
            "summary",
            {},
        )

        return {
            "execution_time_seconds": (
                summary.get(
                    "total_ocr_execution_time_seconds",
                    0,
                )
            ),
            "average_page_time_seconds": (
                summary.get(
                    "average_page_time_seconds",
                    0,
                )
            ),
            "throughput_pages_per_second": (
                summary.get(
                    "throughput_pages_per_second",
                    0,
                )
            ),
            "wall_time_seconds": (
                summary.get(
                    "wall_time_this_run_seconds",
                    0,
                )
            ),
        }

    def evaluate(
        self,
    ) -> dict:

        print("=" * 60)
        print("PP-OCRv6 Cached Evaluation Started")
        print("=" * 60)

        # -------------------------------------------------
        # Ground truth
        # -------------------------------------------------

        ground_truth = (
            GroundTruthLoader.load(
                self.ground_truth_path
            )
        )

        reference_pages = (
            GroundTruthLoader.get_page_texts(
                ground_truth
            )
        )

        # -------------------------------------------------
        # Cached Paddle output
        # -------------------------------------------------

        paddle_document = (
            self._load_paddle_output()
        )

        normalized_document = (
            self._build_normalized_document(
                paddle_document
            )
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        paddle_pages = (
            normalized_document.get(
                "pages",
                [],
            )
        )

        if len(
            paddle_pages
        ) != len(
            reference_pages
        ):
            raise ValueError(
                "PP-OCRv6 page count does not match "
                "ground truth: "
                f"{len(paddle_pages)} vs "
                f"{len(reference_pages)}"
            )

        page_numbers = [
            page.get(
                "page_number"
            )
            for page in paddle_pages
        ]

        expected_page_numbers = list(
            range(
                1,
                len(reference_pages) + 1,
            )
        )

        if (
            page_numbers
            != expected_page_numbers
        ):
            raise ValueError(
                "PP-OCRv6 page numbering does not "
                "match the ground truth."
            )

        # -------------------------------------------------
        # Same text metrics used by all PDF parsers
        # -------------------------------------------------

        text_metrics = (
            TextMetrics.evaluate(
                normalized_document,
                reference_pages,
            )
        )

        # -------------------------------------------------
        # OCR-specific statistics
        # -------------------------------------------------

        ocr_statistics = (
            self._calculate_ocr_statistics(
                paddle_document
            )
        )

        # -------------------------------------------------
        # Performance
        # -------------------------------------------------

        performance = (
            self._get_performance_metrics(
                paddle_document
            )
        )

        # -------------------------------------------------
        # Final result
        # -------------------------------------------------

        result = {
            "parser": "paddleocr_v6_tiny",
            "type": "ocr_baseline",

            "model": {
                "ocr_version": (
                    paddle_document.get(
                        "ocr_version",
                        "PP-OCRv6",
                    )
                ),
                "detection_model": (
                    paddle_document.get(
                        "detection_model",
                        "PP-OCRv6_tiny_det",
                    )
                ),
                "recognition_model": (
                    paddle_document.get(
                        "recognition_model",
                        "PP-OCRv6_tiny_rec",
                    )
                ),
                "render_scale": (
                    paddle_document.get(
                        "render_scale",
                        1.5,
                    )
                ),
            },

            **text_metrics,

            "ocr_statistics": (
                ocr_statistics
            ),

            "performance": (
                performance
            ),

            "unsupported_metrics": {
                "table_teds": (
                    "N/A - OCR baseline"
                ),
                "image_metrics": (
                    "N/A - OCR baseline"
                ),
                "document_layout_metrics": (
                    "N/A - OCR baseline"
                ),
            },
        }

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        with self.result_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print()
        print("PP-OCRv6 evaluation completed.")
        print(
            f"Results saved: {self.result_path}"
        )

        print()
        print("-" * 60)

        print(
            "CER  : "
            f"{result['text_quality']['character_error_rate']}"
        )

        print(
            "WER  : "
            f"{result['text_quality']['word_error_rate']}"
        )

        print(
            "Edit : "
            f"{result['text_quality']['normalized_edit_similarity']}"
        )

        print(
            "Coverage : "
            f"{result['text_quality']['text_coverage_percent']}%"
        )

        print(
            "OCR confidence : "
            f"{ocr_statistics['average_ocr_confidence']}"
        )

        print(
            "Text regions : "
            f"{ocr_statistics['detected_text_regions']}"
        )

        return result


if __name__ == "__main__":

    evaluator = (
        PaddleOCRV6Evaluator()
    )

    evaluator.evaluate()