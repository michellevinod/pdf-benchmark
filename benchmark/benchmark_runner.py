from pathlib import Path

from benchmark.image_metrics import ImageMetrics
from benchmark.layout_metrics import LayoutMetrics
from benchmark.llm_judge import LLMJudge
from benchmark.profiler import Profiler
from benchmark.quality_metrics import QualityMetrics
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

    def __init__(self, pdf_path: str):

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

        for parser_name in self.parsers:

            print(f"\nRunning {parser_name}...")

            parser = ParserFactory.get_parser(parser_name)

            output_dir = (
                Path("outputs")
                / parser_name
            )

            markdown_path = output_dir / "output.md"

            json_path = output_dir / "output.json"

            profiler_results = Profiler.run(
                parser=parser,
                pdf_path=self.pdf_path,
                markdown_path=str(markdown_path),
                json_path=str(json_path),
            )

            result = {
                "parser": parser_name,
                **profiler_results,
            }

            if profiler_results["status"] == "Success":

                result.update(
                    TextMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    TableMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    LayoutMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    ImageMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    QualityMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    RobustnessMetrics.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

                result.update(
                    LLMJudge.evaluate(
                        pdf_path=self.pdf_path,
                        markdown_path=str(markdown_path),
                        json_path=str(json_path),
                    )
                )

            benchmark_results.append(result)

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