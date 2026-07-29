from typing import Any

from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.table_metrics import TableMetrics
from benchmark.text_metrics import TextMetrics


class QualityMetrics:
    """
    Aggregates all extraction quality metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
    ) -> dict:

        return {
            "text": TextMetrics.evaluate(
                normalized_document,
            ),
            "tables": TableMetrics.evaluate(
                normalized_document,
            ),
            "images": ImageMetrics.evaluate(
                normalized_document,
            ),
            "layout": LayoutMetrics.evaluate(
                normalized_document,
            ),
        }