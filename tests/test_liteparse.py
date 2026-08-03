import json
from pathlib import Path

from normalization.liteparse_normalizer import LiteParseNormalizer


def test_liteparse_normalizer_preserves_layout_blocks_and_ocr():
    raw = json.loads(
        Path("outputs/liteparse/output.json").read_text(encoding="utf-8")
    )

    normalized = LiteParseNormalizer().normalize(raw)

    first_page = normalized["pages"][0]
    assert first_page["layout_blocks"], "LiteParse should keep geometry-derived layout blocks"
    assert any(block.get("is_ocr") for block in first_page["layout_blocks"]), (
        "LiteParse should keep OCR-aware blocks when OCR font metadata is present"
    )
    assert first_page["ocr_text"].strip() or any(
        page.get("ocr_text", "").strip() for page in normalized["pages"]
    )
    assert normalized["statistics"]["page_count"] >= 1