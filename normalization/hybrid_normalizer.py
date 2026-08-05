import html
import re
from typing import Any

from normalization.base_normalizer import BaseNormalizer


class HybridNormalizer(BaseNormalizer):
    """
    Converts the Hybrid Approach Markdown output into the
    benchmark's common normalized schema.

    Supported from Markdown:
    - page boundaries
    - plain text
    - Markdown
    - Markdown tables
    - table rows/cells
    - image references/descriptions

    Unsupported from Markdown alone:
    - reliable PDF-coordinate bounding boxes
    - spatial table detection
    - spatial image detection
    - spatial layout evaluation
    """

    PAGE_PATTERN = re.compile(
        r"<!--\s*Page\s+(\d+)\s*-->",
        re.IGNORECASE,
    )

    IMAGE_PATTERN = re.compile(
        r"!\[([^\]]*)\]\(([^)]+)\)"
    )

    IMAGE_DESCRIPTION_PATTERN = re.compile(
        r"^>\s*🖼\s*\*\*\[([^\]]+)\]\*\*\s*(.*)$",
        re.MULTILINE,
    )

    @staticmethod
    def _split_pages(
        markdown: str,
    ) -> list[tuple[int, str]]:
        """
        Splits the Hybrid Markdown using explicit markers such as:

            <!-- Page 1 -->
            <!-- Page 2 -->

        Returns:
            List of (page_number, page_markdown).
        """

        matches = list(
            HybridNormalizer.PAGE_PATTERN.finditer(
                markdown
            )
        )

        if not matches:
            return []

        pages = []

        for index, match in enumerate(
            matches
        ):
            page_number = int(
                match.group(1)
            )

            start = match.end()

            if index + 1 < len(matches):
                end = matches[
                    index + 1
                ].start()
            else:
                end = len(
                    markdown
                )

            page_markdown = markdown[
                start:end
            ].strip()

            pages.append(
                (
                    page_number,
                    page_markdown,
                )
            )

        return pages

    @staticmethod
    def _clean_markdown_text(
        markdown: str,
    ) -> str:
        """
        Produces plain textual content from Markdown.

        The goal is not to reinterpret the document.
        It removes Markdown syntax while preserving
        the visible textual content.
        """

        text = markdown

        # Remove HTML comments.
        text = re.sub(
            r"<!--.*?-->",
            "",
            text,
            flags=re.DOTALL,
        )

        # Replace Markdown images with their alt text.
        text = re.sub(
            r"!\[([^\]]*)\]\([^)]+\)",
            r"\1",
            text,
        )

        # Preserve visible text from links.
        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text,
        )

        # Remove heading markers.
        text = re.sub(
            r"^\s{0,3}#{1,6}\s*",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove blockquote markers.
        text = re.sub(
            r"^\s*>\s?",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove horizontal rules.
        text = re.sub(
            r"^\s*[-*_]{3,}\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove emphasis markers.
        text = text.replace(
            "**",
            "",
        )

        text = text.replace(
            "__",
            "",
        )

        text = text.replace(
            "`",
            "",
        )

        # Remove Markdown table separator rows.
        text = re.sub(
            r"^\s*\|?"
            r"\s*:?-{3,}:?\s*"
            r"(?:\|\s*:?-{3,}:?\s*)+"
            r"\|?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Convert Markdown table pipes into spaces.
        text = re.sub(
            r"\s*\|\s*",
            " ",
            text,
        )

        # Remove simple list markers while preserving content.
        text = re.sub(
            r"^\s*[-+*]\s+",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = html.unescape(
            text
        )

        # Normalize horizontal whitespace.
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Avoid excessive blank lines.
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    @staticmethod
    def _split_markdown_row(
        line: str,
    ) -> list[str]:
        """
        Converts one Markdown table row into cells.
        """

        stripped = line.strip()

        if stripped.startswith("|"):
            stripped = stripped[1:]

        if stripped.endswith("|"):
            stripped = stripped[:-1]

        cells = [
            cell.strip()
            for cell in stripped.split("|")
        ]

        return cells

    @staticmethod
    def _is_separator_row(
        cells: list[str],
    ) -> bool:
        """
        Detects Markdown table separator rows such as:

            |---|---|
            |:---|---:|
        """

        if not cells:
            return False

        for cell in cells:

            value = cell.strip()

            if not re.fullmatch(
                r":?-{3,}:?",
                value,
            ):
                return False

        return True

    @staticmethod
    def _rows_to_html(
        rows: list[list[str]],
    ) -> str:
        """
        Generates a simple canonical HTML representation
        for the normalized table.
        """

        html_rows = []

        for row in rows:

            cells = "".join(
                "<td>"
                + html.escape(
                    str(cell)
                )
                + "</td>"
                for cell in row
            )

            html_rows.append(
                f"<tr>{cells}</tr>"
            )

        return (
            "<table><tbody>"
            + "".join(
                html_rows
            )
            + "</tbody></table>"
        )

    @staticmethod
    def _rows_to_cells(
        rows: list[list[str]],
    ) -> list[dict[str, Any]]:
        """
        Converts table rows into the common cell schema.
        """

        cells = []

        for row_index, row in enumerate(
            rows
        ):

            for column_index, text in enumerate(
                row
            ):

                cells.append(
                    {
                        "row": row_index,
                        "column": column_index,
                        "text": str(
                            text or ""
                        ).strip(),
                    }
                )

        return cells

    @staticmethod
    def _extract_tables(
        page_markdown: str,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Extracts contiguous Markdown table blocks.

        A table must contain:
        - at least two pipe-delimited rows
        - a valid Markdown separator row

        Spatial bounding boxes are intentionally not
        fabricated because Markdown does not contain
        reliable PDF coordinates.
        """

        lines = page_markdown.splitlines()

        candidate_blocks = []
        current_block = []

        for line in lines:

            stripped = line.strip()

            if (
                "|" in stripped
                and stripped
            ):
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

            if len(block) < 2:
                continue

            parsed_rows = [
                HybridNormalizer._split_markdown_row(
                    line
                )
                for line in block
            ]

            separator_index = None

            for index, row in enumerate(
                parsed_rows
            ):

                if HybridNormalizer._is_separator_row(
                    row
                ):
                    separator_index = index
                    break

            if separator_index is None:
                continue

            # Keep all actual data/header rows but remove
            # Markdown's formatting separator.
            rows = [
                row
                for index, row in enumerate(
                    parsed_rows
                )
                if index != separator_index
            ]

            rows = [
                [
                    cell.strip()
                    for cell in row
                ]
                for row in rows
                if any(
                    cell.strip()
                    for cell in row
                )
            ]

            if not rows:
                continue

            column_count = max(
                len(row)
                for row in rows
            )

            normalized_rows = []

            for row in rows:

                padded = (
                    row
                    + [""] * (
                        column_count
                        - len(row)
                    )
                )

                normalized_rows.append(
                    padded
                )

            cells = (
                HybridNormalizer._rows_to_cells(
                    normalized_rows
                )
            )

            markdown_table = "\n".join(
                block
            )

            tables.append(
                {
                    "type": "table",
                    "class": "table",
                    "page_number": page_number,

                    # No PDF-coordinate geometry is available
                    # from the Markdown output.
                    "bbox": None,

                    "markdown": markdown_table,
                    "rows": normalized_rows,
                    "cells": cells,
                    "row_count": len(
                        normalized_rows
                    ),
                    "column_count": (
                        column_count
                    ),
                    "cell_count": len(
                        cells
                    ),
                    "html": (
                        HybridNormalizer._rows_to_html(
                            normalized_rows
                        )
                    ),
                    "has_structure": True,
                    "structure_only": True,
                }
            )

        return tables

    @staticmethod
    def _extract_images(
        page_markdown: str,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Preserves image references exposed by the Hybrid
        Markdown.

        These records indicate that the Hybrid pipeline
        represented an image, but they are NOT spatial
        detections because PDF bounding boxes are absent.
        """

        images = []

        seen = set()

        for match in (
            HybridNormalizer.IMAGE_PATTERN.finditer(
                page_markdown
            )
        ):

            alt_text = (
                match.group(1)
                .strip()
            )

            source = (
                match.group(2)
                .strip()
            )

            key = (
                "reference",
                source,
                alt_text,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            images.append(
                {
                    "type": "image",
                    "page_number": page_number,
                    "bbox": None,
                    "source": source,
                    "alt_text": alt_text,
                    "description": "",
                    "representation": (
                        "markdown_image"
                    ),
                    "spatially_evaluable": False,
                }
            )

        for match in (
            HybridNormalizer
            .IMAGE_DESCRIPTION_PATTERN
            .finditer(
                page_markdown
            )
        ):

            image_id = (
                match.group(1)
                .strip()
            )

            description = (
                match.group(2)
                .strip()
            )

            key = (
                "description",
                image_id,
                description,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            images.append(
                {
                    "type": "image_description",
                    "page_number": page_number,
                    "bbox": None,
                    "source": None,
                    "image_id": image_id,
                    "alt_text": "",
                    "description": description,
                    "representation": (
                        "semantic_image_description"
                    ),
                    "spatially_evaluable": False,
                }
            )

        return images

    @staticmethod
    def _extract_layout_blocks(
        page_markdown: str,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Preserves logical Markdown structure.

        These blocks are useful for inspecting the Hybrid
        representation but are deliberately non-spatial.
        Therefore they must not be used for IoU-based
        layout scoring.
        """

        blocks = []

        for order, line in enumerate(
            page_markdown.splitlines()
        ):

            stripped = line.strip()

            if not stripped:
                continue

            block_type = "text"
            text = stripped

            heading_match = re.match(
                r"^(#{1,6})\s+(.*)$",
                stripped,
            )

            if heading_match:

                block_type = "heading"

                text = (
                    heading_match.group(2)
                    .strip()
                )

            elif stripped.startswith(
                ">"
            ):

                block_type = "blockquote"

                text = re.sub(
                    r"^>\s*",
                    "",
                    stripped,
                )

            elif re.match(
                r"^[-+*]\s+",
                stripped,
            ):

                block_type = "list_item"

                text = re.sub(
                    r"^[-+*]\s+",
                    "",
                    stripped,
                )

            elif HybridNormalizer.IMAGE_PATTERN.search(
                stripped
            ):

                block_type = "image_reference"

            elif "|" in stripped:

                # Table structure is already represented
                # separately under page["tables"].
                continue

            blocks.append(
                {
                    "type": block_type,
                    "text": text,
                    "bbox": None,
                    "page_number": page_number,
                    "reading_order": order,
                    "spatially_evaluable": False,
                }
            )

        return blocks

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:
        """
        Converts Hybrid Markdown into the benchmark's
        common normalized schema.

        Expected raw input:

        {
            "parser": "hybrid",
            "source_pdf": "...",
            "markdown": "..."
        }
        """

        markdown = raw_json.get(
            "markdown",
            "",
        )

        if not isinstance(
            markdown,
            str,
        ):
            raise ValueError(
                "Hybrid raw input must contain "
                "Markdown text under 'markdown'."
            )

        page_sections = self._split_pages(
            markdown
        )

        if not page_sections:
            raise ValueError(
                "No '<!-- Page N -->' page markers "
                "were found in Hybrid Markdown."
            )

        normalized = {
            "parser": raw_json.get(
                "parser",
                "hybrid",
            ),
            "source_pdf": raw_json.get(
                "source_pdf",
                "",
            ),
            "metadata": {
                "source_format": "markdown",
                "approach": "hybrid",
                "spatial_geometry_available": False,
            },
            "pages": [],
            "statistics": {
                "page_count": len(
                    page_sections
                ),
                "table_count": 0,
                "structured_table_count": 0,
                "table_cell_count": 0,
                "image_count": 0,
                "layout_block_count": 0,
            },
        }

        for (
            page_number,
            page_markdown,
        ) in page_sections:

            tables = self._extract_tables(
                page_markdown,
                page_number,
            )

            images = self._extract_images(
                page_markdown,
                page_number,
            )

            layout_blocks = (
                self._extract_layout_blocks(
                    page_markdown,
                    page_number,
                )
            )

            page_text = (
                self._clean_markdown_text(
                    page_markdown
                )
            )

            page = {
                "page_number": page_number,
                "text": page_text,
                "markdown": page_markdown,
                "tables": tables,
                "images": images,
                "figures": list(
                    images
                ),
                "layout_blocks": (
                    layout_blocks
                ),
                "ocr_text": "",
                "metadata": {
                    "source_format": (
                        "markdown"
                    ),
                    "spatial_geometry_available": (
                        False
                    ),
                },
            }

            normalized[
                "pages"
            ].append(
                page
            )

        normalized[
            "pages"
        ].sort(
            key=lambda page: page[
                "page_number"
            ]
        )

        normalized[
            "statistics"
        ][
            "table_count"
        ] = sum(
            len(
                page.get(
                    "tables",
                    [],
                )
            )
            for page in normalized[
                "pages"
            ]
        )

        normalized[
            "statistics"
        ][
            "structured_table_count"
        ] = sum(
            1
            for page in normalized[
                "pages"
            ]
            for table in page.get(
                "tables",
                [],
            )
            if table.get(
                "has_structure"
            )
        )

        normalized[
            "statistics"
        ][
            "table_cell_count"
        ] = sum(
            len(
                table.get(
                    "cells",
                    [],
                )
            )
            for page in normalized[
                "pages"
            ]
            for table in page.get(
                "tables",
                [],
            )
        )

        normalized[
            "statistics"
        ][
            "image_count"
        ] = sum(
            len(
                page.get(
                    "images",
                    [],
                )
            )
            for page in normalized[
                "pages"
            ]
        )

        normalized[
            "statistics"
        ][
            "layout_block_count"
        ] = sum(
            len(
                page.get(
                    "layout_blocks",
                    [],
                )
            )
            for page in normalized[
                "pages"
            ]
        )

        return normalized