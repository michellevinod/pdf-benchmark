from typing import Any

from apted import APTED, Config
from rapidfuzz.fuzz import ratio


class TableTree:
    """
    Node representation used for table tree-edit comparison.
    """

    def __init__(
        self,
        name: str,
        children: list["TableTree"] | None = None,
    ):
        self.name = name
        self.children = children or []


class TableTEDSConfig(Config):
    """
    Cost configuration for table tree edit distance.
    """

    def rename(
        self,
        node1: TableTree,
        node2: TableTree,
    ) -> float:

        if (
            node1.name.startswith("CELL|")
            and node2.name.startswith("CELL|")
        ):

            text1 = node1.name.split("|", 1)[1]
            text2 = node2.name.split("|", 1)[1]

            similarity = ratio(
                text1,
                text2,
            ) / 100.0

            return 1.0 - similarity

        return (
            0.0
            if node1.name == node2.name
            else 1.0
        )

    def children(
        self,
        node: TableTree,
    ) -> list[TableTree]:

        return node.children


class TableMetrics:
    """
    Evaluates table extraction and structural quality.

    Includes:
    - extraction statistics
    - detection precision / recall / F1
    - table coverage
    - TEDS-style normalized tree edit similarity

    TEDS is calculated only when both the reference
    and extracted tables expose usable cell content.
    """

    @staticmethod
    def _normalize_bbox(
        bbox: Any,
        page_height: float | None = None,
    ) -> tuple[float, float, float, float] | None:
        """
        Converts supported bbox representations to a common
        top-left coordinate system.

        Returns:
            (left, top, right, bottom)

        Invalid or zero-area boxes return None.
        """

        if bbox is None:
            return None

        coord_origin = None

        if isinstance(bbox, dict):

            try:
                left = float(bbox["l"])
                top = float(bbox["t"])
                right = float(bbox["r"])
                bottom = float(bbox["b"])

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                return None

            coord_origin = bbox.get(
                "coord_origin"
            )

        elif (
            isinstance(bbox, (list, tuple))
            and len(bbox) >= 4
        ):

            try:
                left = float(bbox[0])
                top = float(bbox[1])
                right = float(bbox[2])
                bottom = float(bbox[3])

            except (
                TypeError,
                ValueError,
            ):
                return None

        else:
            return None

        # Docling may expose PDF coordinates with the
        # origin at the bottom-left.
        if (
            coord_origin == "BOTTOMLEFT"
            and page_height is not None
        ):

            converted_top = (
                page_height - top
            )

            converted_bottom = (
                page_height - bottom
            )

            top = converted_top
            bottom = converted_bottom

        # Protect against reversed coordinate ordering.
        left, right = (
            min(left, right),
            max(left, right),
        )

        top, bottom = (
            min(top, bottom),
            max(top, bottom),
        )

        if (
            right <= left
            or bottom <= top
        ):
            return None

        return (
            left,
            top,
            right,
            bottom,
        )

    @staticmethod
    def _bbox_iou(
        bbox1: tuple[float, float, float, float],
        bbox2: tuple[float, float, float, float],
    ) -> float:
        """
        Computes intersection over union for two normalized boxes.
        """

        left = max(
            bbox1[0],
            bbox2[0],
        )

        top = max(
            bbox1[1],
            bbox2[1],
        )

        right = min(
            bbox1[2],
            bbox2[2],
        )

        bottom = min(
            bbox1[3],
            bbox2[3],
        )

        intersection_width = max(
            0.0,
            right - left,
        )

        intersection_height = max(
            0.0,
            bottom - top,
        )

        intersection = (
            intersection_width
            * intersection_height
        )

        area1 = (
            (bbox1[2] - bbox1[0])
            * (bbox1[3] - bbox1[1])
        )

        area2 = (
            (bbox2[2] - bbox2[0])
            * (bbox2[3] - bbox2[1])
        )

        union = (
            area1
            + area2
            - intersection
        )

        if union <= 0:
            return 0.0

        return intersection / union

    @staticmethod
    def _collect_cell_texts(
        table: dict[str, Any],
    ) -> list[str]:

        cells = table.get(
            "cells",
            [],
        )

        if not isinstance(
            cells,
            list,
        ):
            return []

        texts = []

        for cell in cells:

            if isinstance(
                cell,
                dict,
            ):

                text = str(
                    cell.get(
                        "text",
                        "",
                    )
                ).strip()

                if text:
                    texts.append(
                        text
                    )

            elif cell is not None:

                text = str(
                    cell
                ).strip()

                if text:
                    texts.append(
                        text
                    )

        return texts

    @staticmethod
    def _cell_position(
        cell: dict[str, Any],
        fallback_index: int,
    ) -> tuple[int, int]:

        row = cell.get(
            "row",
            cell.get(
                "row_index",
                cell.get(
                    "start_row",
                    0,
                ),
            ),
        )

        column = cell.get(
            "column",
            cell.get(
                "col",
                cell.get(
                    "column_index",
                    cell.get(
                        "start_col",
                        fallback_index,
                    ),
                ),
            ),
        )

        try:
            row = int(row)

        except (
            TypeError,
            ValueError,
        ):
            row = 0

        try:
            column = int(column)

        except (
            TypeError,
            ValueError,
        ):
            column = fallback_index

        return row, column

    @staticmethod
    def _table_to_tree(
        table: dict[str, Any],
    ) -> TableTree | None:
        """
        Converts a normalized table into:

        TABLE
          ROW
            CELL
            CELL
          ROW
            CELL

        Cell text is retained so both structure and
        textual content influence the TEDS score.
        """

        cells = table.get(
            "cells",
            [],
        )

        if (
            not isinstance(
                cells,
                list,
            )
            or not cells
        ):
            return None

        rows: dict[
            int,
            list[
                tuple[
                    int,
                    str,
                ]
            ],
        ] = {}

        for index, cell in enumerate(
            cells
        ):

            if isinstance(
                cell,
                dict,
            ):

                text = str(
                    cell.get(
                        "text",
                        "",
                    )
                ).strip()

                row, column = (
                    TableMetrics._cell_position(
                        cell,
                        index,
                    )
                )

            else:

                text = str(
                    cell
                ).strip()

                row = 0
                column = index

            rows.setdefault(
                row,
                [],
            ).append(
                (
                    column,
                    text,
                )
            )

        row_nodes = []

        for row_number in sorted(
            rows
        ):

            ordered_cells = sorted(
                rows[row_number],
                key=lambda value: value[0],
            )

            cell_nodes = [
                TableTree(
                    f"CELL|{text}"
                )
                for _, text in ordered_cells
            ]

            row_nodes.append(
                TableTree(
                    "ROW",
                    cell_nodes,
                )
            )

        if not row_nodes:
            return None

        return TableTree(
            "TABLE",
            row_nodes,
        )

    @staticmethod
    def _tree_size(
        node: TableTree,
    ) -> int:

        return (
            1
            + sum(
                TableMetrics._tree_size(
                    child
                )
                for child in node.children
            )
        )

    @staticmethod
    def _teds(
        reference_table: dict[str, Any],
        extracted_table: dict[str, Any],
    ) -> float | None:
        """
        Calculates normalized Tree Edit Distance Similarity.

        Score:
            1 - edit_distance / max(tree sizes)

        Returns a value from 0 to 1.
        """

        reference_tree = (
            TableMetrics._table_to_tree(
                reference_table
            )
        )

        extracted_tree = (
            TableMetrics._table_to_tree(
                extracted_table
            )
        )

        if (
            reference_tree is None
            or extracted_tree is None
        ):
            return None

        distance = APTED(
            reference_tree,
            extracted_tree,
            TableTEDSConfig(),
        ).compute_edit_distance()

        reference_size = (
            TableMetrics._tree_size(
                reference_tree
            )
        )

        extracted_size = (
            TableMetrics._tree_size(
                extracted_tree
            )
        )

        denominator = max(
            reference_size,
            extracted_size,
            1,
        )

        score = (
            1.0
            - (
                distance
                / denominator
            )
        )

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

    @staticmethod
    def _best_table_match(
        reference_table: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> tuple[
        float | None,
        int | None,
    ]:
        """
        Finds the extracted table with the highest
        TEDS score for one reference table.
        """

        best_score = None
        best_index = None

        for index, candidate in enumerate(
            candidates
        ):

            score = TableMetrics._teds(
                reference_table,
                candidate,
            )

            if score is None:
                continue

            if (
                best_score is None
                or score > best_score
            ):
                best_score = score
                best_index = index

        return (
            best_score,
            best_index,
        )

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_tables: (
            list[
                list[
                    dict[
                        str,
                        Any,
                    ]
                ]
            ]
            | None
        ) = None,
        reference_table_count: (
            int
            | None
        ) = None,
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        extracted_tables_by_page = [
            page.get(
                "tables",
                [],
            )
            for page in pages
        ]

        extracted_table_count = sum(
            len(page_tables)
            for page_tables
            in extracted_tables_by_page
        )

        pages_with_tables = sum(
            1
            for page_tables
            in extracted_tables_by_page
            if page_tables
        )

        total_cells = 0
        empty_tables = 0
        cell_text_available = False

        for page_tables in (
            extracted_tables_by_page
        ):

            for table in page_tables:

                cells = table.get(
                    "cells",
                    [],
                )

                if isinstance(
                    cells,
                    list,
                ):
                    total_cells += len(
                        cells
                    )

                cell_texts = (
                    TableMetrics._collect_cell_texts(
                        table
                    )
                )

                if cell_texts:
                    cell_text_available = True

                else:
                    empty_tables += 1

        if (
            extracted_table_count
            and not cell_text_available
        ):
            total_cells = (
                "N/A/Unsupported"
            )

            empty_tables = 0

        page_count = len(
            pages
        )

        average_tables_per_page = (
            extracted_table_count
            / page_count
            if page_count
            else 0.0
        )

        if reference_tables is not None:

            reference_table_count = sum(
                len(page_tables)
                for page_tables
                in reference_tables
            )

        if reference_table_count is None:
            reference_table_count = 0

        # ------------------------------------------
        # Spatial table detection metrics
        # ------------------------------------------

        TABLE_IOU_THRESHOLD = 0.50

        valid_extracted_bbox_count = 0

        for page_index, page_tables in enumerate(
            extracted_tables_by_page
        ):

            page = (
                pages[page_index]
                if page_index < len(pages)
                else {}
            )

            metadata = page.get(
                "metadata",
                {},
            )

            page_height = metadata.get(
                "height"
            )

            for table in page_tables:

                bbox = TableMetrics._normalize_bbox(
                    table.get(
                        "bbox"
                    ),
                    page_height,
                )

                if bbox is not None:
                    valid_extracted_bbox_count += 1

        spatial_detection_supported = (
            reference_tables is not None
            and valid_extracted_bbox_count
            == extracted_table_count
            and extracted_table_count > 0
        )

        if spatial_detection_supported:

            detected_tables = 0

            page_total = max(
                len(reference_tables),
                len(extracted_tables_by_page),
            )

            for page_index in range(
                page_total
            ):

                reference_page_tables = (
                    reference_tables[page_index]
                    if page_index < len(reference_tables)
                    else []
                )

                extracted_page_tables = (
                    extracted_tables_by_page[page_index]
                    if page_index < len(
                        extracted_tables_by_page
                    )
                    else []
                )

                page = (
                    pages[page_index]
                    if page_index < len(pages)
                    else {}
                )

                page_height = page.get(
                    "metadata",
                    {},
                ).get(
                    "height"
                )

                remaining_candidates = []

                for table in extracted_page_tables:

                    bbox = TableMetrics._normalize_bbox(
                        table.get(
                            "bbox"
                        ),
                        page_height,
                    )

                    if bbox is not None:
                        remaining_candidates.append(
                            bbox
                        )

                for reference_table in (
                    reference_page_tables
                ):

                    reference_bbox = (
                        TableMetrics._normalize_bbox(
                            reference_table.get(
                                "bbox"
                            )
                        )
                    )

                    if reference_bbox is None:
                        continue

                    best_iou = 0.0
                    best_index = None

                    for (
                        index,
                        candidate_bbox,
                    ) in enumerate(
                        remaining_candidates
                    ):

                        iou = (
                            TableMetrics._bbox_iou(
                                reference_bbox,
                                candidate_bbox,
                            )
                        )

                        if iou > best_iou:
                            best_iou = iou
                            best_index = index

                    if (
                        best_index is not None
                        and best_iou
                        >= TABLE_IOU_THRESHOLD
                    ):
                        detected_tables += 1

                        remaining_candidates.pop(
                            best_index
                        )

            missing_tables = max(
                0,
                reference_table_count
                - detected_tables,
            )

            extra_tables = max(
                0,
                extracted_table_count
                - detected_tables,
            )

            precision = (
                detected_tables
                / extracted_table_count
                if extracted_table_count
                else 0.0
            )

            recall = (
                detected_tables
                / reference_table_count
                if reference_table_count
                else 0.0
            )

            f1_score = (
                (
                    2
                    * precision
                    * recall
                    / (
                        precision
                        + recall
                    )
                )
                if precision + recall
                else 0.0
            )

            table_coverage = (
                recall * 100
            )

        else:

            detected_tables = (
                "N/A/Unsupported"
            )

            missing_tables = (
                "N/A/Unsupported"
            )

            extra_tables = (
                "N/A/Unsupported"
            )

            precision = (
                "N/A/Unsupported"
            )

            recall = (
                "N/A/Unsupported"
            )

            f1_score = (
                "N/A/Unsupported"
            )

            table_coverage = (
                "N/A/Unsupported"
            )

        # ------------------------------------------
        # TEDS
        # ------------------------------------------

        teds_scores = []

        if (
            reference_tables is not None
            and cell_text_available
        ):

            page_total = max(
                len(
                    reference_tables
                ),
                len(
                    extracted_tables_by_page
                ),
            )

            for page_index in range(
                page_total
            ):

                reference_page_tables = (
                    reference_tables[
                        page_index
                    ]
                    if page_index
                    < len(
                        reference_tables
                    )
                    else []
                )

                extracted_page_tables = (
                    extracted_tables_by_page[
                        page_index
                    ]
                    if page_index
                    < len(
                        extracted_tables_by_page
                    )
                    else []
                )

                remaining_candidates = list(
                    extracted_page_tables
                )

                for reference_table in (
                    reference_page_tables
                ):

                    (
                        best_score,
                        best_index,
                    ) = (
                        TableMetrics._best_table_match(
                            reference_table,
                            remaining_candidates,
                        )
                    )

                    if best_score is None:

                        teds_scores.append(
                            0.0
                        )

                        continue

                    teds_scores.append(
                        best_score
                    )

                    if best_index is not None:

                        remaining_candidates.pop(
                            best_index
                        )

        if teds_scores:

            teds_score = (
                sum(
                    teds_scores
                )
                / len(
                    teds_scores
                )
            )

            teds_score_percent = round(
                teds_score * 100,
                2,
            )

        else:

            teds_score_percent = (
                "N/A/Unsupported"
            )

        return {
            "table_statistics": {
                "extracted_table_count": (
                    extracted_table_count
                ),
                "pages_with_tables": (
                    pages_with_tables
                ),
                "total_cells": (
                    total_cells
                ),
                "average_tables_per_page": round(
                    average_tables_per_page,
                    2,
                ),
                "empty_tables": (
                    empty_tables
                ),
            },

            "table_quality": {
                "reference_table_count": (
                    reference_table_count
                ),
                "extracted_table_count": (
                    extracted_table_count
                ),
                "detected_tables": (
                    detected_tables
                ),
                "missing_tables": (
                    missing_tables
                ),
                "extra_tables": (
                    extra_tables
                ),
                "table_precision": (
                    round(
                        precision,
                        4,
                    )
                    if isinstance(
                        precision,
                        (int, float),
                    )
                    else precision
                ),
                "table_recall": (
                    round(
                        recall,
                        4,
                    )
                    if isinstance(
                        recall,
                        (int, float),
                    )
                    else recall
                ),
                "table_f1_score": (
                    round(
                        f1_score,
                        4,
                    )
                    if isinstance(
                        f1_score,
                        (int, float),
                    )
                    else f1_score
                ),
                "table_coverage_percent": (
                    round(
                        table_coverage,
                        2,
                    )
                    if isinstance(
                        table_coverage,
                        (int, float),
                    )
                    else table_coverage
                ),
                "teds_score": (
                    teds_score_percent
                ),
                "spatial_detection_supported": (
                    spatial_detection_supported
                ),
                "table_iou_threshold": (
                    TABLE_IOU_THRESHOLD
                    if spatial_detection_supported
                    else "N/A/Unsupported"
                ),
            },
        }