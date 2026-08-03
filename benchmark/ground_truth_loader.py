import json
from pathlib import Path


class GroundTruthLoader:
    """
    Loads and validates a frozen benchmark ground-truth JSON.

    The loader is dataset-agnostic and supports benchmark
    documents with any positive number of pages.
    """

    @staticmethod
    def load(path: str | Path) -> dict:
        target = Path(path)

        if not target.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: {target}"
            )

        with target.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = json.load(file)

        if not isinstance(document, dict):
            raise ValueError(
                "Ground truth JSON root must be an object."
            )

        pages = document.get("pages")

        if not isinstance(pages, list):
            raise ValueError(
                "Ground truth pages must be a list."
            )

        if not pages:
            raise ValueError(
                "Ground truth must contain at least one page."
            )

        page_count = len(pages)

        page_numbers = [
            page.get("page_number")
            for page in pages
        ]

        expected_page_numbers = list(
            range(1, page_count + 1)
        )

        if page_numbers != expected_page_numbers:
            raise ValueError(
                "Ground truth page numbers must be sequential "
                f"from 1 through {page_count}."
            )

        statistics = document.get("statistics")

        if not isinstance(statistics, dict):
            raise ValueError(
                "Ground truth statistics are missing."
            )

        return document

    @staticmethod
    def get_page_texts(
        document: dict,
    ) -> list[str]:
        return [
            page.get("text", "")
            for page in document.get("pages", [])
        ]

    @staticmethod
    def get_table_count(
        document: dict,
    ) -> int:
        stats = document.get(
            "statistics",
            {},
        )

        if "table_count" in stats:
            return int(
                stats["table_count"]
            )

        return sum(
            len(page.get("tables", []))
            for page in document.get("pages", [])
        )

    @staticmethod
    def get_image_count(
        document: dict,
    ) -> int:
        stats = document.get(
            "statistics",
            {},
        )

        if "image_occurrence_count" in stats:
            return int(
                stats["image_occurrence_count"]
            )

        if "image_count" in stats:
            return int(
                stats["image_count"]
            )

        return sum(
            len(page.get("images", []))
            for page in document.get("pages", [])
        )

    @staticmethod
    def get_layout_count(
        document: dict,
    ) -> int:
        stats = document.get(
            "statistics",
            {},
        )

        if "layout_block_count" in stats:
            return int(
                stats["layout_block_count"]
            )

        return sum(
            len(page.get("layout_blocks", []))
            for page in document.get("pages", [])
        )

    @staticmethod
    def get_reference_tables(
        document: dict,
    ) -> list[list[dict]]:
        return [
            page.get("tables", [])
            for page in document.get("pages", [])
        ]

    @staticmethod
    def get_reference_images(
        document: dict,
    ) -> list[list[dict]]:
        return [
            page.get("images", [])
            for page in document.get("pages", [])
        ]

    @staticmethod
    def get_reference_layout_blocks(
        document: dict,
    ) -> list[list[dict]]:
        return [
            page.get("layout_blocks", [])
            for page in document.get("pages", [])
        ]