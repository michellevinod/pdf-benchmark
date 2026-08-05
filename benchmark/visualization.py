import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


RESULTS_PATH = Path(
    "results/final_benchmark_results.json"
)

CHARTS_DIR = Path(
    "results/charts"
)


DISPLAY_NAMES = {
    "docling": "Docling",
    "liteparse": "LiteParse",
    "pymupdf4llm": "PyMuPDF4LLM",
}


def load_results() -> list[dict]:

    with RESULTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return data.get(
        "parsers",
        [],
    )


def save_chart(
    filename: str,
) -> None:

    plt.tight_layout()

    path = (
        CHARTS_DIR
        / filename
    )

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved: {path}"
    )


def parser_names(
    results: list[dict],
) -> list[str]:

    return [
        DISPLAY_NAMES.get(
            result["parser"],
            result["parser"],
        )
        for result in results
    ]


def plot_text_quality(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    cer = [
        result["text_quality"][
            "character_error_rate"
        ]
        for result in results
    ]

    wer = [
        result["text_quality"][
            "word_error_rate"
        ]
        for result in results
    ]

    similarity = [
        result["text_quality"][
            "normalized_edit_similarity"
        ]
        for result in results
    ]

    x = np.arange(
        len(names)
    )

    width = 0.25

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        x - width,
        cer,
        width,
        label="CER",
    )

    plt.bar(
        x,
        wer,
        width,
        label="WER",
    )

    plt.bar(
        x + width,
        similarity,
        width,
        label="Edit Similarity",
    )

    plt.xticks(
        x,
        names,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Text Extraction Quality"
    )

    plt.legend()

    save_chart(
        "text_quality.png"
    )


