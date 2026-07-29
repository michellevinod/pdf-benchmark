# Experiment Log

## Experiment 1

Date:
2026-07-28

Objective:
Integrate Docling into the benchmarking framework.

Result:
Success

Observations:
- Markdown exported successfully.
- Minor page transition issue observed.
- Mentor reviewed output and accepted it.


## Experiment 5

Objective:
Validate the BenchmarkRunner by executing all integrated parsers sequentially.

Result:
Success

Observations:
- All three parsers completed successfully.
- Total wall-clock time for the initial run was approximately 7 minutes.
- This run is not considered a benchmark because it may include one-time initialization such as model loading, dependency initialization, and cache creation.

Next Step:
Implement automated profiling and perform multiple benchmark runs under identical conditions.
