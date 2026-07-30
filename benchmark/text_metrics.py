from jiwer import cer, wer


class TextMetrics:
    """
    Computes text extraction statistics and quality metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict,
        reference_pages: list[str],
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        extracted_pages = []

        character_count = 0
        word_count = 0
        line_count = 0
        empty_pages = 0

        for page in pages:

            text = page.get(
                "text",
                "",
            ).strip()

            extracted_pages.append(text)

            character_count += len(text)

            word_count += len(
                text.split()
            )

            line_count += len(
                text.splitlines()
            )

            if not text:
                empty_pages += 1

        page_count = len(pages)

        pages_with_text = (
            page_count - empty_pages
        )

        average_words_per_page = (
            word_count / page_count
            if page_count
            else 0
        )

        reference_text = "\n".join(
            reference_pages
        ).strip()

        extracted_text = "\n".join(
            extracted_pages
        ).strip()

        exact_match = (
            extracted_text == reference_text
        )

        character_error_rate = cer(
            reference_text,
            extracted_text,
        )

        word_error_rate = wer(
            reference_text,
            extracted_text,
        )

        reference_characters = len(
            reference_text
        )

        extracted_characters = len(
            extracted_text
        )

        text_coverage = (
            min(
                extracted_characters,
                reference_characters,
            )
            / reference_characters
            * 100
            if reference_characters
            else 0
        )

        return {
            "text_statistics": {
                "page_count": page_count,
                "pages_with_text": pages_with_text,
                "empty_pages": empty_pages,
                "character_count": character_count,
                "word_count": word_count,
                "line_count": line_count,
                "average_words_per_page": round(
                    average_words_per_page,
                    2,
                ),
            },
            "text_quality": {
                "exact_match": exact_match,
                "character_error_rate": round(
                    character_error_rate,
                    4,
                ),
                "word_error_rate": round(
                    word_error_rate,
                    4,
                ),
                "text_coverage_percent": round(
                    text_coverage,
                    2,
                ),
            },
        }