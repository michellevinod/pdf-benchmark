import json
from pathlib import Path

from docling.document_converter import DocumentConverter

from normalization.normalizer_factory import NormalizerFactory
from parsers.base_parser import BaseParser
from validation.schema_validator import SchemaValidator


class DoclingParser(BaseParser):
    """
    Parser implementation using Docling.
    """

    def parse(
        self,
        pdf_path: str,
        markdown_path: str,
        json_path: str,
    ) -> str:

        converter = DocumentConverter()

        result = converter.convert(pdf_path)

        doc = result.document

        # Native Docling Markdown
        markdown = doc.export_to_markdown()

        markdown_file = Path(markdown_path)
        markdown_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        markdown_file.write_text(
            markdown,
            encoding="utf-8",
        )

        # Native Docling structured JSON
        raw_json = doc.export_to_dict()

        json_file = Path(json_path)
        json_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_file.write_text(
            json.dumps(
                raw_json,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # Normalize the parser output
        normalizer = NormalizerFactory.get_normalizer(
            "docling",
        )

        normalized = normalizer.normalize(
            raw_json,
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
            ),
            encoding="utf-8",
        )

        return markdown