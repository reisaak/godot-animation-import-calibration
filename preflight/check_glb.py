#!/usr/bin/env python3
"""Import Lens Free Preflight: a local structure check, not an import or quality test."""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat

VERSION = "1.0"
# Match the reviewed Import Lens 0.2 intake gates. See PROVENANCE.md.
MAX_BYTES = 25 * 1024 * 1024
MAX_WORKLOAD = 4_000_000
SAMPLE_RATES = (30, 60, 120)
SCOPE = ("Static structure and estimated sampling workload only. A pass does not "
         "guarantee Godot import or A/B correspondence, and says nothing about "
         "animation quality. No engine, measurements or repair are performed.")
EXITS = {"PREFLIGHT_PASS": 0, "UNSUPPORTED": 2, "MALFORMED": 3,
         "INPUT_ERROR": 4, "INPUT_CHANGED": 5, "SETUP_ERROR": 6}


class CommandLine(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(64, "Argument error: " + message + "\n")


def load_parser():
    path = Path(__file__).resolve().parent / "source" / "preflight.py"
    spec = importlib.util.spec_from_file_location("import_lens_free_preflight", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_file(path, rate, parser_module):
    result = {"tool": "Import Lens Free Preflight", "version": VERSION,
              "status": "INPUT_ERROR", "scope": SCOPE, "sample_rate": rate,
              "engine_invoked": False, "measurements_performed": False,
              "engine_import_verified": False, "correspondence_verified": False,
              "input_open_mode": "read-only", "files_written": False}
    descriptor = None
    snapshot = None
    try:
        path = path.expanduser()
        result["input_name"] = path.name
        if path.suffix.lower() != ".glb":
            result.update(status="MALFORMED", reason="Choose a regular .glb input file.")
            return result
        # O_NONBLOCK prevents accidentally opening a FIFO from waiting for a writer.
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                result["reason"] = "Choose a regular .glb file, not a directory or device."
                return result
            if before.st_size > MAX_BYTES:
                result.update(status="UNSUPPORTED", reason="Input exceeds the supported 25 MiB file limit.")
                return result
            snapshot = stream.read(MAX_BYTES + 1)
            if len(snapshot) > MAX_BYTES:
                result.update(status="UNSUPPORTED", reason="Input exceeds the supported 25 MiB file limit.")
                return result
            result.update(input_bytes=len(snapshot), input_sha256=hashlib.sha256(snapshot).hexdigest())
            try:
                info = parser_module.parse(snapshot)
                result["preflight"] = info
                pairs = sum((math.ceil(c["end_seconds"] * rate) + 1)
                            * info["source_split_vertices"] for c in info["clips"])
                result["workload"] = {"estimated_source_vertex_time_pairs": pairs,
                                      "maximum": MAX_WORKLOAD,
                                      "basis": "sum((ceil(clip end seconds × sample rate) + 1) × source split vertices)"}
                if pairs > MAX_WORKLOAD:
                    result.update(status="UNSUPPORTED", reason="Requested sampling exceeds 4,000,000 sampled vertices. Use a smaller asset, fewer clips or a lower sample rate.")
                else:
                    result.update(status="PREFLIGHT_PASS", reason="The shared structure checker and selected workload gate passed. Engine-dependent checks remain untested.")
            except parser_module.Rejected as exc:
                result.update(status=exc.kind, reason=exc.reason)
            except (TypeError, ValueError, KeyError, IndexError, RecursionError, AttributeError, OverflowError):
                result.update(status="MALFORMED", reason="Malformed GLB structure. No model was imported.")
            stream.seek(0)
            result["opened_input_bytes_unchanged"] = stream.read(MAX_BYTES + 1) == snapshot
            if not result["opened_input_bytes_unchanged"]:
                result.update(status="INPUT_CHANGED", reason="The opened file changed during this check. Run again on a stable copy.")
    except (OSError, ValueError):
        result.update(status="INPUT_ERROR", reason="Cannot read the requested regular .glb file. Check its path and read permission.")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return result


def show_text(result):
    lines = [result["status"], result["reason"], "", SCOPE]
    if "input_name" in result:
        # Escape control characters in filenames and model-authored labels.
        lines.append("File: " + json.dumps(result["input_name"], ensure_ascii=True))
    info = result.get("preflight")
    if info:
        lines.append(f"Structure: {info['source_split_vertices']:,} split vertices, {info['joint_count']} joints, {len(info['clips'])} clips")
        for clip in info["clips"]:
            lines.append("  " + json.dumps(clip["name"], ensure_ascii=True) + f": ends at {clip['end_seconds']:g} s")
    if "workload" in result:
        w = result["workload"]
        lines.append(f"Workload at {result['sample_rate']} samples/s: {w['estimated_source_vertex_time_pairs']:,} / {w['maximum']:,} source vertex/time pairs")
    print("\n".join(lines))


def main(argv=None):
    cli = CommandLine(description=SCOPE, epilog="Python 3.11 standard library. Output goes to stdout; this checker creates no reports, caches or project files.")
    cli.add_argument("input", type=Path, help="Local self-contained .glb file")
    cli.add_argument("--sample-rate", type=int, choices=SAMPLE_RATES, default=60,
                     help="Estimate the paid intake workload at this rate; no animation is sampled (default 60)")
    cli.add_argument("--format", choices=("text", "json"), default="text", help="stdout format (default text)")
    cli.add_argument("--version", action="version", version="Import Lens Free Preflight " + VERSION)
    args = cli.parse_args(argv)
    try:
        if sys.version_info < (3, 11):
            raise RuntimeError("Python 3.11 is required.")
        module = load_parser()
    except (OSError, ImportError, RuntimeError):
        result = {"status": "SETUP_ERROR", "reason": "Use Python 3.11 and keep source/preflight.py beside the supplied launcher.", "scope": SCOPE}
    else:
        result = inspect_file(args.input, args.sample_rate, module)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    else:
        show_text(result)
    return EXITS.get(result["status"], 6)


if __name__ == "__main__":
    raise SystemExit(main())
