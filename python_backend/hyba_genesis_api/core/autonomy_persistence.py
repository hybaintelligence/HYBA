"""Autonomy report persistence for PYTHIA."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

# Default directory for storing autonomy reports
DEFAULT_REPORT_DIR = Path(__file__).resolve().parents[3] / "runtime" / "evidence" / "pythia_autonomy"


def ensure_report_dir(report_dir: Path = DEFAULT_REPORT_DIR) -> None:
    """Ensure the report directory exists."""
    report_dir.mkdir(parents=True, exist_ok=True)


def generate_report_filename(timestamp: Optional[datetime] = None) -> str:
    """Generate a filename for the report using ISO 8601 format (UTC)."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    # Use a filesystem-safe format (replace colon with hyphen, remove 'T' and 'Z')
    return f"{timestamp.strftime('%Y-%m-%dT%H-%M-%SZ')}.json"


def save_autonomy_report(
    report: Dict[str, Any],
    report_type: str = "reflexive_cycle",
    report_dir: Path = DEFAULT_REPORT_DIR,
) -> Path:
    """Save an autonomy report to a JSON file.

    Args:
        report: The report data to save
        report_type: Type of report (e.g., "startup", "reflexive_cycle")
        report_dir: Directory to save the report in

    Returns:
        Path to the saved report file
    """
    ensure_report_dir(report_dir)
    timestamp = datetime.now(timezone.utc)
    filename = generate_report_filename(timestamp)
    report_path = report_dir / filename

    # Enrich the report with metadata
    enriched_report = {
        "report_type": report_type,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "report": report,
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(enriched_report, f, ensure_ascii=False, indent=2)

    LOGGER.info("Saved autonomy report", extra={"report_path": str(report_path), "report_type": report_type})
    return report_path


def get_latest_report(report_dir: Path = DEFAULT_REPORT_DIR) -> Optional[Dict[str, Any]]:
    """Get the most recent autonomy report.

    Args:
        report_dir: Directory to look for reports in

    Returns:
        The latest report data, or None if no reports exist
    """
    ensure_report_dir(report_dir)
    report_files = sorted(report_dir.glob("*.json"), reverse=True)
    if not report_files:
        return None

    latest_file = report_files[0]
    try:
        with latest_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LOGGER.error("Failed to read latest report", extra={"error": str(e), "file": str(latest_file)})
        return None


def list_all_reports(report_dir: Path = DEFAULT_REPORT_DIR, limit: int = 100) -> list[Dict[str, Any]]:
    """List all available autonomy reports (metadata only).

    Args:
        report_dir: Directory to look for reports in
        limit: Maximum number of reports to return (most recent first)

    Returns:
        List of report metadata dictionaries
    """
    ensure_report_dir(report_dir)
    report_files = sorted(report_dir.glob("*.json"), reverse=True)[:limit]
    reports = []
    for file in report_files:
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                reports.append({
                    "filename": file.name,
                    "report_type": data.get("report_type"),
                    "timestamp": data.get("timestamp"),
                })
        except Exception as e:
            LOGGER.error("Failed to read report metadata", extra={"error": str(e), "file": str(file)})
    return reports
