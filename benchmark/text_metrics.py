from typing import Any


class TextMetrics:
    """
    Evaluates text extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        page_count = len(pages)

        character_count = 0
        word_count = 0
        empty_pages = 0

        for page in pages:

            text = page.get(
                "text",
                "",
            ) or ""

            character_count += len(text)

            words = text.split()

            word_count += len(words)

            if not text.strip():
                empty_pages += 1

        average_words_per_page = (
            word_count / page_count
            if page_count
            else 0
        )

        return {
            "character_count": character_count,
            "word_count": word_count,
            "average_words_per_page": round(
                average_words_per_page,
                2,
            ),
            "empty_pages": empty_pages,
        }