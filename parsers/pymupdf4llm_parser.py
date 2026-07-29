import json
from pathlib import Path

import pymupdf4llm

from normalization.normalizer_factory import NormalizerFactory
from parsers.base_parser import BaseParser
from validation.schema_validator import SchemaValidator


class PyMuPDF4LLMParser(BaseParser):
    """
    Parser implementation using PyMuPDF4LLM.
    """

    def parse(
        self,
        pdf_path: str,
        markdown_path: str,
        json_path: str,
    ) -> str:

        markdown = pymupdf4llm.to_markdown(pdf_path)

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
            "parser": "pymupdf4llm",
            "source_pdf": Path(pdf_path).name,
            "markdown": markdown,
        }

        json_file.write_text(
            json.dumps(
                json_data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # Normalize the parser output
        normalizer = NormalizerFactory.get_normalizer(
            "pymupdf4llm",
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
            ),
            encoding="utf-8",
        )

        return markdown