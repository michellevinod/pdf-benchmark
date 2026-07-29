from typing import Any


class ImageMetrics:
    """
    Evaluates image extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
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

        return {
            "image_count": total_images,
            "figure_count": total_figures,
            "pages_with_images": pages_with_images,
            "average_images_per_page": round(
                average_images_per_page,
                2,
            ),
        }