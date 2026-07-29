from normalization.base_normalizer import BaseNormalizer


class PyMuPDF4LLMNormalizer(BaseNormalizer):
    """
    Converts PyMuPDF4LLM's raw JSON into the common normalized schema.
    """

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        markdown = raw_json.get(
            "markdown",
            "",
        )

        return {
            "parser": raw_json.get(
                "parser",
                "pymupdf4llm",
            ),
            "source_pdf": raw_json.get(
                "source_pdf",
                "",
            ),
            "metadata": {},
            "pages": [
                {
                    "page_number": None,
                    "text": markdown,
                    "markdown": markdown,
                    "tables": [],
                    "images": [],
                    "figures": [],
                    "layout_blocks": [],
                    "ocr_text": "",
                    "metadata": {},
                }
            ],
            "statistics": {
                "page_count": None,
                "table_count": 0,
                "image_count": 0,
            },
        }