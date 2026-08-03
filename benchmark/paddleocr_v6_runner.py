import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import fitz
from paddleocr import PaddleOCR


class PaddleOCRV6Runner:
    """
    Runs PP-OCRv6-tiny on the benchmark PDF.

    The OCR model is initialized only once and each page result
    is cached immediately so completed pages are not lost if
    processing is interrupted.
    """

    def __init__(
        self,
        pdf_path: str,
        output_path: str = "outputs/paddleocr_v6/raw_results.json",
        render_scale: float = 1.5,
    ):
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path)
        self.render_scale = render_scale

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print("Initializing PP-OCRv6-tiny...")

        self.ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv6_tiny_det",
            text_recognition_model_name="PP-OCRv6_tiny_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

        print("PP-OCRv6-tiny initialized.")

    @staticmethod
    def _to_serializable(
        value: Any,
    ) -> Any:
        """
        Converts NumPy/Paddle result objects into values
        that can safely be written to JSON.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        if isinstance(value, dict):
            return {
                str(key): PaddleOCRV6Runner._to_serializable(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
            ),
        ):
            return [
                PaddleOCRV6Runner._to_serializable(
                    item
                )
                for item in value
            ]

        if hasattr(value, "tolist"):
            try:
                return value.tolist()
            except Exception:
                pass

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        return str(value)

    def _save(
        self,
        data: dict,
    ) -> None:

        with open(
            self.output_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def _load_existing(
        self,
    ) -> dict:

        if not self.output_path.exists():
            return {
                "engine": "PaddleOCR",
                "ocr_version": "PP-OCRv6",
                "detection_model": "PP-OCRv6_tiny_det",
                "recognition_model": "PP-OCRv6_tiny_rec",
                "render_scale": self.render_scale,
                "pages": [],
            }

        try:

            with open(
                self.output_path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

            if not isinstance(
                data.get("pages"),
                list,
            ):
                data["pages"] = []

            return data

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return {
                "engine": "PaddleOCR",
                "ocr_version": "PP-OCRv6",
                "detection_model": "PP-OCRv6_tiny_det",
                "recognition_model": "PP-OCRv6_tiny_rec",
                "render_scale": self.render_scale,
                "pages": [],
            }

    def run(
        self,
    ) -> None:

        print("=" * 60)
        print("PP-OCRv6-tiny Benchmark Started")
        print("=" * 60)

        document = fitz.open(
            self.pdf_path
        )

        total_pages = len(
            document
        )

        data = self._load_existing()

        completed_pages = {
            page.get("page_number")
            for page in data["pages"]
            if page.get("status") == "Success"
        }

        if completed_pages:

            print(
                f"Found {len(completed_pages)} "
                "previously completed pages."
            )

        run_start = time.perf_counter()

        pages_processed_this_run = 0

        for page_index in range(
            total_pages
        ):

            page_number = (
                page_index + 1
            )

            if (
                page_number
                in completed_pages
            ):

                print(
                    f"[{page_number}/{total_pages}] "
                    "Already cached - skipping."
                )

                continue

            print(
                f"[{page_number}/{total_pages}] "
                "Running OCR..."
            )

            page_start = (
                time.perf_counter()
            )

            try:

                page = document[
                    page_index
                ]

                # Render the PDF page in memory.
                # No temporary PNG file is required.

                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(
                        self.render_scale,
                        self.render_scale,
                    ),
                    alpha=False,
                )

                image_array = np.frombuffer(
                    pixmap.samples,
                    dtype=np.uint8,
                ).reshape(
                    pixmap.height,
                    pixmap.width,
                    pixmap.n,
                )

                prediction = list(
                    self.ocr.predict(
                        image_array
                    )
                )

                if prediction:

                    result = prediction[0]

                    result_dict = (
                        dict(result)
                        if hasattr(
                            result,
                            "keys",
                        )
                        else {}
                    )

                    rec_texts = (
                        result_dict.get(
                            "rec_texts",
                            [],
                        )
                    )

                    rec_scores = (
                        result_dict.get(
                            "rec_scores",
                            [],
                        )
                    )

                    dt_polys = (
                        result_dict.get(
                            "dt_polys",
                            [],
                        )
                    )

                    rec_polys = (
                        result_dict.get(
                            "rec_polys",
                            [],
                        )
                    )

                    rec_boxes = (
                        result_dict.get(
                            "rec_boxes",
                            [],
                        )
                    )

                else:

                    rec_texts = []
                    rec_scores = []
                    dt_polys = []
                    rec_polys = []
                    rec_boxes = []

                rec_texts = (
                    self._to_serializable(
                        rec_texts
                    )
                )

                rec_scores = (
                    self._to_serializable(
                        rec_scores
                    )
                )

                dt_polys = (
                    self._to_serializable(
                        dt_polys
                    )
                )

                rec_polys = (
                    self._to_serializable(
                        rec_polys
                    )
                )

                rec_boxes = (
                    self._to_serializable(
                        rec_boxes
                    )
                )

                # Join recognized text in reading sequence.

                page_text = "\n".join(
                    str(text)
                    for text in rec_texts
                    if str(text).strip()
                )

                numeric_scores = []

                for score in rec_scores:

                    try:
                        numeric_scores.append(
                            float(score)
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        pass

                average_confidence = (
                    sum(numeric_scores)
                    / len(numeric_scores)
                    if numeric_scores
                    else 0.0
                )

                page_time = (
                    time.perf_counter()
                    - page_start
                )

                page_result = {
                    "page_number": page_number,
                    "status": "Success",

                    # Original PDF dimensions
                    "pdf_width": float(
                        page.rect.width
                    ),
                    "pdf_height": float(
                        page.rect.height
                    ),

                    # Rendered image dimensions
                    "render_width": (
                        pixmap.width
                    ),
                    "render_height": (
                        pixmap.height
                    ),

                    "render_scale": (
                        self.render_scale
                    ),

                    "text": page_text,

                    "text_line_count": len(
                        rec_texts
                    ),

                    "average_confidence": round(
                        average_confidence,
                        6,
                    ),

                    "rec_texts": (
                        rec_texts
                    ),

                    "rec_scores": (
                        rec_scores
                    ),

                    "dt_polys": (
                        dt_polys
                    ),

                    "rec_polys": (
                        rec_polys
                    ),

                    "rec_boxes": (
                        rec_boxes
                    ),

                    "execution_time_seconds": round(
                        page_time,
                        4,
                    ),
                }

                print(
                    f"    Success | "
                    f"{len(rec_texts)} text regions | "
                    f"{page_time:.2f} sec"
                )

            except Exception as error:

                page_time = (
                    time.perf_counter()
                    - page_start
                )

                page_result = {
                    "page_number": (
                        page_number
                    ),
                    "status": "Failed",
                    "error": str(
                        error
                    ),
                    "execution_time_seconds": round(
                        page_time,
                        4,
                    ),
                }

                print(
                    f"    FAILED: {error}"
                )

            # Remove an older failed/cached copy
            # of this page if present.

            data["pages"] = [
                existing
                for existing
                in data["pages"]
                if existing.get(
                    "page_number"
                ) != page_number
            ]

            data["pages"].append(
                page_result
            )

            data["pages"].sort(
                key=lambda item: (
                    item.get(
                        "page_number",
                        0,
                    )
                )
            )

            pages_processed_this_run += 1

            # Save after EVERY page.

            self._save(
                data
            )

        document.close()

        run_time = (
            time.perf_counter()
            - run_start
        )

        successful_pages = [
            page
            for page in data["pages"]
            if page.get(
                "status"
            ) == "Success"
        ]

        failed_pages = [
            page
            for page in data["pages"]
            if page.get(
                "status"
            ) != "Success"
        ]

        total_ocr_time = sum(
            float(
                page.get(
                    "execution_time_seconds",
                    0,
                )
            )
            for page in successful_pages
        )

        total_text_regions = sum(
            int(
                page.get(
                    "text_line_count",
                    0,
                )
            )
            for page in successful_pages
        )

        average_page_time = (
            total_ocr_time
            / len(successful_pages)
            if successful_pages
            else 0.0
        )

        throughput = (
            len(successful_pages)
            / total_ocr_time
            if total_ocr_time > 0
            else 0.0
        )

        data["summary"] = {
            "total_pdf_pages": (
                total_pages
            ),
            "successful_pages": len(
                successful_pages
            ),
            "failed_pages": len(
                failed_pages
            ),
            "total_text_regions": (
                total_text_regions
            ),
            "total_ocr_execution_time_seconds": round(
                total_ocr_time,
                4,
            ),
            "average_page_time_seconds": round(
                average_page_time,
                4,
            ),
            "throughput_pages_per_second": round(
                throughput,
                4,
            ),
            "pages_processed_this_run": (
                pages_processed_this_run
            ),
            "wall_time_this_run_seconds": round(
                run_time,
                4,
            ),
        }

        self._save(
            data
        )

        print()
        print("=" * 60)
        print("PP-OCRv6-tiny Benchmark Completed")
        print("=" * 60)

        print(
            f"Successful pages : "
            f"{len(successful_pages)}/{total_pages}"
        )

        print(
            f"Failed pages     : "
            f"{len(failed_pages)}"
        )

        print(
            f"Text regions     : "
            f"{total_text_regions}"
        )

        print(
            f"Avg page time    : "
            f"{average_page_time:.2f} sec"
        )

        print(
            f"Throughput       : "
            f"{throughput:.3f} pages/sec"
        )

        print(
            f"Cached output    : "
            f"{self.output_path}"
        )


if __name__ == "__main__":

    runner = PaddleOCRV6Runner(
        pdf_path=(
            "benchmark_dataset/"
            "PDF_Benchmarking_Tester.pdf"
        ),
    )

    runner.run()