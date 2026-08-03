import json
from pathlib import Path

from normalization.pymupdf4llm_normalizer import PyMuPDF4LLMNormalizer


def test_pymupdf4llm_normalizer_keeps_page_boxes_as_layout_blocks():
    raw = json.loads(
        Path("outputs/pymupdf4llm/output.json").read_text(encoding="utf-8")
    )

    normalized = PyMuPDF4LLMNormalizer().normalize(raw)

    first_page = normalized["pages"][0]
    assert "layout_blocks" in first_page
    assert first_page["layout_blocks"], "Page box metadata should not be discarded during normalization"
    assert any(block.get("type") == "table" for block in first_page["layout_blocks"])
    assert normalized["statistics"]["page_count"] >= 1