import argparse
import json
import sys
import os
from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.serializer import serialize_to_cii
from src.cii_roundtrip.export_csv import generate_custom_csv
from src.cii_roundtrip.import_csv import import_csv_to_cii
from src.cii_roundtrip.comparator import compare_files
from src.cii_roundtrip.optimizer import run_optimization_loop

def main():
    parser = argparse.ArgumentParser(description="CAESAR II Neutral File (.cii) Bi-Directional Parser")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Reconstruct Command
    recon_parser = subparsers.add_parser("reconstruct", help="Roundtrip a .cii file and compare/optimize")
    recon_parser.add_argument("--input", required=True, help="Original .neu or .cii file")
    recon_parser.add_argument("--out", required=True, help="Generated output .cii file")
    recon_parser.add_argument("--table", required=False, help="Path to export custom CSV table")
    recon_parser.add_argument("--table-in", required=False, help="Path to IMPORT custom CSV table back to CII")
    recon_parser.add_argument("--optimize", action="store_true", help="Run format optimization loop")
    recon_parser.add_argument("--report", required=False, help="Output JSON report file")

    # UI Command
    ui_parser = subparsers.add_parser("tui", help="Launch ASCII Dashboard")

    args = parser.parse_args()

    if args.command == "reconstruct":
        print(f"Loading {args.input}...")
        p = Parser(args.input, n1_allocation=2000)
        data = p.parse()

        if args.table_in:
            print(f"Importing table {args.table_in} over {args.input} base data...")
            data = import_csv_to_cii(args.table_in, base_cii_data=data)

        opt_report = None
        if args.optimize:
            print("Running Optimization Loop...")
            data, opt_report = run_optimization_loop(data)

        if args.table:
            print(f"Exporting table to {args.table}...")
            generate_custom_csv(data, export_path=args.table)

        print(f"Serializing to {args.out}...")
        serialize_to_cii(data, args.out)

        print(f"Comparing {args.input} vs {args.out}...")
        comp_report = compare_files(args.input, args.out)

        final_report = {
            "comparator": comp_report,
            "optimizer": opt_report
        }

        if comp_report["exact_match"]:
            print("SUCCESS: Exact character-by-character match achieved!")
        else:
            print(f"Mismatch: {comp_report['byte_diff_count']} bytes diff, {comp_report['line_diff_count']} lines diff.")
            print(f"Histogram: {comp_report['mismatches_histogram']}")

        if args.report:
            with open(args.report, "w") as f:
                json.dump(final_report, f, indent=4)
            print(f"JSON report saved to {args.report}")

    elif args.command == "tui":
        from src.cii_roundtrip.tui import DashboardApp
        app = DashboardApp()
        app.run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()