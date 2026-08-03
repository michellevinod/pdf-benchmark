from normalization.base_normalizer import BaseNormalizer


class PyMuPDF4LLMNormalizer(BaseNormalizer):
    """
    Converts PyMuPDF4LLM's raw JSON into the common normalized schema.
    """

    @staticmethod
    def _to_bbox(value):
        if isinstance(value, dict):
            left = value.get("l", value.get("x", 0.0))
            top = value.get("t", value.get("y", 0.0))
            right = value.get("r", value.get("x1", left))
            bottom = value.get("b", value.get("y1", top))
            return {"l": float(left), "t": float(top), "r": float(right), "b": float(bottom)}
        if isinstance(value, (list, tuple)) and len(value) >= 4:
            left, top, right, bottom = value[:4]
            return {"l": float(left), "t": float(top), "r": float(right), "b": float(bottom)}
        return {"l": 0.0, "t": 0.0, "r": 0.0, "b": 0.0}

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        raw_pages = raw_json.get(
            "pages",
            [],
        )

        if not raw_pages:
            markdown = raw_json.get(
                "markdown",
                "",
            )
            raw_pages = [
                {
                    "page_number": 1,
                    "text": markdown,
                    "markdown": markdown,
                    "metadata": {},
                }
            ]

        normalized_pages = []

        for index, raw_page in enumerate(raw_pages):
            if not isinstance(raw_page, dict):
                continue

            page_number = raw_page.get("page_number")
            if page_number is None:
                page_number = index + 1

            text = raw_page.get("text", "")
            markdown = raw_page.get("markdown", text)

            layout_blocks = []
            tables = []
            images = []
            figures = []
            ocr_text = ""

            for item in raw_page.get("page_boxes", []):
                if not isinstance(item, dict):
                    continue
                block_type = str(item.get("class") or item.get("type") or "text").lower()
                bbox = self._to_bbox(item.get("bbox"))
                block = {
                    "type": block_type,
                    "bbox": bbox,
                    "page_number": page_number,
                    "index": item.get("index"),
                    "class": block_type,
                    "text": item.get("text", ""),
                    "pos": item.get("pos"),
                }
                layout_blocks.append(block)
                if block_type == "table":
                    tables.append(block)
                elif block_type in {"image", "figure"}:
                    images.append(block)
                    figures.append(block)

            normalized_pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "markdown": markdown,
                    "tables": tables,
                    "images": images,
                    "figures": figures,
                    "layout_blocks": layout_blocks,
                    "ocr_text": ocr_text,
                    "metadata": raw_page.get("metadata", {}),
                }
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
            "metadata": {
                "page_count": len(normalized_pages),
                "source": "pymupdf4llm",
            },
            "pages": normalized_pages,
            "statistics": {
                "page_count": len(normalized_pages),
                "table_count": sum(len(page["tables"]) for page in normalized_pages),
                "image_count": sum(len(page["images"]) for page in normalized_pages),
            },
        }