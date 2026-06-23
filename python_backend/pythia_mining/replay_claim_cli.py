#!/usr/bin/env python3
"""Replay and stress-test a local reproducibility claim manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.manifest_registry import (  # noqa: E402
    list_claims,
    load_and_reverify,
    save_verified_manifest,
)
from pythia_mining.replay_reporting import (  # noqa: E402
    build_verification_report,
    write_report_html,
    write_report_json,
)
from pythia_mining.replay_executor import (  # noqa: E402
    ReplayExecutionError,
    execute_falsification_probe,
    execute_reproducibility_replay,
    replay_stress_test,
    run_full_falsification_suite,
)

SUBCOMMANDS = {
    "replay",
    "stress",
    "falsify",
    "falsify-all",
    "register",
    "list",
    "reverify",
    "report",
}


def _normalize_subcommand_args(argv: list[str] | None) -> list[str] | None:
    if not argv or argv[0] not in SUBCOMMANDS:
        return argv
    command, rest = argv[0], list(argv[1:])
    if command == "replay":
        return rest
    if command == "stress":
        if not rest:
            return rest
        manifest = rest[0]
        runs = "50"
        tail = rest[1:]
        if "--runs" in tail:
            idx = tail.index("--runs")
            runs = tail[idx + 1]
            tail = tail[:idx] + tail[idx + 2 :]
        return [manifest, "--stress", runs, *tail]
    if command == "falsify":
        if len(rest) < 2:
            return rest
        manifest, route, *tail = rest
        return [manifest, "--falsify", route, *tail]
    if command == "falsify-all":
        if not rest:
            return rest
        manifest, *tail = rest
        return [manifest, "--falsify-all", *tail]
    if command == "register":
        if len(rest) < 2:
            return rest
        manifest, registry, *tail = rest
        return [manifest, "--register", registry, *tail]
    if command == "list":
        if not rest:
            return rest
        registry, *tail = rest
        return ["--list", registry, *tail]
    if command == "reverify":
        if len(rest) < 2:
            return rest
        registry, claim_id, *tail = rest
        return ["--list", registry, "--reverify", claim_id, *tail]
    if command == "report":
        if not rest:
            return rest
        manifest, *tail = rest
        if "--json-path" in tail:
            idx = tail.index("--json-path")
            tail[idx] = "--report-json"
        if "--html-path" in tail:
            idx = tail.index("--html-path")
            tail[idx] = "--report-html"
        return [manifest, *tail]
    return argv


def _load_claim(path: Path, claim_id: str | None = None) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if "claim" in manifest and isinstance(manifest["claim"], dict):
        return manifest["claim"]
    claims = manifest.get("claims", [])
    if not isinstance(claims, list) or not claims:
        raise ReplayExecutionError(
            "manifest must contain claim or non-empty claims list"
        )
    if claim_id:
        for claim in claims:
            if claim.get("id") == claim_id:
                return claim
        raise ReplayExecutionError(f"claim id not found: {claim_id}")
    return claims[0]


def _route(claim: dict[str, Any], name: str) -> dict[str, Any]:
    for route in claim.get("falsification_routes", []):
        if route.get("name") == name:
            return route
    raise ReplayExecutionError(f"falsification route not found: {name}")


def main(argv: list[str] | None = None) -> int:
    argv = _normalize_subcommand_args(argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--claim-id")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--stress", type=int, default=0)
    parser.add_argument("--falsify")
    parser.add_argument("--falsify-all", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--register", type=Path, help="Save verified manifest to a local registry"
    )
    parser.add_argument(
        "--list", type=Path, help="List a local manifest registry and exit"
    )
    parser.add_argument(
        "--reverify", help="Load claim id from --list registry and re-run replay"
    )
    parser.add_argument("--report-json", type=Path, help="Write structured JSON report")
    parser.add_argument("--report-html", type=Path, help="Write HTML report")
    args = parser.parse_args(argv)

    report = None
    try:
        if args.list and not args.reverify:
            records = list_claims(args.list)
            if args.as_json:
                print(
                    json.dumps(
                        {"ok": True, "records": [r.to_dict() for r in records]},
                        sort_keys=True,
                    )
                )
            else:
                for record in records:
                    print(
                        f"{record.claim_id} {record.input_digest} {record.output_digest}"
                    )
            return 0
        if args.list and args.reverify:
            result = load_and_reverify(args.list, args.reverify)
            if args.as_json:
                print(
                    json.dumps(
                        (
                            report.to_dict()
                            if report is not None
                            else {"ok": True, "result": result.to_dict()}
                        ),
                        sort_keys=True,
                    )
                )
            else:
                print(f"✅ Registry replay verified: {result.record.claim_id}")
            return 0
        if args.manifest is None:
            raise ReplayExecutionError(
                "manifest path is required unless --list is used"
            )
        claim = _load_claim(args.manifest, args.claim_id)
        attestation = claim["reproducibility_attestation"]
        if args.falsify_all:
            result = run_full_falsification_suite(claim, cwd=args.cwd)
            if result.failures:
                raise ReplayExecutionError("; ".join(result.failures))
            message = f"✅ Falsification suite verified: {result.claim_id} ({result.coverage_percent:.1f}% coverage)"
        elif args.falsify:
            route = _route(claim, args.falsify)
            result = execute_falsification_probe(
                attestation,
                seed_overrides=route.get("seed_overrides", {}),
                dependency_pin_overrides=route.get("dependency_pin_overrides", {}),
                cwd=args.cwd,
            )
            message = f"✅ Falsification verified: {result.claim_id}"
        elif args.stress:
            result = replay_stress_test(attestation, runs=args.stress, cwd=args.cwd)
            message = (
                f"✅ Stress replay verified: {result.claim_id} ({result.runs} runs)"
            )
        else:
            result = execute_reproducibility_replay(attestation, cwd=args.cwd)
            message = f"✅ Replay verified: {result.claim_id}"
        if args.register:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            record = save_verified_manifest(
                manifest, args.register, source_cwd=args.cwd
            )
            message += f"; registered {record.record_key}"
        report = build_verification_report(
            ok=True,
            operation="replay_claim",
            result=result,
            message=message,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures
        report = build_verification_report(
            ok=False,
            operation="replay_claim",
            error=exc,
            message="Replay verification failed",
        )
        if args.report_json:
            write_report_json(report, args.report_json)
        if args.report_html:
            write_report_html(report, args.report_html)
        if args.as_json:
            print(json.dumps(report.to_dict(), sort_keys=True))
        else:
            print(f"❌ Replay failed: {exc}", file=sys.stderr)
        return 1

    if args.report_json and report is not None:
        write_report_json(report, args.report_json)
    if args.report_html and report is not None:
        write_report_html(report, args.report_html)

    if args.as_json:
        print(
            json.dumps(
                (
                    report.to_dict()
                    if report is not None
                    else {"ok": True, "result": result.to_dict()}
                ),
                sort_keys=True,
            )
        )
    else:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
