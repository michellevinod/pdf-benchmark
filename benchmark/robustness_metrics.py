from typing import Any


class RobustnessMetrics:
    """
    Evaluates parser robustness metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
    ) -> dict:

        metadata = normalized_document.get(
            "metadata",
            {},
        )

        pages = normalized_document.get(
            "pages",
            [],
        )

        statistics = normalized_document.get(
            "statistics",
            {},
        )

        page_count = len(pages)

        pages_with_text = 0
        pages_without_text = 0
        pages_with_metadata = 0

        for page in pages:

            text = page.get(
                "text",
                "",
            )

            if text.strip():
                pages_with_text += 1
            else:
                pages_without_text += 1

            if page.get(
                "metadata",
                {},
            ):
                pages_with_metadata += 1

        return {
            "document_has_metadata": bool(metadata),
            "document_has_statistics": bool(statistics),
            "document_has_pages": page_count > 0,
            "pages_with_text": pages_with_text,
            "pages_without_text": pages_without_text,
            "pages_with_metadata": pages_with_metadata,
        }