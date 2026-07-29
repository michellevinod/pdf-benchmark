from typing import Any


class TableMetrics:
    """
    Evaluates table extraction metrics.
    """

    @staticmethod
    def evaluate(
        normalized_document: dict[str, Any],
    ) -> dict:

        pages = normalized_document.get(
            "pages",
            [],
        )

        total_tables = 0
        pages_with_tables = 0
        empty_tables = 0

        for page in pages:

            tables = page.get(
                "tables",
                [],
            )

            if tables:
                pages_with_tables += 1

            total_tables += len(tables)

            for table in tables:

                cells = table.get(
                    "table_cells",
                    [],
                )

                if not cells:
                    empty_tables += 1

        page_count = len(pages)

        average_tables_per_page = (
            total_tables / page_count
            if page_count
            else 0
        )

        return {
            "table_count": total_tables,
            "pages_with_tables": pages_with_tables,
            "average_tables_per_page": round(
                average_tables_per_page,
                2,
            ),
            "empty_tables": empty_tables,
        }