def plot_execution_time(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    values = [
        result["performance"][
            "execution_time_seconds"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(8, 5)
    )

    plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Seconds"
    )

    plt.title(
        "Parser Execution Time"
    )

    save_chart(
        "execution_time.png"
    )


def plot_throughput(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    values = [
        result["performance"][
            "throughput_pages_per_second"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(8, 5)
    )

    plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Pages / Second"
    )

    plt.title(
        "Parser Throughput"
    )

    save_chart(
        "throughput.png"
    )


def plot_peak_memory(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    values = [
        result["performance"][
            "peak_memory_mb"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(8, 5)
    )

    plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Peak Memory (MB)"
    )

    plt.title(
        "Peak Memory Usage"
    )

    save_chart(
        "peak_memory.png"
    )


def plot_table_quality(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    teds = []

    f1 = []

    for result in results:

        table = result[
            "table_quality"
        ]

        teds.append(
            float(
                table["teds_score"]
            )
            / 100.0
        )

        f1_value = table.get(
            "table_f1_score"
        )

        if isinstance(
            f1_value,
            (int, float),
        ):
            f1.append(
                float(f1_value)
            )
        else:
            f1.append(
                np.nan
            )

    x = np.arange(
        len(names)
    )

    width = 0.35

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        x - width / 2,
        teds,
        width,
        label="TEDS",
    )

    plt.bar(
        x + width / 2,
        f1,
        width,
        label="Detection F1",
    )

    plt.xticks(
        x,
        names,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Table Extraction Quality"
    )

    plt.legend()

    save_chart(
        "table_quality.png"
    )


def plot_layout_quality(
    results: list[dict],
) -> None:

    names = parser_names(
        results
    )

    precision = [
        result["layout_quality"][
            "layout_precision"
        ]
        for result in results
    ]

    recall = [
        result["layout_quality"][
            "layout_recall"
        ]
        for result in results
    ]

    f1 = [
        result["layout_quality"][
            "layout_f1_score"
        ]
        for result in results
    ]

    mean_iou = [
        result["layout_quality"][
            "mean_iou"
        ]
        for result in results
    ]

    x = np.arange(
        len(names)
    )

    width = 0.2

    plt.figure(
        figsize=(10, 5)
    )

    plt.bar(
        x - 1.5 * width,
        precision,
        width,
        label="Precision",
    )

    plt.bar(
        x - 0.5 * width,
        recall,
        width,
        label="Recall",
    )

    plt.bar(
        x + 0.5 * width,
        f1,
        width,
        label="F1",
    )

    plt.bar(
        x + 1.5 * width,
        mean_iou,
        width,
        label="Mean IoU",
    )

    plt.xticks(
        x,
        names,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Layout Extraction Quality"
    )

    plt.legend()

    save_chart(
        "layout_quality.png"
    )


def main():

    CHARTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = load_results()

    if not results:
        raise ValueError(
            "No consolidated parser results found."
        )

    create_overall_comparison_heatmap(
        results,
        CHARTS_DIR,
    )

    print("=" * 60)
    print("Benchmark Visualization")
    print("=" * 60)

    plot_text_quality(
        results
    )

    plot_execution_time(
        results
    )

    plot_throughput(
        results
    )

    plot_peak_memory(
        results
    )

    plot_table_quality(
        results
    )

    plot_layout_quality(
        results
    )

    print()
    print(
        f"Charts saved to: {CHARTS_DIR}"
    )


def create_overall_comparison_heatmap(data, output_dir):
    """
    Creates a normalized heatmap comparing the overall
    strengths of each parser across major benchmark metrics.

    Values are normalized only for visualization.
    Original benchmark values are not modified.
    """

    parsers = [
        parser["parser"]
        for parser in data
    ]

    metric_names = [
        "Text Similarity",
        "Text Coverage",
        "Table F1",
        "TEDS",
        "Image F1",
        "Layout F1",
        "Throughput",
        "Memory Efficiency",
    ]

    raw_values = []

    for parser in data:

        table_f1 = parser["table_quality"].get(
            "table_f1_score"
        )

        image_f1 = parser["image_quality"].get(
            "image_f1_score"
        )

        raw_values.append(
            [
                parser["text_quality"].get(
                    "normalized_edit_similarity",
                    0,
                ),
                parser["text_quality"].get(
                    "text_coverage_percent",
                    0,
                ) / 100,
                (
                    float(table_f1)
                    if isinstance(table_f1, (int, float))
                    else None
                ),
                (
                    parser["table_quality"].get(
                        "teds_score",
                        0,
                    ) / 100
                ),
                (
                    float(image_f1)
                    if isinstance(image_f1, (int, float))
                    else None
                ),
                parser["layout_quality"].get(
                    "layout_f1_score",
                    0,
                ),
                parser["performance"].get(
                    "throughput_pages_per_second",
                    0,
                ),
                parser["performance"].get(
                    "peak_memory_mb",
                    0,
                ),
            ]
        )

    values = np.array(
        [
            [
                np.nan if value is None else value
                for value in row
            ]
            for row in raw_values
        ],
        dtype=float,
    )

    normalized = values.copy()

    # Normalize throughput: higher is better.
    throughput = values[:, 6]

    if np.nanmax(throughput) > 0:
        normalized[:, 6] = (
            throughput
            / np.nanmax(throughput)
        )

    # Normalize memory: lower is better.
    memory = values[:, 7]

    max_memory = np.nanmax(memory)
    min_memory = np.nanmin(memory)

    if max_memory != min_memory:
        normalized[:, 7] = (
            max_memory - memory
        ) / (
            max_memory - min_memory
        )
    else:
        normalized[:, 7] = 1.0

    fig, ax = plt.subplots(
        figsize=(12, 5)
    )

    masked_values = np.ma.masked_invalid(
        normalized.T
    )

    image = ax.imshow(
        masked_values,
        aspect="auto",
        vmin=0,
        vmax=1,
    )

    ax.set_xticks(
        range(len(parsers))
    )

    ax.set_xticklabels(
        parsers
    )

    ax.set_yticks(
        range(len(metric_names))
    )

    ax.set_yticklabels(
        metric_names
    )

    ax.set_title(
        "Overall Parser Comparison"
    )

    # Show normalized scores inside cells.
    for row in range(
        len(metric_names)
    ):
        for column in range(
            len(parsers)
        ):

            value = normalized[
                column,
                row,
            ]

            if np.isnan(value):
                label = "N/A"
            else:
                label = f"{value:.2f}"

            ax.text(
                column,
                row,
                label,
                ha="center",
                va="center",
            )

    fig.colorbar(
        image,
        ax=ax,
        label="Normalized Score (Higher = Better)",
    )

    plt.tight_layout()

    output_path = (
        output_dir
        / "overall_comparison_heatmap.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved: {output_path}"
    )


if __name__ == "__main__":
    main()