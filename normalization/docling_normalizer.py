from normalization.base_normalizer import BaseNormalizer


class DoclingNormalizer(BaseNormalizer):
    """
    Converts Docling's raw JSON into the common normalized schema.
    """

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        normalized = {
            "parser": raw_json.get("parser", "docling"),
            "source_pdf": raw_json.get("source_pdf", ""),
            "metadata": {
                "schema_name": raw_json.get("schema_name"),
                "version": raw_json.get("version"),
                "document_name": raw_json.get("name"),
            },
            "pages": [],
            "statistics": {
                "page_count": len(raw_json.get("pages", [])),
                "table_count": len(raw_json.get("tables", [])),
                "image_count": len(raw_json.get("pictures", [])),
            },
        }

        page_count = len(raw_json.get("pages", []))

        for page_number in range(1, page_count + 1):
            normalized["pages"].append(
                {
                    "page_number": page_number,
                    "text": "",
                    "markdown": "",
                    "tables": [],
                    "images": [],
                    "figures": [],
                    "layout_blocks": [],
                    "ocr_text": "",
                    "metadata": {},
                }
            )

        texts = raw_json.get("texts", [])

        for text in texts:

            prov = text.get("prov", [])

            if not prov:
                continue

            page_number = prov[0].get("page_no")

            if page_number is None:
                continue

            if page_number < 1 or page_number > page_count:
                continue

            page = normalized["pages"][page_number - 1]

            content = text.get("text", "")

            if content:

                if page["text"]:
                    page["text"] += "\n"

                page["text"] += content

        tables = raw_json.get("tables", [])

        for table in tables:

            prov = table.get("prov", [])

            if not prov:
                continue

            page_number = prov[0].get("page_no")

            if page_number is None:
                continue

            if page_number < 1 or page_number > page_count:
                continue

            page = normalized["pages"][page_number - 1]

            page["tables"].append(
                {
                    "bbox": prov[0].get("bbox"),
                    "captions": table.get("captions", []),
                    "references": table.get("references", []),
                    "footnotes": table.get("footnotes", []),
                    "cells": table.get("data", {}).get(
                        "table_cells",
                        [],
                    ),
                }
            )

        pictures = raw_json.get("pictures", [])

        for picture in pictures:

            prov = picture.get("prov", [])

            if not prov:
                continue

            page_number = prov[0].get("page_no")

            if page_number is None:
                continue

            if page_number < 1 or page_number > page_count:
                continue

            page = normalized["pages"][page_number - 1]

            page["images"].append(
                {
                    "bbox": prov[0].get("bbox"),
                    "captions": picture.get("captions", []),
                    "references": picture.get("references", []),
                    "footnotes": picture.get("footnotes", []),
                    "annotations": picture.get("annotations", []),
                }
            )

        return normalized