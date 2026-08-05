import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


RESULTS_PATH = Path(
    "results/final_63page_benchmark_results.json"
)

CHARTS_DIR = Path(
    "results/final_63page_charts"
)


def load_results() -> list[dict]:
    """
    Loads the final consolidated 63-page benchmark results.
    """

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
    """
    Saves the current Matplotlib figure.
    """

    plt.tight_layout()

    path = CHARTS_DIR / filename

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved: {path}"
    )


def is_numeric(
    value,
) -> bool:
    """
    Returns True only for real numeric benchmark values.

    Unsupported and not-measured values are intentionally
    excluded from charts rather than plotted as zero.
    """

    return isinstance(
        value,
        (int, float),
    ) and not isinstance(
        value,
        bool,
    )


def get_names(
    results: list[dict],
) -> list[str]:

    return [
        result.get(
            "display_name",
            result.get(
                "parser",
                "Unknown",
            ),
        )
        for result in results
    ]


def add_value_labels(
    bars,
    decimals: int = 3,
) -> None:
    """
    Adds values above bars.
    """

    for bar in bars:

        height = bar.get_height()

        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            height,
            f"{height:.{decimals}f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )


# =========================================================
# TEXT QUALITY
# =========================================================


def plot_text_error_rates(
    results: list[dict],
) -> None:

    names = get_names(
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

    x = np.arange(
        len(names)
    )

    width = 0.35

    plt.figure(
        figsize=(10, 6)
    )

    bars1 = plt.bar(
        x - width / 2,
        cer,
        width,
        label="CER",
    )

    bars2 = plt.bar(
        x + width / 2,
        wer,
        width,
        label="WER",
    )

    plt.xticks(
        x,
        names,
    )

    plt.ylabel(
        "Error Rate"
    )

    plt.title(
        "Text Extraction Error Rates"
    )

    plt.legend()

    add_value_labels(
        bars1,
        4,
    )

    add_value_labels(
        bars2,
        4,
    )

    save_chart(
        "text_error_rates.png"
    )


def plot_text_similarity(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["text_quality"][
            "normalized_edit_similarity"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Similarity Score"
    )

    plt.title(
        "Normalized Text Edit Similarity"
    )

    add_value_labels(
        bars,
        4,
    )

    save_chart(
        "text_similarity.png"
    )


def plot_text_coverage(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["text_quality"][
            "text_coverage_percent"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Coverage (%)"
    )

    plt.ylim(
        0,
        110,
    )

    plt.title(
        "Text Coverage"
    )

    add_value_labels(
        bars,
        2,
    )

    save_chart(
        "text_coverage.png"
    )


# =========================================================
# TABLE QUALITY
# =========================================================


def plot_extracted_tables(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["table_quality"][
            "extracted_table_count"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.axhline(
        y=48,
        linestyle="--",
        label="Reference tables (48)",
    )

    plt.ylabel(
        "Number of Tables"
    )

    plt.title(
        "Extracted Table Count"
    )

    plt.legend()

    add_value_labels(
        bars,
        0,
    )

    save_chart(
        "extracted_table_count.png"
    )


def plot_table_teds(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["table_quality"][
            "teds_score"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "TEDS-style Score (%)"
    )

    plt.title(
        "Table Structural Similarity"
    )

    add_value_labels(
        bars,
        2,
    )

    save_chart(
        "table_teds.png"
    )


def plot_table_spatial_quality(
    results: list[dict],
) -> None:

    supported = []

    for result in results:

        quality = result.get(
            "table_quality",
            {},
        )

        f1 = quality.get(
            "table_f1_score"
        )

        if is_numeric(
            f1
        ):
            supported.append(
                result
            )

    names = get_names(
        supported
    )

    precision = [
        result["table_quality"][
            "table_precision"
        ]
        for result in supported
    ]

    recall = [
        result["table_quality"][
            "table_recall"
        ]
        for result in supported
    ]

    f1 = [
        result["table_quality"][
            "table_f1_score"
        ]
        for result in supported
    ]

    x = np.arange(
        len(names)
    )

    width = 0.25

    plt.figure(
        figsize=(9, 6)
    )

    bars1 = plt.bar(
        x - width,
        precision,
        width,
        label="Precision",
    )

    bars2 = plt.bar(
        x,
        recall,
        width,
        label="Recall",
    )

    bars3 = plt.bar(
        x + width,
        f1,
        width,
        label="F1",
    )

    plt.xticks(
        x,
        names,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Spatial Table Detection Quality"
    )

    plt.legend()

    add_value_labels(
        bars1,
        4,
    )

    add_value_labels(
        bars2,
        4,
    )

    add_value_labels(
        bars3,
        4,
    )

    save_chart(
        "table_spatial_quality.png"
    )


# =========================================================
# IMAGE QUALITY
# =========================================================


def plot_image_counts(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["image_quality"].get(
            "extracted_image_count",
            0,
        )
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.axhline(
        y=62,
        linestyle="--",
        label="Reference images (62)",
    )

    plt.ylabel(
        "Image / Representation Count"
    )

    plt.title(
        "Extracted Image Representations"
    )

    plt.legend()

    add_value_labels(
        bars,
        0,
    )

    save_chart(
        "image_counts.png"
    )


def plot_image_quality(
    results: list[dict],
) -> None:

    supported = []

    for result in results:

        quality = result.get(
            "image_quality",
            {},
        )

        if is_numeric(
            quality.get(
                "image_f1_score"
            )
        ):
            supported.append(
                result
            )

    if not supported:
        return

    names = get_names(
        supported
    )

    f1 = [
        result["image_quality"][
            "image_f1_score"
        ]
        for result in supported
    ]

    mean_iou = [
        result["image_quality"][
            "mean_iou"
        ]
        for result in supported
    ]

    x = np.arange(
        len(names)
    )

    width = 0.35

    plt.figure(
        figsize=(8, 6)
    )

    bars1 = plt.bar(
        x - width / 2,
        f1,
        width,
        label="Image F1",
    )

    bars2 = plt.bar(
        x + width / 2,
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
        "Spatial Image Extraction Quality"
    )

    plt.legend()

    add_value_labels(
        bars1,
        4,
    )

    add_value_labels(
        bars2,
        4,
    )

    save_chart(
        "image_quality.png"
    )


# =========================================================
# LAYOUT QUALITY
# =========================================================


def plot_layout_counts(
    results: list[dict],
) -> None:

    names = get_names(
        results
    )

    values = [
        result["layout_quality"][
            "extracted_block_count"
        ]
        for result in results
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.axhline(
        y=1656,
        linestyle="--",
        label="Reference blocks (1,656)",
    )

    plt.ylabel(
        "Layout Block Count"
    )

    plt.title(
        "Extracted Layout Block Count"
    )

    plt.legend()

    add_value_labels(
        bars,
        0,
    )

    save_chart(
        "layout_block_counts.png"
    )


def plot_layout_quality(
    results: list[dict],
) -> None:

    supported = []

    for result in results:

        quality = result.get(
            "layout_quality",
            {},
        )

        if is_numeric(
            quality.get(
                "layout_f1_score"
            )
        ):
            supported.append(
                result
            )

    names = get_names(
        supported
    )

    precision = [
        result["layout_quality"][
            "layout_precision"
        ]
        for result in supported
    ]

    recall = [
        result["layout_quality"][
            "layout_recall"
        ]
        for result in supported
    ]

    f1 = [
        result["layout_quality"][
            "layout_f1_score"
        ]
        for result in supported
    ]

    mean_iou = [
        result["layout_quality"][
            "mean_iou"
        ]
        for result in supported
    ]

    x = np.arange(
        len(names)
    )

    width = 0.2

    plt.figure(
        figsize=(11, 6)
    )

    bars1 = plt.bar(
        x - 1.5 * width,
        precision,
        width,
        label="Precision",
    )

    bars2 = plt.bar(
        x - 0.5 * width,
        recall,
        width,
        label="Recall",
    )

    bars3 = plt.bar(
        x + 0.5 * width,
        f1,
        width,
        label="F1",
    )

    bars4 = plt.bar(
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

    add_value_labels(
        bars1,
        3,
    )

    add_value_labels(
        bars2,
        3,
    )

    add_value_labels(
        bars3,
        3,
    )

    add_value_labels(
        bars4,
        3,
    )

    save_chart(
        "layout_quality.png"
    )


# =========================================================
# PERFORMANCE
# =========================================================


def get_performance_supported(
    results: list[dict],
    metric: str,
) -> list[dict]:

    return [
        result
        for result in results
        if is_numeric(
            result.get(
                "performance",
                {},
            ).get(
                metric
            )
        )
    ]


def plot_execution_time(
    results: list[dict],
) -> None:

    supported = (
        get_performance_supported(
            results,
            "execution_time_seconds",
        )
    )

    names = get_names(
        supported
    )

    values = [
        result["performance"][
            "execution_time_seconds"
        ]
        for result in supported
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Execution Time (seconds)"
    )

    plt.title(
        "63-Page PDF Processing Time"
    )

    add_value_labels(
        bars,
        3,
    )

    save_chart(
        "execution_time.png"
    )


def plot_seconds_per_page(
    results: list[dict],
) -> None:

    supported = (
        get_performance_supported(
            results,
            "seconds_per_page",
        )
    )

    names = get_names(
        supported
    )

    values = [
        result["performance"][
            "seconds_per_page"
        ]
        for result in supported
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Seconds per Page"
    )

    plt.title(
        "Processing Time per Page"
    )

    add_value_labels(
        bars,
        3,
    )

    save_chart(
        "seconds_per_page.png"
    )


def plot_throughput(
    results: list[dict],
) -> None:

    supported = (
        get_performance_supported(
            results,
            "throughput_pages_per_second",
        )
    )

    names = get_names(
        supported
    )

    values = [
        result["performance"][
            "throughput_pages_per_second"
        ]
        for result in supported
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Pages per Second"
    )

    plt.title(
        "Parser Throughput"
    )

    add_value_labels(
        bars,
        3,
    )

    save_chart(
        "throughput.png"
    )


def plot_peak_memory(
    results: list[dict],
) -> None:

    supported = (
        get_performance_supported(
            results,
            "peak_memory_mb",
        )
    )

    if not supported:
        return

    names = get_names(
        supported
    )

    values = [
        result["performance"][
            "peak_memory_mb"
        ]
        for result in supported
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Peak Memory (MB)"
    )

    plt.title(
        "Peak Memory Usage"
    )

    add_value_labels(
        bars,
        2,
    )

    save_chart(
        "peak_memory.png"
    )


def plot_average_cpu(
    results: list[dict],
) -> None:

    supported = (
        get_performance_supported(
            results,
            "average_cpu_percent",
        )
    )

    if not supported:
        return

    names = get_names(
        supported
    )

    values = [
        result["performance"][
            "average_cpu_percent"
        ]
        for result in supported
    ]

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        names,
        values,
    )

    plt.ylabel(
        "Average Process CPU (%)"
    )

    plt.title(
        "Average CPU Utilization"
    )

    add_value_labels(
        bars,
        2,
    )

    save_chart(
        "average_cpu.png"
    )


# =========================================================
# SUMMARY HEATMAP
# =========================================================


def normalize_higher_better(
    values: list[float],
) -> list[float]:

    minimum = min(
        values
    )

    maximum = max(
        values
    )

    if maximum == minimum:
        return [
            1.0
            for _ in values
        ]

    return [
        (
            value - minimum
        )
        / (
            maximum - minimum
        )
        for value in values
    ]


def normalize_lower_better(
    values: list[float],
) -> list[float]:

    normalized = (
        normalize_higher_better(
            values
        )
    )

    return [
        1 - value
        for value in normalized
    ]


def plot_overall_heatmap(
    results: list[dict],
) -> None:
    """
    Creates a normalized overview using only metrics that
    are numerically comparable across ALL four approaches.

    Spatial table/image/layout metrics are intentionally
    excluded because some approaches do not support them.
    """

    names = get_names(
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

    coverage = [
        result["text_quality"][
            "text_coverage_percent"
        ]
        for result in results
    ]

    teds = [
        result["table_quality"][
            "teds_score"
        ]
        for result in results
    ]

    matrix = np.array(
        [
            normalize_lower_better(
                cer
            ),
            normalize_lower_better(
                wer
            ),
            normalize_higher_better(
                similarity
            ),
            normalize_higher_better(
                coverage
            ),
            normalize_higher_better(
                teds
            ),
        ]
    ).T

    metrics = [
        "CER",
        "WER",
        "Text Similarity",
        "Text Coverage",
        "TEDS-style",
    ]

    plt.figure(
        figsize=(10, 6)
    )

    image = plt.imshow(
        matrix,
        aspect="auto",
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
    )

    plt.colorbar(
        image,
        label="Relative Normalized Performance",
    )

    plt.xticks(
        np.arange(
            len(metrics)
        ),
        metrics,
        rotation=25,
        ha="right",
    )

    plt.yticks(
        np.arange(
            len(names)
        ),
        names,
    )

    for row in range(
        matrix.shape[0]
    ):

        for column in range(
            matrix.shape[1]
        ):

            plt.text(
                column,
                row,
                f"{matrix[row, column]:.2f}",
                ha="center",
                va="center",
            )

    plt.title(
        "Overall Comparable Quality Overview"
    )

    save_chart(
        "overall_quality_heatmap.png"
    )


# =========================================================
# MAIN
# =========================================================


def main():

    CHARTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = load_results()

    if not results:
        raise ValueError(
            "No final 63-page benchmark results found."
        )

    print(
        "=" * 60
    )

    print(
        "Final 63-Page Benchmark Visualization"
    )

    print(
        "=" * 60
    )

    print(
        f"Approaches: {len(results)}"
    )

    print()

    # Text
    plot_text_error_rates(
        results
    )

    plot_text_similarity(
        results
    )

    plot_text_coverage(
        results
    )

    # Tables
    plot_extracted_tables(
        results
    )

    plot_table_teds(
        results
    )

    plot_table_spatial_quality(
        results
    )

    # Images
    plot_image_counts(
        results
    )

    plot_image_quality(
        results
    )

    # Layout
    plot_layout_counts(
        results
    )

    plot_layout_quality(
        results
    )

    # Performance
    plot_execution_time(
        results
    )

    plot_seconds_per_page(
        results
    )

    plot_throughput(
        results
    )

    plot_peak_memory(
        results
    )

    plot_average_cpu(
        results
    )

    # Overall comparable summary
    plot_overall_heatmap(
        results
    )

    print()

    print(
        "=" * 60
    )

    print(
        "Visualization Complete"
    )

    print(
        "=" * 60
    )

    print(
        f"Charts saved to: {CHARTS_DIR}"
    )


if __name__ == "__main__":
    main()