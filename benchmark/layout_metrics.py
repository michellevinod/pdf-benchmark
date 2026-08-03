from typing import Any


class LayoutMetrics:
    """
    Evaluates document layout extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_layout_blocks: list[list[dict[str, Any]]] | None = None,
        reference_layout_count: int | None = None,
    ) -> dict:

        pages = normalized_document.get("pages", [])
        extracted_layout_by_page = [page.get("layout_blocks", []) for page in pages]
        total_layout_blocks = sum(len(page_blocks) for page_blocks in extracted_layout_by_page)
        pages_with_layout = sum(1 for page_blocks in extracted_layout_by_page if page_blocks)
        ocr_pages = sum(1 for page in pages if str(page.get("ocr_text", "")).strip())

        page_count = len(pages)
        average_layout_blocks_per_page = total_layout_blocks / page_count if page_count else 0.0

        if reference_layout_blocks is not None:
            reference_layout_count = sum(len(page_blocks) for page_blocks in reference_layout_blocks)
        if reference_layout_count is None:
            reference_layout_count = 0

        layout_coverage = (
            (min(total_layout_blocks, reference_layout_count) / reference_layout_count) * 100
            if reference_layout_count
            else 0.0
        )
        layout_coverage = min(100.0, max(0.0, layout_coverage))

        missing_layout_blocks = max(0, reference_layout_count - total_layout_blocks)
        extra_layout_blocks = max(0, total_layout_blocks - reference_layout_count)

        reading_order_accuracy = "N/A/Unsupported"
        if reference_layout_blocks is not None and extracted_layout_by_page:
            has_ordered_ref = any(isinstance(page_blocks, list) and page_blocks and isinstance(page_blocks[0], dict) and "reading_order" in page_blocks[0] for page_blocks in reference_layout_blocks)
            has_ordered_extracted = any(isinstance(page_blocks, list) and page_blocks and isinstance(page_blocks[0], dict) and "reading_order" in page_blocks[0] for page_blocks in extracted_layout_by_page)
            if has_ordered_ref and has_ordered_extracted:
                reading_order_accuracy = "N/A/Unsupported"

        return {
            "layout_statistics": {
                "layout_block_count": total_layout_blocks,
                "pages_with_layout": pages_with_layout,
                "ocr_pages": ocr_pages,
                "average_layout_blocks_per_page": round(average_layout_blocks_per_page, 2),
            },
            "layout_quality": {
                "reference_block_count": reference_layout_count,
                "extracted_block_count": total_layout_blocks,
                "missing_layout_blocks": missing_layout_blocks,
                "extra_layout_blocks": extra_layout_blocks,
                "layout_coverage_percent": round(layout_coverage, 2),
                "spatial_block_matching": "N/A/Unsupported",
                "reading_order_accuracy": reading_order_accuracy,
            },
        }