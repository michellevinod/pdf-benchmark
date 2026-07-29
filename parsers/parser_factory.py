from parsers.docling_parser import DoclingParser
from parsers.liteparse_parser import LiteParseParser
from parsers.pymupdf4llm_parser import PyMuPDF4LLMParser


class ParserFactory:
    """
    Factory class to instantiate parser implementations.
    """

    @staticmethod
    def get_parser(parser_name: str):
        parser_name = parser_name.lower()

        parsers = {
            "docling": DoclingParser,
            "liteparse": LiteParseParser,
            "pymupdf4llm": PyMuPDF4LLMParser,
        }

        if parser_name not in parsers:
            raise ValueError(
                f"Unsupported parser: {parser_name}"
            )

        return parsers[parser_name]()