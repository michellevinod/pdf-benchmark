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
        Saves benchmark results as a flattened CSV file.
        """

        if not results:
            return

        output_path = Path(output_file)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        def flatten(
            data: dict[str, Any],
            parent_key: str = "",
        ) -> dict[str, Any]:

            flattened = {}

            for key, value in data.items():

                new_key = (
                    f"{parent_key}_{key}"
                    if parent_key
                    else key
                )

                if isinstance(value, dict):
                    flattened.update(
                        flatten(
                            value,
                            new_key,
                        )
                    )
                else:
                    flattened[new_key] = value

            return flattened

        flattened_results = [
            flatten(result)
            for result in results
        ]

        fieldnames = []
        for item in flattened_results:
            for key in item.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()
            for record in flattened_results:
                writer.writerow({
                    key: record.get(key, "")
                    for key in fieldnames
                })