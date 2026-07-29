from normalization.docling_normalizer import DoclingNormalizer
from normalization.liteparse_normalizer import LiteParseNormalizer
from normalization.pymupdf4llm_normalizer import PyMuPDF4LLMNormalizer


class NormalizerFactory:

    @staticmethod
    def get_normalizer(
        parser_name: str,
    ):

        normalizers = {
            "docling": DoclingNormalizer,
            "liteparse": LiteParseNormalizer,
            "pymupdf4llm": PyMuPDF4LLMNormalizer,
        }

        if parser_name not in normalizers:
            raise ValueError(
                f"Unsupported parser: {parser_name}"
            )

        return normalizers[parser_name]()