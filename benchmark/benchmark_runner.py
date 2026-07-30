import json
from pathlib import Path

from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.llm_judge import LLMJudge
from benchmark.profiler import Profiler
from benchmark.reference_extractor import ReferenceExtractor
from benchmark.report_generator import ReportGenerator
from benchmark.robustness_metrics import RobustnessMetrics
from benchmark.table_metrics import TableMetrics
from benchmark.text_metrics import TextMetrics
from parsers.parser_factory import ParserFactory


class BenchmarkRunner:
    """
    Runs all configured parsers on the benchmark PDF
    and evaluates their outputs.
    """

    def __init__(
        self,
        pdf_path: str,
    ):

        self.pdf_path = pdf_path

        self.parsers = [
            "docling",
            "liteparse",
            "pymupdf4llm",
        ]

    def run(self):

        print("=" * 60)
        print("PDF Benchmark Started")
        print("=" * 60)

        benchmark_results = []

        reference_pages = ReferenceExtractor.extract_text(
            self.pdf_path,
        )

        reference_table_count = (
            ReferenceExtractor.extract_table_count(
                self.pdf_path,
            )
        )

        reference_image_count = (
            ReferenceExtractor.extract_image_count(
                self.pdf_path,
            )
        )

        for parser_name in self.parsers:

            print(f"\nRunning {parser_name}...")

            parser = ParserFactory.get_parser(
                parser_name,
            )

            output_dir = (
                Path("outputs")
                / parser_name
            )

            markdown_path = (
                output_dir
                / "output.md"
            )

            json_path = (
                output_dir
                / "output.json"
            )

            normalized_path = (
                output_dir
                / "normalized.json"
            )

            profiler_results = Profiler.run(
                parser=parser,
                pdf_path=self.pdf_path,
                markdown_path=str(
                    markdown_path,
                ),
                json_path=str(
                    json_path,
                ),
            )

            result = {
                "parser": parser_name,
                **profiler_results,
            }

            if profiler_results["status"] == "Success":

                with open(
                    normalized_path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    normalized_document = json.load(
                        file,
                    )

                result.update(
                    TextMetrics.evaluate(
                        normalized_document,
                        reference_pages,
                    )
                )

                result.update(
                    TableMetrics.evaluate(
                        normalized_document,
                        reference_table_count,
                    )
                )

                result.update(
                    ImageMetrics.evaluate(
                        normalized_document,
                        reference_image_count,
                    )
                )

                result.update(
                    LayoutMetrics.evaluate(
                        normalized_document,
                    )
                )

                result.update(
                    RobustnessMetrics.evaluate(
                        normalized_document,
                    )
                )

                result.update(
                    LLMJudge.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(
                            markdown_path,
                        ),
                        json_path=str(
                            json_path,
                        ),
                    )
                )

            benchmark_results.append(
                result,
            )

            print(
                f"{parser_name}: {result['status']}"
            )

        ReportGenerator.save_json(
            benchmark_results,
            "results/benchmark_results.json",
        )

        ReportGenerator.save_csv(
            benchmark_results,
            "results/benchmark_results.csv",
        )

        print("\n" + "=" * 60)
        print("Benchmark Completed")
        print("=" * 60)

        for result in benchmark_results:

            print("\n" + "-" * 60)

            print(
                f"Parser : {result['parser']}"
            )

            print(
                f"Status : {result['status']}"
            )

            print(
                f"Time   : {result['execution_time_seconds']} sec"
            )

            print(
                f"Pages  : {result['page_count']}"
            )

            print(
                f"Speed  : {result['throughput_pages_per_second']} pages/sec"
            )

            print(
                f"Peak RAM : {result['peak_memory_mb']} MB"
            )

            if result["status"] != "Success":

                print(
                    f"Error : {result['error']}"
                )


if __name__ == "__main__":

    runner = BenchmarkRunner(
        pdf_path="benchmark_dataset/PDF_Benchmarking_Tester.pdf",
    )

    runner.run()