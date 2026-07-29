from normalization.base_normalizer import BaseNormalizer


class LiteParseNormalizer(BaseNormalizer):
    """
    Converts LiteParse's raw JSON into the common normalized schema.
    """

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        pages = raw_json.get("pages", [])

        normalized = {
            "parser": raw_json.get("parser", "liteparse"),
            "source_pdf": raw_json.get("source_pdf", ""),
            "metadata": {
                "producer": raw_json.get("producer"),
                "creator": raw_json.get("creator"),
                "form_type": raw_json.get("form_type"),
            },
            "pages": [],
            "statistics": {
                "page_count": len(pages),
                "table_count": 0,
                "image_count": raw_json.get(
                    "image_count",
                    0,
                ),
            },
        }

        for page in pages:

            normalized["pages"].append(
                {
                    "page_number": page.get("page_number"),

                    "text": page.get(
                        "text",
                        "",
                    ),

                    "markdown": page.get(
                        "markdown",
                        "",
                    ),

                    "tables": [],

                    "images": [],

                    "figures": [],

                    "layout_blocks": [],

                    "ocr_text": "",

                    "metadata": {
                        "width": page.get("width"),
                        "height": page.get("height"),
                        "text_items": page.get(
                            "text_items",
                            [],
                        ),
                        "annotations": page.get(
                            "annotations",
                            [],
                        ),
                        "form_fields": page.get(
                            "form_fields",
                            [],
                        ),
                        "vector_graphics": page.get(
                            "vector_graphics",
                            [],
                        ),
                        "content_bounds": page.get(
                            "content_bounds",
                        ),
                        "structure_tree": page.get(
                            "structure_tree",
                        ),
                        "complexity": page.get(
                            "complexity",
                        ),
                    },
                }
            )

        return normalized