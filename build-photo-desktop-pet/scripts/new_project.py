#!/usr/bin/env python3
"""Create a generic Tauri desktop-pet project from the bundled template."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


TEXT_SUFFIXES = {".html", ".json", ".toml", ".rs", ".ts", ".tsx", ".txt", ".md"}
EXPECTED_ASSETS = [
    "idle.png",
    "click.png",
    "drag.png",
    "stretch.png",
    "thinking.png",
    "coding.png",
    "processing.png",
    "debugging.png",
    "error.png",
    "drink-water.png",
    "task-complete.png",
    "new-message.png",
    "break-reminder.png",
]


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "photo-desktop-pet"


def rust_identifier(slug: str) -> str:
    value = re.sub(r"[^a-z0-9_]", "_", slug.replace("-", "_"))
    if not value or not value[0].isalpha():
        value = "pet_" + value
    return value


def registry_key(product_name: str, slug: str) -> str:
    ascii_name = re.sub(r"[^A-Za-z0-9]", "", product_name)
    if ascii_name:
        return ascii_name[:48]
    digest = hashlib.sha1(product_name.encode("utf-8")).hexdigest()[:8]
    return "PhotoDesktopPet" + digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--product-name", default="我的桌宠")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--slug", default="photo-desktop-pet")
    parser.add_argument("--identifier")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        parser.error("--version must use semantic form such as 1.0.0")

    template = Path(__file__).resolve().parent.parent / "assets" / "desktop-pet-template"
    if not template.exists():
        raise SystemExit(f"Template missing: {template}")
    out = args.out.resolve()
    if out.exists():
        if not args.force:
            raise SystemExit(f"Output already exists: {out}. Use --force to replace it.")
        shutil.rmtree(out)
    shutil.copytree(template, out)
    (out / "public" / "assets" / "pet" / "integrated-v1").mkdir(parents=True, exist_ok=True)

    slug = normalize_slug(args.slug)
    crate = rust_identifier(slug)
    identifier = args.identifier or f"com.local.{slug}"
    substitutions = {
        "__PRODUCT_NAME__": args.product_name,
        "__PRODUCT_SLUG__": slug,
        "__RUST_CRATE__": crate,
        "__VERSION__": args.version,
        "__BUNDLE_ID__": identifier,
        "__REGISTRY_KEY__": registry_key(args.product_name, slug),
    }

    for path in out.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for token, replacement in substitutions.items():
            text = text.replace(token, replacement)
        path.write_text(text, encoding="utf-8", newline="\n")

    unresolved = []
    for path in out.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            if "__PRODUCT_" in path.read_text(encoding="utf-8") or "__RUST_CRATE__" in path.read_text(encoding="utf-8"):
                unresolved.append(str(path))
    if unresolved:
        raise SystemExit("Unresolved template tokens:\n" + "\n".join(unresolved))

    spec = {
        "product_name": args.product_name,
        "version": args.version,
        "slug": slug,
        "rust_crate": crate,
        "identifier": identifier,
        "canvas": [384, 341],
        "frame_count": 12,
        "platform_targets": ["windows", "macos"],
        "custom_icon_ready": False,
        "custom_icon_note": "Replace the bundled generic chibi placeholder with icons derived from the current user's approved neutral standing base before packaging.",
        "macos_runtime_ready": False,
        "macos_runtime_note": "Implement and test native macOS activity, permission and login-item adapters before claiming full automatic-state parity.",
        "asset_directory": "public/assets/pet/integrated-v1",
        "expected_assets": EXPECTED_ASSETS,
    }
    (out / "project-spec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"created": str(out), **spec}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
