from normalization.base_normalizer import BaseNormalizer


class DoclingNormalizer(BaseNormalizer):
    """
    Converts Docling's raw JSON into the common normalized schema.

    Preserves text, tables, images, and layout information
    required by the benchmark evaluation layer.
    """

    def normalize(
        self,
        raw_json: dict,
    ) -> dict:

        raw_pages = raw_json.get(
            "pages",
            {},
        )

        page_count = len(raw_pages)

        normalized = {
            "parser": raw_json.get(
                "parser",
                "docling",
            ),
            "source_pdf": raw_json.get(
                "source_pdf",
                "",
            ),
            "metadata": {
                "schema_name": raw_json.get(
                    "schema_name",
                ),
                "version": raw_json.get(
                    "version",
                ),
                "document_name": raw_json.get(
                    "name",
                ),
            },
            "pages": [],
            "statistics": {
                "page_count": page_count,
                "table_count": len(
                    raw_json.get(
                        "tables",
                        [],
                    )
                ),
                "image_count": len(
                    raw_json.get(
                        "pictures",
                        [],
                    )
                ),
            },
        }

        # -------------------------------------------------
        # Create normalized page objects
        # -------------------------------------------------

        for page_number in range(
            1,
            page_count + 1,
        ):

            raw_page = raw_pages.get(
                str(page_number),
                {},
            )

            page_size = raw_page.get(
                "size",
                {},
            )

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
                    "metadata": {
                        "width": page_size.get(
                            "width"
                        ),
                        "height": page_size.get(
                            "height"
                        ),
                    },
                }
            )

        # -------------------------------------------------
        # Text + layout blocks
        # -------------------------------------------------

        texts = raw_json.get(
            "texts",
            [],
        )

        for text in texts:

            provenance = text.get(
                "prov",
                [],
            )

            if not provenance:
                continue

            content = text.get(
                "text",
                "",
            )

            label = text.get(
                "label",
                "text",
            )

            for prov in provenance:

                page_number = prov.get(
                    "page_no",
                )

                if page_number is None:
                    continue

                if (
                    page_number < 1
                    or page_number > page_count
                ):
                    continue

                page = normalized[
                    "pages"
                ][page_number - 1]

                # Add textual content
                if content:

                    if page["text"]:
                        page["text"] += "\n"

                    page["text"] += content

                # Preserve layout information
                page[
                    "layout_blocks"
                ].append(
                    {
                        "type": label,
                        "text": content,
                        "bbox": prov.get(
                            "bbox"
                        ),
                        "charspan": prov.get(
                            "charspan"
                        ),
                        "content_layer": (
                            text.get(
                                "content_layer"
                            )
                        ),
                        "self_ref": text.get(
                            "self_ref"
                        ),
                    }
                )

        # -------------------------------------------------
        # Tables
        # -------------------------------------------------

        tables = raw_json.get(
            "tables",
            [],
        )

        for table in tables:

            provenance = table.get(
                "prov",
                [],
            )

            if not provenance:
                continue

            for prov in provenance:

                page_number = prov.get(
                    "page_no",
                )

                if page_number is None:
                    continue

                if (
                    page_number < 1
                    or page_number > page_count
                ):
                    continue

                page = normalized[
                    "pages"
                ][page_number - 1]

                page["tables"].append(
                    {
                        "bbox": prov.get(
                            "bbox"
                        ),
                        "captions": table.get(
                            "captions",
                            [],
                        ),
                        "references": table.get(
                            "references",
                            [],
                        ),
                        "footnotes": table.get(
                            "footnotes",
                            [],
                        ),
                        "cells": (
                            table.get(
                                "data",
                                {},
                            ).get(
                                "table_cells",
                                [],
                            )
                        ),
                    }
                )

                # Tables are also layout elements
                page[
                    "layout_blocks"
                ].append(
                    {
                        "type": "table",
                        "text": "",
                        "bbox": prov.get(
                            "bbox"
                        ),
                        "content_layer": (
                            table.get(
                                "content_layer"
                            )
                        ),
                        "self_ref": table.get(
                            "self_ref"
                        ),
                    }
                )

        # -------------------------------------------------
        # Pictures / figures
        # -------------------------------------------------

        pictures = raw_json.get(
            "pictures",
            [],
        )

        for picture in pictures:

            provenance = picture.get(
                "prov",
                [],
            )

            if not provenance:
                continue

            for prov in provenance:

                page_number = prov.get(
                    "page_no",
                )

                if page_number is None:
                    continue

                if (
                    page_number < 1
                    or page_number > page_count
                ):
                    continue

                page = normalized[
                    "pages"
                ][page_number - 1]

                image_data = {
                    "bbox": prov.get(
                        "bbox"
                    ),
                    "captions": picture.get(
                        "captions",
                        [],
                    ),
                    "references": picture.get(
                        "references",
                        [],
                    ),
                    "footnotes": picture.get(
                        "footnotes",
                        [],
                    ),
                    "annotations": picture.get(
                        "annotations",
                        [],
                    ),
                }

                page["images"].append(
                    image_data
                )

                page["figures"].append(
                    image_data
                )

                # Pictures are also layout elements
                page[
                    "layout_blocks"
                ].append(
                    {
                        "type": "picture",
                        "text": "",
                        "bbox": prov.get(
                            "bbox"
                        ),
                        "content_layer": (
                            picture.get(
                                "content_layer"
                            )
                        ),
                        "self_ref": picture.get(
                            "self_ref"
                        ),
                    }
                )

        # -------------------------------------------------
        # Sort layout blocks into approximate reading order
        # -------------------------------------------------

        for page in normalized["pages"]:

            def layout_sort_key(
                block: dict,
            ):

                bbox = block.get(
                    "bbox"
                )

                if not bbox:
                    return (
                        float("inf"),
                        float("inf"),
                    )

                # Docling coordinates use BOTTOMLEFT.
                # Higher top coordinate appears earlier
                # on the page.
                top = bbox.get(
                    "t",
                    0,
                )

                left = bbox.get(
                    "l",
                    0,
                )

                return (
                    -top,
                    left,
                )

            page[
                "layout_blocks"
            ].sort(
                key=layout_sort_key
            )

        return normalized