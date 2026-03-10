from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .core.agent import build_default_pipeline
from .providers.search import SearchError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cited research brief from live web sources."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Research question to investigate. If omitted, the CLI prompts for it.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the final report.",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        help="Override the number of search results to process.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path for writing the report instead of printing only to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    query = " ".join(args.query).strip()
    if not query:
        query = input("Enter your research query: ").strip()

    if not query:
        parser.error("A research query is required.")

    settings = Settings.from_env()
    pipeline = build_default_pipeline(settings, max_search_results=args.max_sources)

    try:
        report = pipeline.run(query)
    except (SearchError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output = report.to_markdown()
    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2)

    if args.output:
        output_path = Path(args.output)
        if output.endswith("\n"):
            output_path.write_text(output, encoding="utf-8")
        else:
            output_path.write_text(f"{output}\n", encoding="utf-8")

    print(output)
    return 0
