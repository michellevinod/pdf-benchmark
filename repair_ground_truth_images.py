import json
from pathlib import Path

import fitz


PDF_PATH = Path(
    "benchmark_dataset/PDF_Benchmarking_Tester.pdf"
)

GROUND_TRUTH_PATH = Path(
    "benchmark_dataset/ground_truth.json"
)

BACKUP_PATH = Path(
    "benchmark_dataset/ground_truth_before_image_bbox_repair.json"
)


def is_valid_bbox(bbox: list[float]) -> bool:
    """
    Returns True when the bounding box has positive
    width and height.
    """

    if not bbox or len(bbox) != 4:
        return False

    x0, y0, x1, y1 = bbox

    return (
        x1 > x0
        and y1 > y0
    )


def main():

    print("=" * 60)
    print("Ground Truth Image BBox Repair")
    print("=" * 60)

    # --------------------------------------------------
    # Load frozen ground truth
    # --------------------------------------------------

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        ground_truth = json.load(file)

    # --------------------------------------------------
    # Backup BEFORE modifying anything
    # --------------------------------------------------

    if not BACKUP_PATH.exists():

        BACKUP_PATH.write_text(
            json.dumps(
                ground_truth,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(
            f"Backup created: {BACKUP_PATH}"
        )

    else:

        print(
            f"Backup already exists: {BACKUP_PATH}"
        )

    # --------------------------------------------------
    # Open original PDF
    # --------------------------------------------------

    document = fitz.open(
        PDF_PATH
    )

    repaired = 0
    already_valid = 0
    unresolved = 0
    multiple_occurrences = 0

    pages = ground_truth.get(
        "pages",
        [],
    )

    # --------------------------------------------------
    # Repair image placements
    # --------------------------------------------------

    for page_index, page_data in enumerate(
        pages
    ):

        pdf_page = document[
            page_index
        ]

        images = page_data.get(
            "images",
            [],
        )

        repaired_images = []

        for image in images:

            xref = image.get(
                "xref"
            )

            existing_bbox = image.get(
                "bbox",
                [],
            )

            # Keep an already valid reference bbox.
            if is_valid_bbox(
                existing_bbox
            ):

                already_valid += 1
                repaired_images.append(
                    image
                )
                continue

            if not xref:

                print(
                    f"WARNING: page {page_index + 1}: "
                    "image has no xref."
                )

                unresolved += 1
                repaired_images.append(
                    image
                )
                continue

            try:

                rects = (
                    pdf_page.get_image_rects(
                        xref
                    )
                )

            except Exception as exc:

                print(
                    f"WARNING: page {page_index + 1}, "
                    f"xref {xref}: {exc}"
                )

                unresolved += 1
                repaired_images.append(
                    image
                )
                continue

            if not rects:

                print(
                    f"WARNING: page {page_index + 1}, "
                    f"xref {xref}: no placement rectangle."
                )

                unresolved += 1
                repaired_images.append(
                    image
                )
                continue

            # An image xref can appear more than once
            # on the same PDF page.
            if len(rects) > 1:

                multiple_occurrences += (
                    len(rects) - 1
                )

            for occurrence_index, rect in enumerate(
                rects,
                start=1,
            ):

                repaired_image = dict(
                    image
                )

                repaired_image[
                    "bbox"
                ] = [
                    float(rect.x0),
                    float(rect.y0),
                    float(rect.x1),
                    float(rect.y1),
                ]

                repaired_image[
                    "page_number"
                ] = (
                    page_index + 1
                )

                if len(rects) > 1:

                    original_id = (
                        repaired_image.get(
                            "image_id",
                            (
                                f"p{page_index + 1}"
                                f"_xref{xref}"
                            ),
                        )
                    )

                    repaired_image[
                        "image_id"
                    ] = (
                        f"{original_id}"
                        f"_occ{occurrence_index}"
                    )

                repaired_images.append(
                    repaired_image
                )

                repaired += 1

        page_data[
            "images"
        ] = repaired_images

    document.close()

    # --------------------------------------------------
    # Recalculate image statistics ONLY
    # --------------------------------------------------

    all_images = [
        image
        for page in pages
        for image in page.get(
            "images",
            [],
        )
    ]

    valid_images = [
        image
        for image in all_images
        if is_valid_bbox(
            image.get(
                "bbox",
                [],
            )
        )
    ]

    pages_with_images = sum(
        1
        for page in pages
        if page.get(
            "images",
            []
        )
    )

    # Update existing image-related document statistics
    # if those fields exist.

    statistics = ground_truth.get(
        "statistics"
    )

    if isinstance(
        statistics,
        dict,
    ):

        if "image_count" in statistics:
            statistics[
                "image_count"
            ] = len(
                all_images
            )

        if "pages_with_images" in statistics:
            statistics[
                "pages_with_images"
            ] = pages_with_images

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    invalid_after_repair = []

    for page_index, page in enumerate(
        pages,
        start=1,
    ):

        for image in page.get(
            "images",
            [],
        ):

            if not is_valid_bbox(
                image.get(
                    "bbox",
                    [],
                )
            ):

                invalid_after_repair.append(
                    {
                        "page": page_index,
                        "image_id": image.get(
                            "image_id"
                        ),
                        "xref": image.get(
                            "xref"
                        ),
                        "bbox": image.get(
                            "bbox"
                        ),
                    }
                )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    GROUND_TRUTH_PATH.write_text(
        json.dumps(
            ground_truth,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("Repair Summary")
    print("=" * 60)

    print(
        f"Image occurrences stored : {len(all_images)}"
    )

    print(
        f"Valid image bboxes       : {len(valid_images)}"
    )

    print(
        f"Repaired occurrences     : {repaired}"
    )

    print(
        f"Already valid            : {already_valid}"
    )

    print(
        f"Additional occurrences   : {multiple_occurrences}"
    )

    print(
        f"Pages with images        : {pages_with_images}"
    )

    print(
        f"Unresolved during repair : {unresolved}"
    )

    print(
        f"Invalid bboxes remaining : "
        f"{len(invalid_after_repair)}"
    )

    if invalid_after_repair:

        print(
            "\nUnresolved images:"
        )

        for item in (
            invalid_after_repair[:20]
        ):

            print(
                item
            )

    else:

        print(
            "\nSUCCESS: All stored image occurrences "
            "have valid bounding boxes."
        )


if __name__ == "__main__":
    main()