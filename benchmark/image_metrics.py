from typing import Any


class ImageMetrics:
    """
    Evaluates image extraction quality against ground-truth
    image regions using page-level bounding-box matching.

    Metrics:
    - extracted/reference image counts
    - matched, missing and extra images
    - precision
    - recall
    - F1 score
    - mean IoU
    - image detection match rate
    """

    IOU_THRESHOLD = 0.5

    @staticmethod
    def _extract_bbox(
        item: dict[str, Any],
        page_height: float | None = None,
    ) -> list[float] | None:
        """
        Converts supported bbox formats to:
        [x0, y0, x1, y1]

        Supports:
        - [x0, y0, x1, y1]
        - {l, t, r, b}
        - {x0, y0, x1, y1}
        """

        bbox = item.get("bbox")

        if bbox is None:
            return None

        if isinstance(bbox, list) and len(bbox) == 4:
            try:
                return [float(value) for value in bbox]
            except (TypeError, ValueError):
                return None

        if isinstance(bbox, dict):

            if all(
                key in bbox
                for key in ("x0", "y0", "x1", "y1")
            ):
                try:
                    return [
                        float(bbox["x0"]),
                        float(bbox["y0"]),
                        float(bbox["x1"]),
                        float(bbox["y1"]),
                    ]
                except (TypeError, ValueError):
                    return None

            if all(
                key in bbox
                for key in ("l", "t", "r", "b")
            ):
                try:
                    left = float(bbox["l"])
                    top = float(bbox["t"])
                    right = float(bbox["r"])
                    bottom = float(bbox["b"])

                    coord_origin = str(
                        bbox.get(
                            "coord_origin",
                            "",
                        )
                    ).upper()

                    # Docling uses a bottom-left coordinate origin.
                    # Ground truth / PyMuPDF uses top-left coordinates.
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

                        return [
                            min(left, right),
                            min(
                                converted_top,
                                converted_bottom,
                            ),
                            max(left, right),
                            max(
                                converted_top,
                                converted_bottom,
                            ),
                        ]

                    return [
                        min(left, right),
                        min(top, bottom),
                        max(left, right),
                        max(top, bottom),
                    ]

                except (TypeError, ValueError):
                    return None

        return None

    @staticmethod
    def _normalize_box(
        box: list[float],
    ) -> list[float]:

        x0, y0, x1, y1 = box

        return [
            min(x0, x1),
            min(y0, y1),
            max(x0, x1),
            max(y0, y1),
        ]

    @staticmethod
    def _area(
        box: list[float],
    ) -> float:

        x0, y0, x1, y1 = (
            ImageMetrics._normalize_box(box)
        )

        return max(
            0.0,
            x1 - x0,
        ) * max(
            0.0,
            y1 - y0,
        )

    @staticmethod
    def _iou(
        box1: list[float],
        box2: list[float],
    ) -> float:
        """
        Intersection over Union.
        """

        box1 = ImageMetrics._normalize_box(box1)
        box2 = ImageMetrics._normalize_box(box2)

        x0 = max(box1[0], box2[0])
        y0 = max(box1[1], box2[1])
        x1 = min(box1[2], box2[2])
        y1 = min(box1[3], box2[3])

        intersection = max(
            0.0,
            x1 - x0,
        ) * max(
            0.0,
            y1 - y0,
        )

        area1 = ImageMetrics._area(box1)
        area2 = ImageMetrics._area(box2)

        union = (
            area1
            + area2
            - intersection
        )

        if union <= 0:
            return 0.0

        return intersection / union

    @staticmethod
    def _match_page(
        reference_images: list[dict[str, Any]],
        extracted_images: list[dict[str, Any]],
        page_height: float | None = None,
    ) -> tuple[int, list[float]]:
        """
        Greedy one-to-one matching using the highest IoU
        above the configured threshold.
        """

        reference_boxes = []

        for image in reference_images:

            box = ImageMetrics._extract_bbox(
                image
            )

            if (
                box is not None
                and ImageMetrics._area(box) > 0
            ):
                reference_boxes.append(
                    box
                )

        extracted_boxes = []

        for image in extracted_images:

            box = ImageMetrics._extract_bbox(
                image,
                page_height,
            )

            if (
                box is not None
                and ImageMetrics._area(box) > 0
            ):
                extracted_boxes.append(
                    box
                )

        candidates = []

        for reference_index, reference_box in enumerate(
            reference_boxes
        ):

            for extracted_index, extracted_box in enumerate(
                extracted_boxes
            ):

                iou = ImageMetrics._iou(
                    reference_box,
                    extracted_box,
                )

                if iou >= ImageMetrics.IOU_THRESHOLD:

                    candidates.append(
                        (
                            iou,
                            reference_index,
                            extracted_index,
                        )
                    )

        candidates.sort(
            key=lambda item: item[0],
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

            if reference_index in used_reference:
                continue

            if extracted_index in used_extracted:
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
            len(matched_ious),
            matched_ious,
        )

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
        reference_images: (
            list[list[dict[str, Any]]]
            | None
        ) = None,
        reference_image_count: int | None = None,
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        extracted_images_by_page = [
            page.get("images", [])
            for page in pages
        ]

        total_images = sum(
            len(page_images)
            for page_images in extracted_images_by_page
        )

        total_figures = sum(
            len(page.get("figures", []))
            for page in pages
        )

        pages_with_images = sum(
            1
            for page_images in extracted_images_by_page
            if page_images
        )

        page_count = len(pages)

        average_images_per_page = (
            total_images / page_count
            if page_count
            else 0.0
        )

        if reference_images is not None:

            reference_image_count = sum(
                len(page_images)
                for page_images in reference_images
            )

        if reference_image_count is None:
            reference_image_count = 0

        # --------------------------------------------
        # Spatial matching
        # --------------------------------------------

        matched_images = 0
        all_matched_ious = []

        valid_reference_boxes = 0
        valid_extracted_boxes = 0

        if reference_images is not None:

            total_pages = max(
                len(reference_images),
                len(extracted_images_by_page),
            )

            for page_index in range(total_pages):

                reference_page = (
                    reference_images[page_index]
                    if page_index < len(reference_images)
                    else []
                )

                extracted_page = (
                    extracted_images_by_page[page_index]
                    if page_index < len(extracted_images_by_page)
                    else []
                )

                page_metadata = (
                    pages[page_index].get(
                        "metadata",
                        {},
                    )
                    if page_index < len(pages)
                    else {}
                )

                page_height = page_metadata.get(
                    "height"
                )

                valid_reference_boxes += sum(
                    1
                    for item in reference_page
                    if (
                        (
                            box := ImageMetrics._extract_bbox(
                                item
                            )
                        )
                        is not None
                        and ImageMetrics._area(box) > 0
                    )
                )

                valid_extracted_boxes += sum(
                    1
                    for item in extracted_page
                    if (
                        (
                            box := ImageMetrics._extract_bbox(
                                item,
                                page_height,
                            )
                        )
                        is not None
                        and ImageMetrics._area(box) > 0
                    )
                )

                page_matches, page_ious = (
                    ImageMetrics._match_page(
                        reference_page,
                        extracted_page,
                        page_height,
                    )
                )

                matched_images += page_matches

                all_matched_ious.extend(
                    page_ious
                )

        # --------------------------------------------
        # Detection quality
        # --------------------------------------------

        if valid_extracted_boxes:

            precision = (
                matched_images
                / valid_extracted_boxes
            )

        else:
            precision = 0.0

        if valid_reference_boxes:

            recall = (
                matched_images
                / valid_reference_boxes
            )

        else:
            recall = 0.0

        if precision + recall:

            f1_score = (
                2
                * precision
                * recall
                / (
                    precision
                    + recall
                )
            )

        else:
            f1_score = 0.0

        mean_iou = (
            sum(all_matched_ious)
            / len(all_matched_ious)
            if all_matched_ious
            else 0.0
        )

        missing_images = max(
            0,
            valid_reference_boxes
            - matched_images,
        )

        extra_images = max(
            0,
            valid_extracted_boxes
            - matched_images,
        )

        match_rate = (
            matched_images
            / valid_reference_boxes
            * 100
            if valid_reference_boxes
            else 0.0
        )

        # If a parser exposes no usable image regions,
        # spatial evaluation is genuinely unsupported.

        spatial_supported = (
            valid_extracted_boxes > 0
            and valid_reference_boxes > 0
        )

        if spatial_supported:

            spatial_match = round(
                mean_iou * 100,
                2,
            )

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
                match_rate,
                2,
            )

        else:

            spatial_match = "N/A/Unsupported"
            precision_result = "N/A/Unsupported"
            recall_result = "N/A/Unsupported"
            f1_result = "N/A/Unsupported"
            mean_iou_result = "N/A/Unsupported"
            match_rate_result = "N/A/Unsupported"

        return {
            "image_statistics": {
                "extracted_image_count": total_images,
                "figure_count": total_figures,
                "pages_with_images": pages_with_images,
                "average_images_per_page": round(
                    average_images_per_page,
                    2,
                ),
                "valid_extracted_bboxes": (
                    valid_extracted_boxes
                ),
            },

            "image_quality": {
                "reference_image_count": (
                    reference_image_count
                ),
                "valid_reference_bboxes": (
                    valid_reference_boxes
                ),
                "extracted_image_count": (
                    total_images
                ),
                "matched_images": (
                    matched_images
                    if spatial_supported
                    else "N/A/Unsupported"
                ),
                "missing_images": (
                    missing_images
                    if spatial_supported
                    else "N/A/Unsupported"
                ),
                "extra_images": (
                    extra_images
                    if spatial_supported
                    else "N/A/Unsupported"
                ),
                "image_precision": (
                    precision_result
                ),
                "image_recall": (
                    recall_result
                ),
                "image_f1_score": (
                    f1_result
                ),
                "mean_iou": (
                    mean_iou_result
                ),
                "image_match_rate_percent": (
                    match_rate_result
                ),
                "structural_image_match": (
                    spatial_match
                ),
                "iou_threshold": (
                    ImageMetrics.IOU_THRESHOLD
                ),
            },
        }