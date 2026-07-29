import json
from pathlib import Path

from liteparse import LiteParse

from normalization.normalizer_factory import NormalizerFactory
from parsers.base_parser import BaseParser
from validation.schema_validator import SchemaValidator


class LiteParseParser(BaseParser):
    """
    Parser implementation using LiteParse.
    """

    def parse(
        self,
        pdf_path: str,
        markdown_path: str,
        json_path: str,
    ) -> str:

        parser = LiteParse(
            output_format="markdown",
            quiet=True,
        )

        result = parser.parse(pdf_path)

        markdown = result.text

        markdown_file = Path(markdown_path)
        markdown_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        markdown_file.write_text(
            markdown,
            encoding="utf-8",
        )

        json_file = Path(json_path)
        json_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_data = {
            "parser": "liteparse",
            "source_pdf": Path(pdf_path).name,
            "producer": result.producer,
            "creator": result.creator,
            "form_type": result.form_type,
            "num_pages": result.num_pages,
            "image_count": len(result.images),
            "image_error_count": result.image_error_count,
            "pages": [
                {
                    "page_number": page.page_num,
                    "width": page.width,
                    "height": page.height,
                    "text": page.text,
                    "markdown": page.markdown,
                    "text_items": page.text_items,
                    "annotations": page.annotations,
                    "form_fields": page.form_fields,
                    "vector_graphics": page.vector_graphics,
                    "content_bounds": page.content_bounds,
                    "structure_tree": page.structure_tree,
                    "complexity": page.complexity,
                }
                for page in result.pages
            ],
            "images": result.images,
        }

        json_file.write_text(
            json.dumps(
                json_data,
                indent=4,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        # Normalize the parser output
        normalizer = NormalizerFactory.get_normalizer(
            "liteparse",
        )

        normalized = normalizer.normalize(
            json_data,
        )

        # Validate normalized schema
        SchemaValidator.validate(
            normalized,
        )

        normalized_path = (
            json_file.parent / "normalized.json"
        )

        normalized_path.write_text(
            json.dumps(
                normalized,
                indent=4,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        return markdown