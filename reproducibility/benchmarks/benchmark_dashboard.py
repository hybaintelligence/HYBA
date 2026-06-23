#!/usr/bin/env python3
"""
Benchmark Result Visualization Dashboard

Creates interactive dashboards for viewing benchmark results,
performance trends, and comparative analysis.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


class BenchmarkDashboard:
    """Creates visualization dashboards for benchmark results."""

    def __init__(self, results_dir: str = "benchmark_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.results: List[Dict[str, Any]] = []
        self._load_results()

    def _load_results(self) -> None:
        """Load all benchmark results from directory."""
        for result_file in sorted(self.results_dir.glob("*.json")):
            try:
                with open(result_file) as f:
                    self.results.append(json.load(f))
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {result_file}")

    def generate_html_dashboard(self, output_file: str = "dashboard.html") -> None:
        """Generate HTML dashboard for benchmark results."""
        html = self._generate_html_header()
        html += self._generate_summary_section()
        html += self._generate_trends_section()
        html += self._generate_comparison_section()
        html += self._generate_html_footer()

        with open(output_file, "w") as f:
            f.write(html)
        print(f"Dashboard saved to {output_file}")

    def _generate_html_header(self) -> str:
        """Generate HTML header."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HYBA Benchmark Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #666;
        }
        .metric-value {
            color: #333;
            font-weight: 600;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .status.passed {
            background: #d4edda;
            color: #155724;
        }
        .status.failed {
            background: #f8d7da;
            color: #721c24;
        }
        .status.timeout {
            background: #fff3cd;
            color: #856404;
        }
        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 HYBA Benchmark Dashboard</h1>
            <p class="subtitle">Performance metrics and trends for enterprise benchmarks</p>
        </header>
"""

    def _generate_summary_section(self) -> str:
        """Generate summary section."""
        html = '<div class="grid">\n'

        if self.results:
            latest = self.results[-1]

            # Latest run summary
            html += '<div class="card">\n'
            html += "<h2>Latest Run</h2>\n"

            html += '<div class="metric">\n'
            html += '<span class="metric-label">Timestamp:</span>\n'
            html += (
                f'<span class="metric-value">{latest.get("timestamp", "N/A")}</span>\n'
            )
            html += "</div>\n"

            html += '<div class="metric">\n'
            html += '<span class="metric-label">Commit:</span>\n'
            html += f'<span class="metric-value"><code>{latest.get("git_commit", "N/A")[:8]}</code></span>\n'
            html += "</div>\n"

            sys_info = latest.get("system_info", {})
            html += '<div class="metric">\n'
            html += '<span class="metric-label">CPU Cores:</span>\n'
            html += f'<span class="metric-value">{sys_info.get("cpu_count", "N/A")}</span>\n'
            html += "</div>\n"

            html += '<div class="metric">\n'
            html += '<span class="metric-label">Memory:</span>\n'
            memory_gb = sys_info.get("memory_total_gb", 0)
            html += f'<span class="metric-value">{memory_gb:.2f} GB</span>\n'
            html += "</div>\n"

            html += "</div>\n"

            # Benchmark status summary
            html += '<div class="card">\n'
            html += "<h2>Benchmark Status</h2>\n"

            benchmarks = latest.get("benchmarks", {})
            for bench_name, result in benchmarks.items():
                status = result.get("status", "unknown")
                status_class = (
                    "passed"
                    if status == "passed"
                    else "failed" if status == "failed" else "timeout"
                )
                html += '<div class="metric">\n'
                html += f'<span class="metric-label">{bench_name}:</span>\n'
                html += f'<span class="status {status_class}">{status.upper()}</span>\n'
                html += "</div>\n"

            html += "</div>\n"

        html += "</div>\n"
        return html

    def _generate_trends_section(self) -> str:
        """Generate trends section."""
        html = '<div class="card">\n'
        html += "<h2>Performance Trends</h2>\n"
        html += '<div class="chart-container">\n'
        html += '<canvas id="trendsChart"></canvas>\n'
        html += "</div>\n"

        # Extract data for charting
        dates = []
        passed_counts = []

        for result in sorted(self.results, key=lambda r: r.get("timestamp", "")):
            dates.append(result.get("timestamp", "")[:10])
            benchmarks = result.get("benchmarks", {})
            passed = sum(1 for r in benchmarks.values() if r.get("status") == "passed")
            passed_counts.append(passed)

        html += (
            """
        <script>
            const ctx = document.getElementById('trendsChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: """
            + json.dumps(dates)
            + """,
                    datasets: [{
                        label: 'Passed Benchmarks',
                        data: """
            + json.dumps(passed_counts)
            + """,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
        """
        )

        html += "</div>\n"
        return html

    def _generate_comparison_section(self) -> str:
        """Generate comparison section."""
        html = '<div class="card">\n'
        html += "<h2>Benchmark Comparison</h2>\n"
        html += '<div class="chart-container">\n'
        html += '<canvas id="comparisonChart"></canvas>\n'
        html += "</div>\n"

        if self.results:
            latest = self.results[-1]
            benchmarks = latest.get("benchmarks", {})
            bench_names = list(benchmarks.keys())
            bench_status = [
                1 if benchmarks[name].get("status") == "passed" else 0
                for name in bench_names
            ]

            html += (
                """
            <script>
                const ctx2 = document.getElementById('comparisonChart').getContext('2d');
                new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: """
                + json.dumps(bench_names)
                + """,
                        datasets: [{
                            label: 'Status (1=Passed, 0=Failed)',
                            data: """
                + json.dumps(bench_status)
                + """,
                            backgroundColor: [
                                '#28a745',
                                '#dc3545',
                                '#ffc107'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1
                            }
                        }
                    }
                });
            </script>
            """
            )

        html += "</div>\n"
        return html

    def _generate_html_footer(self) -> str:
        """Generate HTML footer."""
        return (
            """
        <footer>
            <p>HYBA Benchmark Dashboard | Generated """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
        </footer>
    </div>
</body>
</html>
"""
        )

    def generate_markdown_report(
        self, output_file: str = "BENCHMARK_ANALYSIS.md"
    ) -> None:
        """Generate markdown analysis report."""
        report = []
        report.append("# Benchmark Analysis Report\n\n")

        if not self.results:
            report.append("No benchmark results found.\n")
        else:
            report.append("## Summary\n\n")
            report.append(f"- **Total Runs**: {len(self.results)}\n")
            report.append(
                f"- **Date Range**: {self.results[0].get('timestamp')} to {self.results[-1].get('timestamp')}\n\n"
            )

            report.append("## Latest Results\n\n")
            latest = self.results[-1]
            benchmarks = latest.get("benchmarks", {})

            for bench_name, result in benchmarks.items():
                status = result.get("status", "unknown")
                report.append(f"- **{bench_name}**: {status.upper()}\n")

            report.append("\n## Performance Trends\n\n")

            # Calculate pass rate trend
            passed_rates = []
            for result in self.results:
                benchmarks = result.get("benchmarks", {})
                total = len(benchmarks)
                if total > 0:
                    passed = sum(
                        1 for r in benchmarks.values() if r.get("status") == "passed"
                    )
                    rate = (passed / total) * 100
                    passed_rates.append(rate)

            if passed_rates:
                avg_rate = sum(passed_rates) / len(passed_rates)
                report.append(f"- **Average Pass Rate**: {avg_rate:.1f}%\n")

        with open(output_file, "w") as f:
            f.write("".join(report))
        print(f"Analysis report saved to {output_file}")


def main():
    """Entry point for dashboard generation."""
    # Create results directory if it doesn't exist
    Path("benchmark_results").mkdir(exist_ok=True)

    dashboard = BenchmarkDashboard()
    dashboard.generate_html_dashboard("benchmark_dashboard.html")
    dashboard.generate_markdown_report("BENCHMARK_ANALYSIS.md")

    print("Dashboard generation complete!")


if __name__ == "__main__":
    main()
