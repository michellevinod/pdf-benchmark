from typing import Any


class LayoutMetrics:
    """
    Evaluates document layout extraction quality.

    Metrics include:
    - extracted/reference block counts
    - matched, missing and extra blocks
    - spatial precision
    - spatial recall
    - spatial F1 score
    - mean IoU
    - spatial match rate

    Layout blocks are matched page-by-page using
    bounding-box Intersection over Union (IoU).
    """

    IOU_THRESHOLD = 0.5

    @staticmethod
    def _extract_bbox(
        block: dict[str, Any],
        page_height: float | None = None,
    ) -> list[float] | None:
        """
        Converts supported bbox formats to:

        [x0, y0, x1, y1]

        Supports:
        - [x0, y0, x1, y1]
        - {l, t, r, b}
        - {x0, y0, x1, y1}

        Docling BOTTOMLEFT coordinates are converted
        to TOPLEFT when page height is available.
        """

        bbox = block.get("bbox")

        if bbox is None:
            return None

        # ---------------------------------------------
        # List bbox
        # ---------------------------------------------

        if (
            isinstance(bbox, list)
            and len(bbox) == 4
        ):

            try:

                x0, y0, x1, y1 = [
                    float(value)
                    for value in bbox
                ]

                return [
                    min(x0, x1),
                    min(y0, y1),
                    max(x0, x1),
                    max(y0, y1),
                ]

            except (TypeError, ValueError):
                return None

        # ---------------------------------------------
        # Dictionary bbox
        # ---------------------------------------------

        if isinstance(bbox, dict):

            # x0/y0/x1/y1 format

            if all(
                key in bbox
                for key in (
                    "x0",
                    "y0",
                    "x1",
                    "y1",
                )
            ):

                try:

                    x0 = float(
                        bbox["x0"]
                    )

                    y0 = float(
                        bbox["y0"]
                    )

                    x1 = float(
                        bbox["x1"]
                    )

                    y1 = float(
                        bbox["y1"]
                    )

                    return [
                        min(x0, x1),
                        min(y0, y1),
                        max(x0, x1),
                        max(y0, y1),
                    ]

                except (TypeError, ValueError):
                    return None

            # Docling l/t/r/b format

            if all(
                key in bbox
                for key in (
                    "l",
                    "t",
                    "r",
                    "b",
                )
            ):

                try:

                    left = float(
                        bbox["l"]
                    )

                    top = float(
                        bbox["t"]
                    )

                    right = float(
                        bbox["r"]
                    )

                    bottom = float(
                        bbox["b"]
                    )

                    coord_origin = str(
                        bbox.get(
                            "coord_origin",
                            "",
                        )
                    ).upper()

                    if (
                        coord_origin
                        == "BOTTOMLEFT"
                        and page_height
                        is not None
                    ):

                        converted_top = (
                            page_height
                            - top
                        )

                        converted_bottom = (
                            page_height
                            - bottom
                        )

                        return [
                            min(
                                left,
                                right,
                            ),
                            min(
                                converted_top,
                                converted_bottom,
                            ),
                            max(
                                left,
                                right,
                            ),
                            max(
                                converted_top,
                                converted_bottom,
                            ),
                        ]

                    return [
                        min(
                            left,
                            right,
                        ),
                        min(
                            top,
                            bottom,
                        ),
                        max(
                            left,
                            right,
                        ),
                        max(
                            top,
                            bottom,
                        ),
                    ]

                except (TypeError, ValueError):
                    return None

        return None

    @staticmethod
    def _area(
        box: list[float],
    ) -> float:

        x0, y0, x1, y1 = box

        return (
            max(
                0.0,
                x1 - x0,
            )
            * max(
                0.0,
                y1 - y0,
            )
        )

    @staticmethod
    def _iou(
        box1: list[float],
        box2: list[float],
    ) -> float:
        """
        Calculates Intersection over Union.
        """

        intersection_x0 = max(
            box1[0],
            box2[0],
        )

        intersection_y0 = max(
            box1[1],
            box2[1],
        )

        intersection_x1 = min(
            box1[2],
            box2[2],
        )

        intersection_y1 = min(
            box1[3],
            box2[3],
        )

        intersection_width = max(
            0.0,
            intersection_x1
            - intersection_x0,
        )

        intersection_height = max(
            0.0,
            intersection_y1
            - intersection_y0,
        )

        intersection_area = (
            intersection_width
            * intersection_height
        )

        area1 = LayoutMetrics._area(
            box1
        )

        area2 = LayoutMetrics._area(
            box2
        )

        union_area = (
            area1
            + area2
            - intersection_area
        )

        if union_area <= 0:
            return 0.0

        return (
            intersection_area
            / union_area
        )

    @staticmethod
    def _match_page(
        reference_blocks: list[
            dict[str, Any]
        ],
        extracted_blocks: list[
            dict[str, Any]
        ],
        page_height: float | None = None,
    ) -> tuple[
        int,
        list[float],
    ]:
        """
        Performs greedy one-to-one spatial matching.

        The highest-IoU pairs are selected first,
        provided IoU >= IOU_THRESHOLD.
        """

        reference_boxes = []

        for block in reference_blocks:

            box = (
                LayoutMetrics._extract_bbox(
                    block
                )
            )

            if (
                box is not None
                and LayoutMetrics._area(
                    box
                ) > 0
            ):

                reference_boxes.append(
                    box
                )

        extracted_boxes = []

        for block in extracted_blocks:

            box = (
                LayoutMetrics._extract_bbox(
                    block,
                    page_height,
                )
            )

            if (
                box is not None
                and LayoutMetrics._area(
                    box
                ) > 0
            ):

                extracted_boxes.append(
                    box
                )

        candidates = []

        for (
            reference_index,
            reference_box,
        ) in enumerate(
            reference_boxes
        ):

            for (
                extracted_index,
                extracted_box,
            ) in enumerate(
                extracted_boxes
            ):

                iou = (
                    LayoutMetrics._iou(
                        reference_box,
                        extracted_box,
                    )
                )

                if (
                    iou
                    >= LayoutMetrics.IOU_THRESHOLD
                ):

                    candidates.append(
                        (
                            iou,
                            reference_index,
                            extracted_index,
                        )
                    )

        # Highest IoU first

        candidates.sort(
            key=lambda candidate: (
                candidate[0]
            ),
            reverse=True,
        )

        used_reference = set()
        used_extracted = set()

        matched_ious = []

        for (
            iou,
            reference_index,
            extracted_index,
        ) in candidates:

            if (
                reference_index
                in used_reference
            ):
                continue

            if (
                extracted_index
                in used_extracted
            ):
                continue

            used_reference.add(
                reference_index
            )

            used_extracted.add(
                extracted_index
            )

            matched_ious.append(
                iou
            )

        return (
            len(
                matched_ious
            ),
            matched_ious,
        )

    @staticmethod
    def evaluate(
        normalized_document: dict[
            str,
            Any,
        ],
        reference_layout_blocks: (
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
        reference_layout_count: (
            int
            | None
        ) = None,
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        extracted_layout_by_page = [
            page.get(
                "layout_blocks",
                [],
            )
            for page in pages
        ]

        total_layout_blocks = sum(
            len(page_blocks)
            for page_blocks
            in extracted_layout_by_page
        )

        pages_with_layout = sum(
            1
            for page_blocks
            in extracted_layout_by_page
            if page_blocks
        )

        ocr_pages = sum(
            1
            for page in pages
            if str(
                page.get(
                    "ocr_text",
                    "",
                )
            ).strip()
        )

        page_count = len(
            pages
        )

        average_layout_blocks_per_page = (
            total_layout_blocks
            / page_count
            if page_count
            else 0.0
        )

        # ---------------------------------------------
        # Reference count
        # ---------------------------------------------

        if (
            reference_layout_blocks
            is not None
        ):

            reference_layout_count = sum(
                len(
                    page_blocks
                )
                for page_blocks
                in reference_layout_blocks
            )

        if (
            reference_layout_count
            is None
        ):
            reference_layout_count = 0

        # ---------------------------------------------
        # Spatial matching
        # ---------------------------------------------

        matched_blocks = 0

        all_matched_ious = []

        valid_reference_boxes = 0
        valid_extracted_boxes = 0

        if (
            reference_layout_blocks
            is not None
        ):

            total_pages = max(
                len(
                    reference_layout_blocks
                ),
                len(
                    extracted_layout_by_page
                ),
            )

            for page_index in range(
                total_pages
            ):

                reference_page = (
                    reference_layout_blocks[
                        page_index
                    ]
                    if page_index
                    < len(
                        reference_layout_blocks
                    )
                    else []
                )

                extracted_page = (
                    extracted_layout_by_page[
                        page_index
                    ]
                    if page_index
                    < len(
                        extracted_layout_by_page
                    )
                    else []
                )

                # -------------------------------------
                # Page dimensions
                # -------------------------------------

                page_metadata = (
                    pages[
                        page_index
                    ].get(
                        "metadata",
                        {},
                    )
                    if page_index
                    < len(
                        pages
                    )
                    else {}
                )

                page_height = (
                    page_metadata.get(
                        "height"
                    )
                )

                # -------------------------------------
                # Count valid reference boxes
                # -------------------------------------

                for block in (
                    reference_page
                ):

                    box = (
                        LayoutMetrics._extract_bbox(
                            block
                        )
                    )

                    if (
                        box is not None
                        and LayoutMetrics._area(
                            box
                        ) > 0
                    ):

                        valid_reference_boxes += 1

                # -------------------------------------
                # Count valid extracted boxes
                # -------------------------------------

                for block in (
                    extracted_page
                ):

                    box = (
                        LayoutMetrics._extract_bbox(
                            block,
                            page_height,
                        )
                    )

                    if (
                        box is not None
                        and LayoutMetrics._area(
                            box
                        ) > 0
                    ):

                        valid_extracted_boxes += 1

                # -------------------------------------
                # Spatial page matching
                # -------------------------------------

                (
                    page_matches,
                    page_ious,
                ) = (
                    LayoutMetrics._match_page(
                        reference_page,
                        extracted_page,
                        page_height,
                    )
                )

                matched_blocks += (
                    page_matches
                )

                all_matched_ious.extend(
                    page_ious
                )

        # ---------------------------------------------
        # Precision / Recall / F1
        # ---------------------------------------------

        precision = (
            matched_blocks
            / valid_extracted_boxes
            if valid_extracted_boxes
            else 0.0
        )

        recall = (
            matched_blocks
            / valid_reference_boxes
            if valid_reference_boxes
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
            if (
                precision
                + recall
            )
            else 0.0
        )

        mean_iou = (
            sum(
                all_matched_ious
            )
            / len(
                all_matched_ious
            )
            if all_matched_ious
            else 0.0
        )

        missing_blocks = max(
            0,
            valid_reference_boxes
            - matched_blocks,
        )

        extra_blocks = max(
            0,
            valid_extracted_boxes
            - matched_blocks,
        )

        spatial_match_rate = (
            matched_blocks
            / valid_reference_boxes
            * 100
            if valid_reference_boxes
            else 0.0
        )

        # ---------------------------------------------
        # Spatial support
        # ---------------------------------------------

        spatial_supported = (
            valid_reference_boxes > 0
            and valid_extracted_boxes > 0
        )

        if spatial_supported:

            precision_result = round(
                precision,
                4,
            )

            recall_result = round(
                recall,
                4,
            )

            f1_result = round(
                f1_score,
                4,
            )

            mean_iou_result = round(
                mean_iou,
                4,
            )

            match_rate_result = round(
                spatial_match_rate,
                2,
            )

            spatial_match_result = round(
                mean_iou
                * 100,
                2,
            )

            matched_result = (
                matched_blocks
            )

            missing_result = (
                missing_blocks
            )

            extra_result = (
                extra_blocks
            )

        else:

            precision_result = (
                "N/A/Unsupported"
            )

            recall_result = (
                "N/A/Unsupported"
            )

            f1_result = (
                "N/A/Unsupported"
            )

            mean_iou_result = (
                "N/A/Unsupported"
            )

            match_rate_result = (
                "N/A/Unsupported"
            )

            spatial_match_result = (
                "N/A/Unsupported"
            )

            matched_result = (
                "N/A/Unsupported"
            )

            missing_result = (
                "N/A/Unsupported"
            )

            extra_result = (
                "N/A/Unsupported"
            )

        # ---------------------------------------------
        # Reading order
        # ---------------------------------------------

        reading_order_accuracy = (
            "N/A/Unsupported"
        )

        return {
            "layout_statistics": {
                "layout_block_count": (
                    total_layout_blocks
                ),
                "pages_with_layout": (
                    pages_with_layout
                ),
                "ocr_pages": (
                    ocr_pages
                ),
                "average_layout_blocks_per_page": round(
                    average_layout_blocks_per_page,
                    2,
                ),
                "valid_extracted_bboxes": (
                    valid_extracted_boxes
                ),
            },

            "layout_quality": {
                "reference_block_count": (
                    reference_layout_count
                ),
                "valid_reference_bboxes": (
                    valid_reference_boxes
                ),
                "extracted_block_count": (
                    total_layout_blocks
                ),
                "matched_layout_blocks": (
                    matched_result
                ),
                "missing_layout_blocks": (
                    missing_result
                ),
                "extra_layout_blocks": (
                    extra_result
                ),
                "layout_precision": (
                    precision_result
                ),
                "layout_recall": (
                    recall_result
                ),
                "layout_f1_score": (
                    f1_result
                ),
                "mean_iou": (
                    mean_iou_result
                ),
                "layout_match_rate_percent": (
                    match_rate_result
                ),
                "spatial_block_matching": (
                    spatial_match_result
                ),
                "iou_threshold": (
                    LayoutMetrics.IOU_THRESHOLD
                ),
                "reading_order_accuracy": (
                    reading_order_accuracy
                ),
            },
        }