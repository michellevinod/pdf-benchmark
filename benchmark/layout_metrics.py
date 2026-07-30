from typing import Any


class LayoutMetrics:
    """
    Evaluates document layout extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_layout_count: int,
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        total_layout_blocks = 0
        pages_with_layout = 0
        ocr_pages = 0

        for page in pages:

            layout_blocks = page.get(
                "layout_blocks",
                [],
            )

            if layout_blocks:
                pages_with_layout += 1

            total_layout_blocks += len(
                layout_blocks,
            )

            ocr_text = page.get(
                "ocr_text",
                "",
            )

            if ocr_text.strip():
                ocr_pages += 1

        page_count = len(pages)

        average_layout_blocks_per_page = (
            total_layout_blocks / page_count
            if page_count
            else 0
        )

        layout_coverage = (
            (
                min(
                    total_layout_blocks,
                    reference_layout_count,
                )
                / reference_layout_count
            )
            * 100
            if reference_layout_count
            else 0
        )

        missing_layout_blocks = max(
            0,
            reference_layout_count
            - total_layout_blocks,
        )

        extra_layout_blocks = max(
            0,
            total_layout_blocks
            - reference_layout_count,
        )

        return {
            "layout_statistics": {
                "layout_block_count": total_layout_blocks,
                "pages_with_layout": pages_with_layout,
                "ocr_pages": ocr_pages,
                "average_layout_blocks_per_page": round(
                    average_layout_blocks_per_page,
                    2,
                ),
            },
            "layout_quality": {
                "layout_coverage_percent": round(
                    layout_coverage,
                    2,
                ),
                "missing_layout_blocks": (
                    missing_layout_blocks
                ),
                "extra_layout_blocks": (
                    extra_layout_blocks
                ),
            },
        }