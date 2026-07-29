import os
import platform
import socket
import threading
import time
import traceback
from datetime import datetime
from importlib.metadata import (
    PackageNotFoundError,
    version,
)
from pathlib import Path

import fitz
import psutil


class Profiler:
    """
    Profiles parser execution and collects benchmark metrics.
    """

    @staticmethod
    def run(
        parser,
        pdf_path: str,
        markdown_path: str,
        json_path: str,
    ):

        process = psutil.Process(os.getpid())

        pdf = fitz.open(pdf_path)
        page_count = len(pdf)
        pdf.close()

        memory_before = process.memory_info().rss
        peak_memory = memory_before

        cpu_samples = []

        monitoring = True

        status = "Success"
        error = None
        traceback_text = None

        benchmark_timestamp = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        try:
            parser_version = version(
                parser.__class__.__module__.split(".")[0]
            )

        except PackageNotFoundError:
            parser_version = "Unknown"

        def monitor():

            nonlocal peak_memory

            process.cpu_percent(None)

            while monitoring:

                memory = process.memory_info().rss

                if memory > peak_memory:
                    peak_memory = memory

                cpu_samples.append(
                    process.cpu_percent(interval=None)
                )

                time.sleep(0.05)

        monitor_thread = threading.Thread(
            target=monitor,
            daemon=True,
        )

        monitor_thread.start()

        start_time = time.perf_counter()

        try:

            parser.parse(
                pdf_path=pdf_path,
                markdown_path=markdown_path,
                json_path=json_path,
            )

        except Exception as exc:

            status = "Failed"
            error = str(exc)
            traceback_text = traceback.format_exc()

        finally:

            end_time = time.perf_counter()

            monitoring = False

            monitor_thread.join()

        memory_after = process.memory_info().rss

        markdown_file = Path(markdown_path)
        json_file = Path(json_path)

        markdown_size = (
            markdown_file.stat().st_size
            if markdown_file.exists()
            else 0
        )

        json_size = (
            json_file.stat().st_size
            if json_file.exists()
            else 0
        )

        output_size = markdown_size + json_size

        execution_time = end_time - start_time

        pages_per_second = (
            page_count / execution_time
            if execution_time > 0
            else 0
        )

        time_per_page = (
            execution_time / page_count
            if page_count > 0
            else 0
        )

        average_cpu = (
            sum(cpu_samples) / len(cpu_samples)
            if cpu_samples
            else 0
        )

        return {
            "benchmark_timestamp": benchmark_timestamp,

            "parser_name": parser.__class__.__name__,

            "parser_version": parser_version,

            "status": status,

            "error": error,

            "traceback": traceback_text,

            "pdf_name": Path(pdf_path).name,

            "page_count": page_count,

            "execution_time_seconds": round(
                execution_time,
                3,
            ),

            "processing_time_per_page_seconds": round(
                time_per_page,
                3,
            ),

            "throughput_pages_per_second": round(
                pages_per_second,
                3,
            ),

            "memory_before_mb": round(
                memory_before / (1024 ** 2),
                2,
            ),

            "memory_after_mb": round(
                memory_after / (1024 ** 2),
                2,
            ),

            "memory_used_mb": round(
                (memory_after - memory_before) / (1024 ** 2),
                2,
            ),

            "peak_memory_mb": round(
                peak_memory / (1024 ** 2),
                2,
            ),

            "average_cpu_percent": round(
                average_cpu,
                2,
            ),

            "output_size_kb": round(
                output_size / 1024,
                2,
            ),

            "python_version": platform.python_version(),

            "operating_system": platform.platform(),

            "machine_name": socket.gethostname(),

            "cpu_model": platform.processor(),

            "physical_cpu_cores": psutil.cpu_count(
                logical=False,
            ),

            "logical_cpu_cores": psutil.cpu_count(
                logical=True,
            ),

            "total_ram_gb": round(
                psutil.virtual_memory().total
                / (1024 ** 3),
                2,
            ),
        }