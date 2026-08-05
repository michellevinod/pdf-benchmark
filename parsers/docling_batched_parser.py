import json
import time
from pathlib import Path

import fitz
from docling.document_converter import (
    ConversionStatus,
    DocumentConverter,
)

from normalization.normalizer_factory import NormalizerFactory
from validation.schema_validator import SchemaValidator


class DoclingBatchedParser:
    """
    Runs Docling on a PDF in smaller page ranges.

    The Docling-native documents are normalized independently
    and then merged at the benchmark common-schema level.

    This avoids unsafe merging of Docling-native references.
    """

    def __init__(
        self,
        batch_size: int = 10,
    ):
        self.batch_size = batch_size

    @staticmethod
    def _empty_document(
        source_pdf: str,
    ) -> dict:
        return {
            "parser": "docling",
            "source_pdf": source_pdf,
            "pages": [],
            "statistics": {},
            "metadata": {
                "batched_processing": True,
            },
        }

    @staticmethod
    def _localize_docling_page_numbers(
        raw_json: dict,
        start_page: int,
    ) -> None:
        """
        Converts Docling's original PDF page numbers into
        batch-local page numbers before normalization.

        Example:
            batch 11-20
            original 11 -> local 1
            original 12 -> local 2
            ...
            original 20 -> local 10

        The normalized pages are later mapped back to their
        original PDF page numbers by _remap_pages().
        """

        # ---------------------------------------------
        # Remap raw page dictionary keys
        # ---------------------------------------------

        raw_pages = raw_json.get(
            "pages",
            {},
        )

        localized_pages = {}

        for original_key, page_data in (
            raw_pages.items()
        ):
            original_page = int(
                original_key
            )

            local_page = (
                original_page
                - start_page
                + 1
            )

            localized_pages[
                str(local_page)
            ] = page_data

        raw_json["pages"] = (
            localized_pages
        )

        # ---------------------------------------------
        # Remap provenance page numbers
        # ---------------------------------------------

        collections = (
            "texts",
            "tables",
            "pictures",
        )

        for collection_name in collections:

            for item in raw_json.get(
                collection_name,
                [],
            ):

                for prov in item.get(
                    "prov",
                    [],
                ):

                    original_page = prov.get(
                        "page_no"
                    )

                    if original_page is None:
                        continue

                    prov["page_no"] = (
                        original_page
                        - start_page
                        + 1
                    )

    @staticmethod
    def _remap_pages(
        normalized: dict,
        start_page: int,
    ) -> None:
        """
        Docling page-range conversion may expose page numbers
        relative to the batch. Convert them back to original
        PDF page numbers.
        """

        pages = normalized.get(
            "pages",
            [],
        )

        for local_index, page in enumerate(
            pages,
            start=0,
        ):
            original_page_number = (
                start_page + local_index
            )

            page["page_number"] = (
                original_page_number
            )

            # Also repair page numbers stored in nested
            # benchmark objects where present.
            for collection_name in (
                "tables",
                "images",
                "figures",
                "layout_blocks",
            ):
                for item in page.get(
                    collection_name,
                    [],
                ):
                    if isinstance(item, dict):
                        item["page_number"] = (
                            original_page_number
                        )

    @staticmethod
    def _recalculate_statistics(
        document: dict,
    ) -> None:

        pages = document.get(
            "pages",
            [],
        )

        document["statistics"] = {
            "page_count": len(pages),

            "table_count": sum(
                len(page.get("tables", []))
                for page in pages
            ),

            "structured_table_count": sum(
                1
                for page in pages
                for table in page.get(
                    "tables",
                    [],
                )
                if table.get(
                    "has_structure"
                )
            ),

            "table_cell_count": sum(
                len(table.get("cells", []))
                for page in pages
                for table in page.get(
                    "tables",
                    [],
                )
            ),

            "image_count": sum(
                len(page.get("images", []))
                for page in pages
            ),

            "layout_block_count": sum(
                len(
                    page.get(
                        "layout_blocks",
                        [],
                    )
                )
                for page in pages
            ),
        }

    def parse(
        self,
        pdf_path: str,
        normalized_path: str,
    ) -> dict:

        pdf_document = fitz.open(
            pdf_path
        )

        total_pages = len(
            pdf_document
        )

        pdf_document.close()

        converter = DocumentConverter()

        combined = self._empty_document(
            source_pdf=pdf_path,
        )

        batch_results = []

        overall_start = time.perf_counter()

        for start_page in range(
            1,
            total_pages + 1,
            self.batch_size,
        ):

            end_page = min(
                start_page
                + self.batch_size
                - 1,
                total_pages,
            )

            print(
                "\n"
                + "=" * 60
            )

            print(
                f"Docling batch: "
                f"{start_page}-{end_page}"
            )

            print(
                "=" * 60
            )

            batch_start = (
                time.perf_counter()
            )

            result = converter.convert(
                pdf_path,
                page_range=(
                    start_page,
                    end_page,
                ),
            )

            elapsed = (
                time.perf_counter()
                - batch_start
            )

            print(
                f"Status : {result.status}"
            )

            print(
                f"Time   : {elapsed:.3f} sec"
            )

            if result.status != (
                ConversionStatus.SUCCESS
            ):
                raise RuntimeError(
                    "Docling batch failed or "
                    "partially succeeded: "
                    f"{start_page}-{end_page}, "
                    f"status={result.status}"
                )

            raw_json = (
                result.document.export_to_dict()
            )

            # Convert Docling's original PDF page numbering
            # to batch-local numbering for the existing
            # DoclingNormalizer.
            self._localize_docling_page_numbers(
                raw_json,
                start_page,
            )

            normalizer = (
                NormalizerFactory.get_normalizer(
                    "docling"
                )
            )

            normalized = (
                normalizer.normalize(
                    raw_json
                )
            )

            self._remap_pages(
                normalized,
                start_page,
            )

            batch_page_count = len(
                normalized.get(
                    "pages",
                    [],
                )
            )

            expected_page_count = (
                end_page
                - start_page
                + 1
            )

            if (
                batch_page_count
                != expected_page_count
            ):
                raise RuntimeError(
                    "Unexpected normalized page "
                    "count for batch "
                    f"{start_page}-{end_page}: "
                    f"expected "
                    f"{expected_page_count}, "
                    f"got {batch_page_count}"
                )

            combined[
                "pages"
            ].extend(
                normalized.get(
                    "pages",
                    [],
                )
            )

            batch_results.append(
                {
                    "start_page": start_page,
                    "end_page": end_page,
                    "page_count": (
                        batch_page_count
                    ),
                    "status": str(
                        result.status
                    ),
                    "execution_time_seconds": (
                        round(
                            elapsed,
                            3,
                        )
                    ),
                }
            )

            # Release references before next batch.
            del normalized
            del raw_json
            del result

        combined[
            "pages"
        ].sort(
            key=lambda page: page.get(
                "page_number",
                0,
            )
        )

        self._recalculate_statistics(
            combined
        )

        combined[
            "batching"
        ] = {
            "enabled": True,
            "batch_size": (
                self.batch_size
            ),
            "batch_count": len(
                batch_results
            ),
            "batches": batch_results,
            "total_execution_time_seconds": (
                round(
                    time.perf_counter()
                    - overall_start,
                    3,
                )
            ),
        }

        # Final schema validation after all
        # normalized batches have been merged.
        SchemaValidator.validate(
            combined
        )

        target = Path(
            normalized_path
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            json.dumps(
                combined,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return combined