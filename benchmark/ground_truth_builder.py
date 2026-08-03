import argparse
import csv
import json
import sys
from pathlib import Path

import fitz


DEFAULT_PDF_PATH = "benchmark_dataset/PDF_Benchmarking_Tester.pdf"
DEFAULT_GROUND_TRUTH_PATH = "benchmark_dataset/ground_truth.json"
DEFAULT_VALIDATION_PATH = "benchmark_dataset/ground_truth_validation.json"
DEFAULT_REVIEW_PATH = "benchmark_dataset/ground_truth_review.csv"
EXPECTED_PAGE_COUNT = 62


def _bbox_to_list(value):
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
    return [0.0, 0.0, 0.0, 0.0]


def _safe_text(value):
    if value is None:
        return ""
    return str(value)


class GroundTruthBuilder:
    @staticmethod
    def _build_text_blocks(page, page_number):
        blocks = page.get_text("blocks")
        text_blocks = []

        for index, block in enumerate(blocks, start=1):
            if len(block) < 5:
                continue

            text = str(block[4]).strip()
            if not text:
                continue

            bbox = _bbox_to_list(block[:4])
            text_blocks.append(
                {
                    "block_id": f"p{page_number}_b{index}",
                    "text": text,
                    "bbox": bbox,
                    "block_type": "text",
                    "reading_order": index,
                    "page_number": page_number,
                }
            )

        return text_blocks

    @staticmethod
    def _build_tables(page, page_number):
        tables = []
        table_objects = page.find_tables().tables

        for table_index, table in enumerate(table_objects, start=1):
            grid = table.extract()
            row_count = int(table.row_count)
            column_count = int(table.col_count)
            cell_bboxes = list(table.cells) if hasattr(table, "cells") and table.cells else []
            cells = []

            for row_index in range(row_count):
                for col_index in range(column_count):
                    cell_text = ""
                    if row_index < len(grid) and col_index < len(grid[row_index]):
                        raw_value = grid[row_index][col_index]
                        cell_text = "" if raw_value is None else str(raw_value)

                    index = row_index * column_count + col_index
                    bbox = (
                        _bbox_to_list(cell_bboxes[index])
                        if index < len(cell_bboxes)
                        else [0.0, 0.0, 0.0, 0.0]
                    )

                    cells.append(
                        {
                            "row": row_index,
                            "column": col_index,
                            "text": cell_text,
                            "bbox": bbox,
                        }
                    )

            tables.append(
                {
                    "table_id": f"p{page_number}_t{table_index}",
                    "bbox": _bbox_to_list(table.bbox),
                    "row_count": row_count,
                    "column_count": column_count,
                    "cells": cells,
                    "verified": False,
                    "page_number": page_number,
                }
            )

        return tables

    @staticmethod
    def _build_images(document, page, page_number):
        images = []
        image_xrefs = page.get_images(full=True)

        for image_index, image_spec in enumerate(image_xrefs, start=1):
            xref = image_spec[0] if isinstance(image_spec, (list, tuple)) else image_spec
            rects = page.get_image_rects(xref)
            bbox = _bbox_to_list(rects[0]) if rects else [0.0, 0.0, 0.0, 0.0]
            image_info = document.extract_image(int(xref)) or {}
            image_width = image_info.get("width", 0)
            image_height = image_info.get("height", 0)

            images.append(
                {
                    "image_id": f"p{page_number}_i{image_index}",
                    "xref": int(xref),
                    "bbox": bbox,
                    "width": int(image_width),
                    "height": int(image_height),
                    "semantic_type": "unknown",
                    "verified": False,
                    "page_number": page_number,
                }
            )

        return images

    @staticmethod
    def _build_layout_blocks(page, page_number):
        blocks = page.get_text("blocks")
        layout_blocks = []

        for block_index, block in enumerate(blocks, start=1):
            if len(block) < 5:
                continue

            block_type = "text"
            block_text = str(block[4]).strip()
            if not block_text:
                block_type = "empty"

            layout_blocks.append(
                {
                    "block_id": f"p{page_number}_b{block_index}",
                    "page_number": page_number,
                    "block_type": block_type,
                    "bbox": _bbox_to_list(block[:4]),
                    "text": block_text,
                    "reading_order": block_index,
                }
            )

        return layout_blocks

    @staticmethod
    def _review_reason(page_page):
        reasons = []
        if page_page["tables"]:
            reasons.append("table_detection")
        if len(page_page["images"]) > 0:
            reasons.append("image_content")
        if len(page_page["layout_blocks"]) > 25:
            reasons.append("complex_layout")
        if page_page["requires_ocr_review"]:
            reasons.append("ocr_review")
        if page_page["layout"]["block_count"] > 20:
            reasons.append("multi_column")
        return "; ".join(reasons) if reasons else "standard" 

    @staticmethod
    def _validate_ground_truth(document):
        issues = []
        pages = document.get("pages", [])

        if len(pages) != EXPECTED_PAGE_COUNT:
            issues.append(
                f"Expected {EXPECTED_PAGE_COUNT} pages, got {len(pages)}."
            )

        page_numbers = [page.get("page_number") for page in pages]
        expected_numbers = list(range(1, EXPECTED_PAGE_COUNT + 1))
        if page_numbers != expected_numbers:
            issues.append("Page numbering is not exactly 1 through 62.")

        if len(set(page_numbers)) != len(page_numbers):
            issues.append("Duplicate page numbers detected.")

        stats = document.get("statistics", {})
        if stats.get("table_count") != sum(len(page.get("tables", [])) for page in pages):
            issues.append("Document table_count does not match page totals.")

        if stats.get("image_occurrence_count") != sum(len(page.get("images", [])) for page in pages):
            issues.append("Document image_occurrence_count does not match page totals.")

        if stats.get("layout_block_count") != sum(len(page.get("layout_blocks", [])) for page in pages):
            issues.append("Document layout_block_count does not match page totals.")

        char_total = sum(len(page.get("text", "")) for page in pages)
        if stats.get("character_count") != char_total:
            issues.append("Document character_count does not match page totals.")

        word_total = sum(len(page.get("text", "").split()) for page in pages)
        if stats.get("word_count") != word_total:
            issues.append("Document word_count does not match page totals.")

        line_total = sum(len(page.get("text", "").splitlines()) for page in pages)
        if stats.get("line_count") != line_total:
            issues.append("Document line_count does not match page totals.")

        for page in pages:
            for block in page.get("text_blocks", []):
                if not isinstance(block.get("bbox"), list) or len(block["bbox"]) != 4:
                    issues.append(f"Invalid bbox on page {page['page_number']} text block {block.get('block_id')}." )
            for table in page.get("tables", []):
                if not isinstance(table.get("bbox"), list) or len(table["bbox"]) != 4:
                    issues.append(f"Invalid bbox on page {page['page_number']} table {table.get('table_id')}.")
            for image in page.get("images", []):
                if not isinstance(image.get("bbox"), list) or len(image["bbox"]) != 4:
                    issues.append(f"Invalid bbox on page {page['page_number']} image {image.get('image_id')}.")

            reading_order = page.get("layout", {}).get("reading_order", [])
            block_ids = {block.get("block_id") for block in page.get("layout_blocks", [])}
            for block_id in reading_order:
                if block_id not in block_ids:
                    issues.append(
                        f"Reading-order block {block_id} is missing from page {page['page_number']} layout blocks."
                    )

        return issues

    @staticmethod
    def _save_review_csv(pages, output_path):
        fieldnames = [
            "page_number",
            "text_block_count",
            "table_count",
            "image_count",
            "layout_block_count",
            "requires_ocr_review",
            "review_reason",
            "verified",
        ]

        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for page in pages:
                row = {
                    "page_number": page["page_number"],
                    "text_block_count": len(page.get("text_blocks", [])),
                    "table_count": len(page.get("tables", [])),
                    "image_count": len(page.get("images", [])),
                    "layout_block_count": page["layout"]["block_count"],
                    "requires_ocr_review": str(page.get("requires_ocr_review", False)).lower(),
                    "review_reason": GroundTruthBuilder._review_reason(page),
                    "verified": str(page.get("verification", {}).get("text_verified", False)).lower(),
                }
                writer.writerow(row)

    @staticmethod
    def _save_validation_report(pages, issues, output_path):
        pages_requiring_review = []
        for page in pages:
            if (
                page.get("requires_ocr_review")
                or page.get("tables")
                or page.get("images")
                or page.get("layout", {}).get("block_count", 0) > 20
                or len(page.get("text_blocks", [])) == 0
            ):
                pages_requiring_review.append(page["page_number"])

        summary = {
            "page_count": len(pages),
            "table_count": sum(len(page.get("tables", [])) for page in pages),
            "image_count": sum(len(page.get("images", [])) for page in pages),
            "layout_block_count": sum(len(page.get("layout_blocks", [])) for page in pages),
            "pages_requiring_ocr_review": sum(1 for page in pages if page.get("requires_ocr_review")),
            "pages_requiring_manual_review": len(pages_requiring_review),
            "issues": len(issues),
        }

        report = {
            "valid": not issues,
            "page_count": EXPECTED_PAGE_COUNT,
            "pages_checked": len(pages),
            "issues": issues,
            "pages_requiring_review": pages_requiring_review,
            "summary": summary,
        }

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)

    @staticmethod
    def build(pdf_path: str, output_path: str, validation_path: str, review_path: str):
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_file}")

        document = fitz.open(str(pdf_file))
        if len(document) != EXPECTED_PAGE_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_PAGE_COUNT} pages in {pdf_file}, found {len(document)}."
            )

        pages = []
        total_character_count = 0
        total_word_count = 0
        total_line_count = 0

        for page_number in range(1, len(document) + 1):
            page = document[page_number - 1]
            text = page.get_text("text")
            text_blocks = GroundTruthBuilder._build_text_blocks(page, page_number)
            tables = GroundTruthBuilder._build_tables(page, page_number)
            images = GroundTruthBuilder._build_images(document, page, page_number)
            layout_blocks = GroundTruthBuilder._build_layout_blocks(page, page_number)
            reading_order = [block["block_id"] for block in sorted(
                layout_blocks,
                key=lambda item: (item["bbox"][1], item["bbox"][0]),
            )]
            requires_ocr_review = bool((not text.strip()) and images)

            total_character_count += len(text)
            total_word_count += len(text.split())
            total_line_count += len(text.splitlines())

            page_entry = {
                "page_number": page_number,
                "width": float(page.rect.width),
                "height": float(page.rect.height),
                "text": text,
                "text_blocks": text_blocks,
                "tables": tables,
                "images": images,
                "layout_blocks": layout_blocks,
                "layout": {
                    "block_count": len(layout_blocks),
                    "reading_order": reading_order,
                    "reading_order_verified": False,
                },
                "requires_ocr_review": requires_ocr_review,
                "verification": {
                    "text_verified": False,
                    "tables_verified": False,
                    "images_verified": False,
                    "layout_verified": False,
                    "notes": [],
                },
            }

            page_entry["verification"]["notes"] = [
                "Automatically extracted from native PDF. Manual verification required."
            ]
            pages.append(page_entry)

        ground_truth = {
            "document": {
                "file_name": pdf_file.name,
                "page_count": EXPECTED_PAGE_COUNT,
                "domain": "Oil & Gas",
                "ground_truth_version": "1.0",
                "creation_method": "PDF-native extraction + manual verification",
                "verified": False,
            },
            "statistics": {
                "page_count": EXPECTED_PAGE_COUNT,
                "character_count": total_character_count,
                "word_count": total_word_count,
                "line_count": total_line_count,
                "table_count": sum(len(page.get("tables", [])) for page in pages),
                "table_cell_count": sum(
                    len(table.get("cells", [])) for page in pages for table in page.get("tables", [])
                ),
                "image_occurrence_count": sum(len(page.get("images", [])) for page in pages),
                "layout_block_count": sum(len(page.get("layout_blocks", [])) for page in pages),
                "pages_with_text": sum(1 for page in pages if page.get("text", "").strip()),
                "pages_with_tables": sum(1 for page in pages if page.get("tables")),
                "pages_with_images": sum(1 for page in pages if page.get("images")),
                "pages_requiring_ocr_review": sum(1 for page in pages if page.get("requires_ocr_review")),
            },
            "pages": pages,
        }

        issues = GroundTruthBuilder._validate_ground_truth(ground_truth)
        if issues:
            raise ValueError("Ground truth validation failed: " + "; ".join(issues))

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            json.dumps(ground_truth, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        validation_file = Path(validation_path)
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        GroundTruthBuilder._save_validation_report(pages, issues, validation_file)

        review_file = Path(review_path)
        review_file.parent.mkdir(parents=True, exist_ok=True)
        GroundTruthBuilder._save_review_csv(pages, review_file)

        return ground_truth


def parse_args():
    parser = argparse.ArgumentParser(description="Create a frozen ground-truth JSON from the benchmark PDF.")
    parser.add_argument("--pdf-path", default=DEFAULT_PDF_PATH)
    parser.add_argument("--output", default=DEFAULT_GROUND_TRUTH_PATH)
    parser.add_argument("--validation-output", default=DEFAULT_VALIDATION_PATH)
    parser.add_argument("--review-output", default=DEFAULT_REVIEW_PATH)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    output_file = Path(args.output)
    if output_file.exists() and not args.overwrite:
        print(
            f"Ground truth already exists at {output_file}. "
            "Use --overwrite to replace it.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        GroundTruthBuilder.build(
            pdf_path=args.pdf_path,
            output_path=args.output,
            validation_path=args.validation_output,
            review_path=args.review_output,
        )
        print(f"Ground truth created at {output_file}")
        print(f"Validation report created at {args.validation_output}")
        print(f"Review CSV created at {args.review_output}")
    except Exception as exc:
        print(f"Ground truth creation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
