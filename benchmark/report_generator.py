import csv
import json
from pathlib import Path


class ReportGenerator:
    """
    Generates benchmark reports in JSON and CSV formats.
    """

    @staticmethod
    def save_json(results: list[dict], output_file: str):

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                indent=4,
            )

    @staticmethod
    def save_csv(results: list[dict], output_file: str):

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=results[0].keys(),
            )

            writer.writeheader()
            writer.writerows(results)