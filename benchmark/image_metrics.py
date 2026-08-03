from typing import Any


class ImageMetrics:
    """
    Evaluates image extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_images: list[list[dict[str, Any]]] | None = None,
        reference_image_count: int | None = None,
    ) -> dict:

        pages = normalized_document.get("pages", [])

        extracted_images_by_page = [page.get("images", []) for page in pages]
        total_images = sum(len(page_images) for page_images in extracted_images_by_page)
        total_figures = sum(len(page.get("figures", [])) for page in pages)
        pages_with_images = sum(1 for page_images in extracted_images_by_page if page_images)

        page_count = len(pages)
        average_images_per_page = total_images / page_count if page_count else 0.0

        if reference_images is not None:
            reference_image_count = sum(len(page_images) for page_images in reference_images)
        if reference_image_count is None:
            reference_image_count = 0

        image_coverage = (
            (min(total_images, reference_image_count) / reference_image_count) * 100
            if reference_image_count
            else 0.0
        )
        image_coverage = min(100.0, max(0.0, image_coverage))

        missing_images = max(0, reference_image_count - total_images)
        extra_images = max(0, total_images - reference_image_count)

        return {
            "image_statistics": {
                "extracted_image_count": total_images,
                "figure_count": total_figures,
                "pages_with_images": pages_with_images,
                "average_images_per_page": round(average_images_per_page, 2),
            },
            "image_quality": {
                "reference_image_count": reference_image_count,
                "extracted_image_count": total_images,
                "missing_images": missing_images,
                "extra_images": extra_images,
                "image_coverage_percent": round(image_coverage, 2),
                "structural_image_match": "N/A/Unsupported",
            },
        }