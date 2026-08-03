import re

from normalization.base_normalizer import BaseNormalizer
from normalization.pymupdf4llm_normalizer import PyMuPDF4LLMNormalizer


class LiteParseNormalizer(BaseNormalizer):
    """
    Converts LiteParse raw JSON into the common normalized schema.

    Preserves page-level text, markdown, layout information,
    and OCR-derived content for benchmark evaluation.
    """

    @staticmethod
    def _parse_text_item(
        item: str,
    ) -> dict | None:
        """
        Parses LiteParse's serialized TextItem representation.
        """

        if not isinstance(item, str):
            return None

        text_match = re.search(
            r"TextItem\(text=(['\"])(.*?)\1,\s*x=",
            item,
            re.DOTALL,
        )

        x_match = re.search(
            r"\bx=([-+]?\d*\.?\d+)",
            item,
        )

        y_match = re.search(
            r"\by=([-+]?\d*\.?\d+)",
            item,
        )

        width_match = re.search(
            r"\bwidth=([-+]?\d*\.?\d+)",
            item,
        )

        height_match = re.search(
            r"\bheight=([-+]?\d*\.?\d+)",
            item,
        )

        font_match = re.search(
            r"font_name=(?:'([^']*)'|\"([^\"]*)\"|None)",
            item,
        )

        confidence_match = re.search(
            r"\bconfidence=([-+]?\d*\.?\d+)",
            item,
        )

        rotation_match = re.search(
            r"\brotation=([-+]?\d*\.?\d+)",
            item,
        )

        if not (
            x_match
            and y_match
            and width_match
            and height_match
        ):
            return None

        text = (
            text_match.group(2)
            if text_match
            else ""
        )

        font_name = None

        if font_match:
            font_name = (
                font_match.group(1)
                or font_match.group(2)
            )

        x = float(
            x_match.group(1)
        )

        y = float(
            y_match.group(1)
        )

        width = float(
            width_match.group(1)
        )

        height = float(
            height_match.group(1)
        )

        confidence = (
            float(
                confidence_match.group(1)
            )
            if confidence_match
            else None
        )

        rotation = (
            float(
                rotation_match.group(1)
            )
            if rotation_match
            else 0.0
        )

        is_ocr = (
            font_name is not None
            and font_name.upper() == "OCR"
        )

        return {
            "type": (
                "ocr_text"
                if is_ocr
                else "text"
            ),
            "text": text,
            "bbox": {
                "l": x,
                "t": y,
                "r": x + width,
                "b": y + height,
            },
            "font_name": font_name,
            "confidence": confidence,
            "rotation": rotation,
            "is_ocr": is_ocr,
        }

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        raw_pages = raw_json.get(
            "pages",
            [],
        )

        normalized = {
            "parser": raw_json.get(
                "parser",
                "liteparse",
            ),
            "source_pdf": raw_json.get(
                "source_pdf",
                "",
            ),
            "metadata": {
                "producer": raw_json.get(
                    "producer"
                ),
                "creator": raw_json.get(
                    "creator"
                ),
                "form_type": raw_json.get(
                    "form_type"
                ),
            },
            "pages": [],
            "statistics": {
                "page_count": raw_json.get(
                    "num_pages",
                    len(raw_pages),
                ),
                "table_count": 0,
                "image_count": raw_json.get(
                    "image_count",
                    0,
                ),
                "image_error_count": (
                    raw_json.get(
                        "image_error_count",
                        0,
                    )
                ),
            },
        }

        for raw_page in raw_pages:

            page_number = raw_page.get(
                "page_number"
            )

            layout_blocks = []
            ocr_text_parts = []

            text_items = raw_page.get(
                "text_items",
                [],
            )

            for item in text_items:

                block = self._parse_text_item(
                    item
                )

                if block is None:
                    continue

                layout_blocks.append(
                    block
                )

                if (
                    block["is_ocr"]
                    and block["text"]
                ):
                    ocr_text_parts.append(
                        block["text"]
                    )

            # Sort approximately in visual reading order.
            layout_blocks.sort(
                key=lambda block: (
                    block["bbox"]["t"],
                    block["bbox"]["l"],
                )
            )

            markdown = raw_page.get(
                "markdown",
                "",
            )

            structural_tables = (
                PyMuPDF4LLMNormalizer._extract_markdown_tables(
                    markdown
                )
            )

            tables = []

            for table_index, structure in enumerate(
                structural_tables
            ):
                tables.append(
                    {
                        "type": "table",
                        "class": "table",
                        "page_number": page_number,
                        "index": table_index,
                        "bbox": None,
                        "text": "",
                        "markdown": structure[
                            "markdown"
                        ],
                        "rows": structure[
                            "rows"
                        ],
                        "cells": structure[
                            "cells"
                        ],
                        "row_count": structure[
                            "row_count"
                        ],
                        "column_count": structure[
                            "column_count"
                        ],
                        "cell_count": structure[
                            "cell_count"
                        ],
                        "html": structure[
                            "html"
                        ],
                        "has_structure": True,
                        "structure_only": True,
                    }
                )

            page = {
                "page_number": page_number,
                "text": raw_page.get(
                    "text",
                    "",
                ),
                "markdown": raw_page.get(
                    "markdown",
                    "",
                ),
                "tables": tables,
                "images": [],
                "figures": [],
                "layout_blocks": layout_blocks,
                "ocr_text": "\n".join(
                    ocr_text_parts
                ),
                "metadata": {
                    "width": raw_page.get(
                        "width"
                    ),
                    "height": raw_page.get(
                        "height"
                    ),
                    "annotations": (
                        raw_page.get(
                            "annotations"
                        )
                    ),
                    "form_fields": (
                        raw_page.get(
                            "form_fields"
                        )
                    ),
                    "vector_graphics": (
                        raw_page.get(
                            "vector_graphics"
                        )
                    ),
                    "content_bounds": (
                        raw_page.get(
                            "content_bounds"
                        )
                    ),
                    "structure_tree": (
                        raw_page.get(
                            "structure_tree"
                        )
                    ),
                    "complexity": (
                        raw_page.get(
                            "complexity"
                        )
                    ),
                },
            }

            normalized["pages"].append(
                page
            )

        normalized["statistics"]["table_count"] = sum(
            len(page.get("tables", []))
            for page in normalized["pages"]
        )

        normalized["statistics"]["structured_table_count"] = sum(
            1
            for page in normalized["pages"]
            for table in page.get("tables", [])
            if table.get("has_structure")
        )

        normalized["statistics"]["table_cell_count"] = sum(
            len(table.get("cells", []))
            for page in normalized["pages"]
            for table in page.get("tables", [])
        )

        return normalized