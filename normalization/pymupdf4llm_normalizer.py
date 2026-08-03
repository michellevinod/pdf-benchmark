import html
import re

from normalization.base_normalizer import BaseNormalizer


class PyMuPDF4LLMNormalizer(BaseNormalizer):
    """
    Converts PyMuPDF4LLM raw JSON into the common normalized schema.

    Preserves spatial table detections from page_boxes and enriches
    them with table structures recovered from PyMuPDF4LLM Markdown.
    """

    @staticmethod
    def _to_bbox(value):
        """
        Converts supported bbox representations into the common
        {l, t, r, b} format.
        """

        if isinstance(value, dict):
            left = value.get(
                "l",
                value.get("x", 0.0),
            )
            top = value.get(
                "t",
                value.get("y", 0.0),
            )
            right = value.get(
                "r",
                value.get("x1", left),
            )
            bottom = value.get(
                "b",
                value.get("y1", top),
            )

            return {
                "l": float(left),
                "t": float(top),
                "r": float(right),
                "b": float(bottom),
            }

        if (
            isinstance(value, (list, tuple))
            and len(value) >= 4
        ):
            left, top, right, bottom = value[:4]

            return {
                "l": float(left),
                "t": float(top),
                "r": float(right),
                "b": float(bottom),
            }

        return {
            "l": 0.0,
            "t": 0.0,
            "r": 0.0,
            "b": 0.0,
        }

    @staticmethod
    def _clean_cell(value: str) -> str:
        """
        Cleans a Markdown table cell while preserving its textual
        content for structural comparison.
        """

        value = str(value or "").strip()

        # Remove common Markdown formatting without deleting content.
        value = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            value,
        )

        value = re.sub(
            r"__(.*?)__",
            r"\1",
            value,
        )

        value = re.sub(
            r"(?<!\*)\*([^*]+)\*(?!\*)",
            r"\1",
            value,
        )

        value = re.sub(
            r"(?<!_)_([^_]+)_(?!_)",
            r"\1",
            value,
        )

        value = re.sub(
            r"<br\s*/?>",
            " ",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _split_markdown_row(
        line: str,
    ) -> list[str]:
        """
        Splits a Markdown table row into cells.

        Escaped pipe characters are temporarily protected so they
        are not interpreted as column separators.
        """

        placeholder = "__ESCAPED_PIPE__"

        protected = line.replace(
            r"\|",
            placeholder,
        )

        protected = protected.strip()

        if protected.startswith("|"):
            protected = protected[1:]

        if protected.endswith("|"):
            protected = protected[:-1]

        cells = protected.split("|")

        return [
            PyMuPDF4LLMNormalizer._clean_cell(
                cell.replace(
                    placeholder,
                    "|",
                )
            )
            for cell in cells
        ]

    @staticmethod
    def _is_separator_row(
        cells: list[str],
    ) -> bool:
        """
        Identifies Markdown table separator rows such as:

        | --- | ---: | :---: |
        """

        if not cells:
            return False

        found_nonempty = False

        for cell in cells:

            value = cell.strip()

            if not value:
                continue

            found_nonempty = True

            if not re.fullmatch(
                r":?-{3,}:?",
                value,
            ):
                return False

        return found_nonempty

    @staticmethod
    def _looks_like_table_block(
        lines: list[str],
    ) -> bool:
        """
        Determines whether a sequence of Markdown lines represents
        a table rather than ordinary prose containing pipe symbols.
        """

        if len(lines) < 2:
            return False

        parsed_rows = [
            PyMuPDF4LLMNormalizer._split_markdown_row(
                line
            )
            for line in lines
        ]

        parsed_rows = [
            row
            for row in parsed_rows
            if len(row) >= 2
        ]

        if len(parsed_rows) < 2:
            return False

        # Standard Markdown tables normally contain a separator row.
        if any(
            PyMuPDF4LLMNormalizer._is_separator_row(
                row
            )
            for row in parsed_rows[:3]
        ):
            return True

        # PyMuPDF4LLM may produce pipe-based tables without a perfect
        # Markdown separator. Require multiple consistently tabular rows.
        widths = [
            len(row)
            for row in parsed_rows
        ]

        if len(widths) < 3:
            return False

        most_common_width = max(
            set(widths),
            key=widths.count,
        )

        matching_rows = sum(
            1
            for width in widths
            if width == most_common_width
        )

        return (
            most_common_width >= 2
            and matching_rows >= 2
        )

    @staticmethod
    def _normalize_rows(
        rows: list[list[str]],
    ) -> list[list[str]]:
        """
        Removes Markdown separator rows and normalizes row widths.
        """

        cleaned_rows = []

        for row in rows:

            if (
                PyMuPDF4LLMNormalizer._is_separator_row(
                    row
                )
            ):
                continue

            cleaned = [
                PyMuPDF4LLMNormalizer._clean_cell(
                    cell
                )
                for cell in row
            ]

            if any(cleaned):
                cleaned_rows.append(
                    cleaned
                )

        if not cleaned_rows:
            return []

        max_columns = max(
            len(row)
            for row in cleaned_rows
        )

        normalized = []

        for row in cleaned_rows:

            padded = (
                row
                + [""] * (
                    max_columns - len(row)
                )
            )

            normalized.append(
                padded
            )

        return normalized

    @staticmethod
    def _rows_to_html(
        rows: list[list[str]],
    ) -> str:
        """
        Converts canonical rows into deterministic HTML suitable
        for structural table comparison.
        """

        if not rows:
            return ""

        html_rows = []

        for row in rows:

            cells = "".join(
                "<td>"
                + html.escape(
                    str(cell),
                    quote=True,
                )
                + "</td>"
                for cell in row
            )

            html_rows.append(
                f"<tr>{cells}</tr>"
            )

        return (
            "<table><tbody>"
            + "".join(html_rows)
            + "</tbody></table>"
        )

    @staticmethod
    def _rows_to_cells(
        rows: list[list[str]],
    ) -> list[dict]:
        """
        Converts canonical table rows into the common normalized
        cell representation used by table evaluation metrics.
        """

        cells = []

        for row_index, row in enumerate(rows):

            for column_index, text in enumerate(row):

                cells.append(
                    {
                        "row": row_index,
                        "column": column_index,
                        "text": str(text or "").strip(),
                    }
                )

        return cells

    @staticmethod
    def _extract_markdown_tables(
        markdown: str,
    ) -> list[dict]:
        """
        Extracts table-like Markdown blocks and converts them into
        canonical rows and HTML.
        """

        if not isinstance(markdown, str):
            return []

        lines = markdown.splitlines()

        candidate_blocks = []
        current_block = []

        for line in lines:

            stripped = line.strip()

            # A potential Markdown table row must contain a pipe.
            if "|" in stripped:
                current_block.append(
                    stripped
                )

            else:
                if current_block:
                    candidate_blocks.append(
                        current_block
                    )
                    current_block = []

        if current_block:
            candidate_blocks.append(
                current_block
            )

        tables = []

        for block in candidate_blocks:

            if not (
                PyMuPDF4LLMNormalizer._looks_like_table_block(
                    block
                )
            ):
                continue

            raw_rows = [
                PyMuPDF4LLMNormalizer._split_markdown_row(
                    line
                )
                for line in block
            ]

            rows = (
                PyMuPDF4LLMNormalizer._normalize_rows(
                    raw_rows
                )
            )

            if len(rows) < 2:
                continue

            column_count = max(
                len(row)
                for row in rows
            )

            if column_count < 2:
                continue

            markdown_table = "\n".join(
                block
            )

            cells = (
                PyMuPDF4LLMNormalizer._rows_to_cells(
                    rows
                )
            )

            tables.append(
                {
                    "markdown": markdown_table,
                    "rows": rows,
                    "cells": cells,
                    "row_count": len(rows),
                    "column_count": column_count,
                    "cell_count": len(cells),
                    "html": (
                        PyMuPDF4LLMNormalizer._rows_to_html(
                            rows
                        )
                    ),
                }
            )

        return tables

    @staticmethod
    def _attach_table_structures(
        detected_tables: list[dict],
        structural_tables: list[dict],
        page_number: int,
    ) -> list[dict]:
        """
        Combines spatial table detections with Markdown structures.

        The parser's existing table detections remain authoritative
        for bounding boxes. Structural tables are attached in page
        order when both representations are available.

        Any additional Markdown table structure is preserved as a
        structure-only table instead of silently discarding it.
        """

        combined_tables = []

        pair_count = min(
            len(detected_tables),
            len(structural_tables),
        )

        # Pair detected table regions and Markdown structures
        # in their page order.
        for index in range(pair_count):

            table = dict(
                detected_tables[index]
            )

            structure = (
                structural_tables[index]
            )

            table.update(
                {
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
                }
            )

            combined_tables.append(
                table
            )

        # Spatial detections for which no usable Markdown
        # structure was recovered.
        for index in range(
            pair_count,
            len(detected_tables),
        ):

            table = dict(
                detected_tables[index]
            )

            table.update(
                {
                    "markdown": "",
                    "rows": [],
                    "cells": [],
                    "row_count": 0,
                    "column_count": 0,
                    "cell_count": 0,
                    "html": "",
                    "has_structure": False,
                }
            )

            combined_tables.append(
                table
            )

        # Markdown structures with no corresponding page-box
        # table detection are preserved, but explicitly marked
        # as structure-only.
        for index in range(
            pair_count,
            len(structural_tables),
        ):

            structure = (
                structural_tables[index]
            )

            combined_tables.append(
                {
                    "type": "table",
                    "class": "table",
                    "page_number": page_number,
                    "index": None,
                    "bbox": {
                        "l": 0.0,
                        "t": 0.0,
                        "r": 0.0,
                        "b": 0.0,
                    },
                    "text": "",
                    "pos": None,
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

        return combined_tables

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

        for index, raw_page in enumerate(
            raw_pages
        ):

            if not isinstance(
                raw_page,
                dict,
            ):
                continue

            page_number = raw_page.get(
                "page_number"
            )

            if page_number is None:
                page_number = index + 1

            text = raw_page.get(
                "text",
                "",
            )

            markdown = raw_page.get(
                "markdown",
                text,
            )

            layout_blocks = []
            detected_tables = []
            images = []
            figures = []
            ocr_text = ""

            # -------------------------------------------------
            # Spatial detections from PyMuPDF4LLM page_boxes
            # -------------------------------------------------

            for item in raw_page.get(
                "page_boxes",
                [],
            ):

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                block_type = str(
                    item.get("class")
                    or item.get("type")
                    or "text"
                ).lower()

                bbox = self._to_bbox(
                    item.get("bbox")
                )

                block = {
                    "type": block_type,
                    "bbox": bbox,
                    "page_number": (
                        page_number
                    ),
                    "index": item.get(
                        "index"
                    ),
                    "class": block_type,
                    "text": item.get(
                        "text",
                        "",
                    ),
                    "pos": item.get(
                        "pos"
                    ),
                }

                layout_blocks.append(
                    block
                )

                if block_type == "table":
                    detected_tables.append(
                        block
                    )

                elif block_type in {
                    "image",
                    "figure",
                }:
                    images.append(
                        block
                    )

                    figures.append(
                        block
                    )

            # -------------------------------------------------
            # Recover table structure from page Markdown
            # -------------------------------------------------

            structural_tables = (
                self._extract_markdown_tables(
                    markdown
                )
            )

            tables = (
                self._attach_table_structures(
                    detected_tables=detected_tables,
                    structural_tables=structural_tables,
                    page_number=page_number,
                )
            )

            normalized_pages.append(
                {
                    "page_number": (
                        page_number
                    ),
                    "text": text,
                    "markdown": markdown,
                    "tables": tables,
                    "images": images,
                    "figures": figures,
                    "layout_blocks": (
                        layout_blocks
                    ),
                    "ocr_text": (
                        ocr_text
                    ),
                    "metadata": raw_page.get(
                        "metadata",
                        {},
                    ),
                }
            )

        total_tables = sum(
            len(
                page["tables"]
            )
            for page in normalized_pages
        )

        structured_tables = sum(
            1
            for page in normalized_pages
            for table in page["tables"]
            if table.get(
                "has_structure",
                False,
            )
        )

        total_cells = sum(
            int(
                table.get(
                    "cell_count",
                    0,
                )
            )
            for page in normalized_pages
            for table in page["tables"]
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
                "page_count": len(
                    normalized_pages
                ),
                "source": (
                    "pymupdf4llm"
                ),
            },
            "pages": (
                normalized_pages
            ),
            "statistics": {
                "page_count": len(
                    normalized_pages
                ),
                "table_count": (
                    total_tables
                ),
                "structured_table_count": (
                    structured_tables
                ),
                "table_cell_count": (
                    total_cells
                ),
                "image_count": sum(
                    len(
                        page["images"]
                    )
                    for page
                    in normalized_pages
                ),
            },
        }