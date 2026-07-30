from typing import Any


class ImageMetrics:
    """
    Evaluates image extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_image_count: int,
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        total_images = 0
        total_figures = 0
        pages_with_images = 0

        for page in pages:

            images = page.get(
                "images",
                [],
            )

            figures = page.get(
                "figures",
                [],
            )

            if images or figures:
                pages_with_images += 1

            total_images += len(images)
            total_figures += len(figures)

        page_count = len(pages)

        average_images_per_page = (
            total_images / page_count
            if page_count
            else 0
        )

        image_coverage = (
            (
                min(
                    total_images,
                    reference_image_count,
                )
                / reference_image_count
            )
            * 100
            if reference_image_count
            else 0
        )

        missing_images = max(
            0,
            reference_image_count - total_images,
        )

        extra_images = max(
            0,
            total_images - reference_image_count,
        )

        return {
            "image_statistics": {
                "image_count": total_images,
                "figure_count": total_figures,
                "pages_with_images": pages_with_images,
                "average_images_per_page": round(
                    average_images_per_page,
                    2,
                ),
            },
            "image_quality": {
                "image_coverage_percent": round(
                    image_coverage,
                    2,
                ),
                "missing_images": missing_images,
                "extra_images": extra_images,
            },
        }