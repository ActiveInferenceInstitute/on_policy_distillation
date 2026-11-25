#!/usr/bin/env python3
"""Admit the original pinned source before its real importer/parser operations."""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from types import ModuleType

BOOTSTRAP_SHA256 = "f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37"
SOURCE_MANIFEST_SHA256 = "43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51"
PINNED_COMMIT = "75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resource(name: str, expected: str) -> tuple[Path, bytes]:
    selected = os.environ.get(name)
    if not selected:
        raise ValueError(f"{name} must select the independently frozen producer resource")
    path = Path(selected)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"{name}: resource-hash-mismatch")
    return path, data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "digest"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--workflow", default=".github/workflows/ci.yml")
    parser.add_argument("--job", default="release-gate")
    parser.add_argument("--module")
    parser.add_argument("--class-name")
    parser.add_argument("--spec", action="append", default=[])
    args = parser.parse_args(argv)
    bootstrap_path, bootstrap_bytes = _resource("GNN_BOOTSTRAP", BOOTSTRAP_SHA256)
    manifest_path, manifest = _resource("GNN_SOURCE_MANIFEST", SOURCE_MANIFEST_SHA256)
    bootstrap = ModuleType("_opd_reviewed_gnn_bootstrap")
    bootstrap.__file__ = str(bootstrap_path)
    sys.modules[bootstrap.__name__] = bootstrap
    exec(compile(bootstrap_bytes, str(bootstrap_path), "exec", dont_inherit=True), bootstrap.__dict__)
    pin = bootstrap.read_pin(args.repo / "gnn/upstream.json")
    if pin.commit != PINNED_COMMIT or pin.tag != "v5.1.0":
        raise ValueError("consumer pin differs from the independently reviewed source manifest")
    source = args.source.resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    if args.action == "check":
        result = bootstrap.check_importer(
            args.repo,
            expected_commit=PINNED_COMMIT,
            expected_tag="v5.1.0",
            require_pointer=True,
            pointer_workflow=args.workflow,
            pointer_job=args.job,
            source_manifest=manifest,
            source_manifest_sha256=SOURCE_MANIFEST_SHA256,
            package_root=source / "src/gnn",
            origin_mode="source",
        )
        status = 0 if result["ok"] and result["qualified"] else 1
    else:
        if not args.module or not args.class_name or not args.spec:
            parser.error("digest requires --module, --class-name and --spec")
        tree = ast.parse((PROJECT_ROOT / "src/gnn/upstream.py").read_bytes())
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "DIGEST_DRIVER_SOURCE" for target in node.targets)
        )
        driver = ast.literal_eval(assignment.value)
        namespace = {"__name__": "_opd_authored_digest_driver"}
        arguments = ["--module", args.module, "--class-name", args.class_name]
        for spec in args.spec:
            arguments.extend(("--spec", spec))
        capture = io.StringIO()
        with bootstrap.qualified_source(
            pin,
            manifest=manifest,
            manifest_sha256=SOURCE_MANIFEST_SHA256,
            package_root=source / "src/gnn",
            origin_mode="source",
        ) as qualification:
            exec(compile(driver, "<authored-gnn-digest>", "exec", dont_inherit=True), namespace)
            with contextlib.redirect_stdout(capture):
                status = namespace["main"](arguments)
            result = json.loads(capture.getvalue())
        result["source_qualification"] = qualification
        if not qualification["ok"] or not qualification["imports_verified"]:
            raise ValueError("producer did not authenticate the complete verdict lifetime")
    if bootstrap_path.read_bytes() != bootstrap_bytes or manifest_path.read_bytes() != manifest:
        raise ValueError("independently frozen producer resource changed during the verdict")
    print(json.dumps(result, sort_keys=True, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
