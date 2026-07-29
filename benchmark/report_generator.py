import csv
import json
from pathlib import Path
from typing import Any


class ReportGenerator:
    """
    Generates benchmark reports in JSON and CSV formats.
    """

    @staticmethod
    def save_json(
        results: list[dict[str, Any]],
        output_file: str,
    ) -> None:
        """
        Saves benchmark results as a JSON file.
        """

        output_path = Path(output_file)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False,
            )

    @staticmethod
    def save_csv(
        results: list[dict[str, Any]],
        output_file: str,
    ) -> None:
        """
        Saves benchmark results as a CSV file.
        """

        if not results:
            return

        output_path = Path(output_file)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = list(results[0].keys())

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(results)