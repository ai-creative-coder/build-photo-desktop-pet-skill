#!/usr/bin/env python3
"""Fail when a distributable skill contains private paths or unapproved raster assets."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {
    ".css", ".html", ".json", ".md", ".ps1", ".py", ".rs", ".toml",
    ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
RASTER_SUFFIXES = {".apng", ".avif", ".bmp", ".gif", ".heic", ".heif", ".icns", ".ico", ".jpeg", ".jpg", ".png", ".webp"}
# The skill owner explicitly authorized one generic chibi placeholder represented
# only by these derived cross-platform application-icon files. The original
# source image and its local path must never be bundled.
ALLOWED_RASTER_PATHS = {
    "assets/desktop-pet-template/src-tauri/icons/icon.icns",
    "assets/desktop-pet-template/src-tauri/icons/icon.ico",
    "assets/desktop-pet-template/src-tauri/icons/icon.png",
}
GENERIC_PATTERNS = {
    "absolute_windows_user_path": re.compile(r"(?i)[A-Z]:\\Users\\(?!__)[^\\\r\n]+"),
    "absolute_unix_user_path": re.compile(r"/(?:Users|home)/(?!__)[^/\r\n]+"),
    "camera_filename": re.compile(r"(?i)\b(?:IMG|DSC|PXL)[_-]?\d{4,}\b"),
}


def normalized(relative: Path | str) -> str:
    return str(relative).replace("\\", "/")


def scan_text(text: str, location: str, forbidden: list[str]) -> list[dict]:
    findings = []
    for label, pattern in GENERIC_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            if "__PRODUCT_NAME__" not in value:
                findings.append({"file": location, "rule": label, "value": value[:120]})
    lowered = text.casefold()
    for term in forbidden:
        if term.casefold() in lowered:
            findings.append({"file": location, "rule": "forbidden_term", "value": term})
    return findings


def scan_tree(root: Path, forbidden: list[str]) -> dict:
    findings = []
    raster_files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = normalized(path.relative_to(root))
        if path.suffix.lower() in RASTER_SUFFIXES:
            raster_files.append(relative)
            if relative not in ALLOWED_RASTER_PATHS:
                findings.append({"file": relative, "rule": "unexpected_raster_asset"})
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append({"file": relative, "rule": "non_utf8_text"})
            continue
        findings.extend(scan_text(text, relative, forbidden))
    return {"findings": findings, "raster_files": sorted(raster_files)}


def scan_zip(path: Path, forbidden: list[str]) -> dict:
    findings = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            normalized_name = name.replace("\\", "/")
            lowered_name = normalized_name.casefold()
            for term in forbidden:
                if term.casefold() in lowered_name:
                    findings.append({"file": normalized_name, "rule": "forbidden_term_in_zip_name", "value": term})
            suffix = Path(normalized_name).suffix.lower()
            relative = normalized_name.split("/", 1)[-1] if "/" in normalized_name else normalized_name
            if suffix in RASTER_SUFFIXES and relative not in ALLOWED_RASTER_PATHS:
                findings.append({"file": normalized_name, "rule": "unexpected_raster_asset"})
            if suffix in TEXT_SUFFIXES:
                try:
                    text = archive.read(name).decode("utf-8")
                except UnicodeDecodeError:
                    findings.append({"file": normalized_name, "rule": "non_utf8_text_in_zip"})
                else:
                    findings.extend(scan_text(text, normalized_name, forbidden))
        return {"findings": findings, "entries": len(names)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Skill directory")
    parser.add_argument("--zip", type=Path, dest="zip_path")
    parser.add_argument("--forbid", action="append", default=[], help="Case-insensitive term that must not occur")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Skill directory not found: {root}")
    tree = scan_tree(root, args.forbid)
    zip_report = scan_zip(args.zip_path, args.forbid) if args.zip_path else None
    findings = list(tree["findings"])
    if zip_report:
        findings.extend(zip_report["findings"])
    report = {
        "ok": not findings,
        "root": str(root),
        "raster_files": tree["raster_files"],
        "zip": str(args.zip_path) if args.zip_path else None,
        "zip_entries": zip_report["entries"] if zip_report else None,
        "findings": findings,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
