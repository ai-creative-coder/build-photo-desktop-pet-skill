#!/usr/bin/env python3
"""Build and collect a macOS Tauri .app and DMG on a Mac host."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from validate_release_review import validate_review
from validate_localization import validate_localization


GUIDES = ("DESKTOP_PET_USER_GUIDE.txt", "DESKTOP_PET_STATE_TRIGGER_GUIDE.md")


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(file_sha256(path)))
    return digest.hexdigest().upper()


def safe_name(value: str) -> str:
    cleaned = "".join("_" if char in '/\\:*?"<>|' else char for char in value).strip()
    return cleaned or "DesktopPet"


def has_notarization_credentials() -> bool:
    apple_id = all(os.environ.get(name) for name in ("APPLE_ID", "APPLE_PASSWORD", "APPLE_TEAM_ID"))
    api_key = all(
        os.environ.get(name)
        for name in ("APPLE_API_ISSUER", "APPLE_API_KEY", "APPLE_API_KEY_PATH")
    )
    return apple_id or api_key


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument(
        "--allow-unsigned",
        action="store_true",
        help="Create a local-test build without requiring Developer ID and notarization credentials.",
    )
    parser.add_argument(
        "--allow-limited-runtime",
        action="store_true",
        help="Build before a native macOS activity adapter is marked ready; do not distribute as full parity.",
    )
    args = parser.parse_args()

    if platform.system() != "Darwin":
        raise SystemExit("macOS release builds must run on a Mac host.")

    project = args.project.expanduser().resolve()
    config_path = project / "src-tauri" / "tauri.conf.json"
    mac_config_path = project / "src-tauri" / "tauri.macos.conf.json"
    if not config_path.is_file() or not mac_config_path.is_file():
        raise SystemExit("Missing Tauri base or macOS platform configuration.")
    run(["xcode-select", "-p"], project)

    config = load_json(config_path)
    product = str(config["productName"])
    version = str(config["version"])
    spec_path = project / "project-spec.json"
    spec = load_json(spec_path) if spec_path.is_file() else {}
    localization_errors = validate_localization(project)
    if localization_errors:
        raise SystemExit(
            "Language confirmation or localization review failed: "
            + "; ".join(localization_errors)
        )
    if spec.get("custom_icon_ready") is not True:
        raise SystemExit(
            "Project icons still use the bundled generic chibi placeholder. "
            "Run generate_project_icons.py with the approved standing RGBA base before packaging."
        )
    missing_icons = [
        str(project / "src-tauri" / "icons" / name)
        for name in ("icon.png", "icon.icns")
        if not (project / "src-tauri" / "icons" / name).is_file()
    ]
    if missing_icons:
        raise SystemExit("Missing generated project icons: " + ", ".join(missing_icons))
    review_errors = validate_review(project)
    if review_errors:
        raise SystemExit(
            "Final visual review failed or is missing: " + "; ".join(review_errors)
        )
    mac_runtime_ready = spec.get("macos_runtime_ready") is True
    if not mac_runtime_ready and not args.allow_limited_runtime:
        raise SystemExit(
            "macOS native runtime is not marked ready in project-spec.json. "
            "Implement and test it, or use --allow-limited-runtime only for a clearly labeled local preview."
        )

    signed_release = not args.allow_unsigned
    if signed_release:
        if not os.environ.get("APPLE_SIGNING_IDENTITY"):
            raise SystemExit("APPLE_SIGNING_IDENTITY is required for a distributable macOS release.")
        if not has_notarization_credentials():
            raise SystemExit("Apple notarization credentials are required for a distributable macOS release.")

    if not args.skip_install:
        run(["npm", "ci" if (project / "package-lock.json").is_file() else "install"], project)
    run(["npm", "run", "build"], project)
    run(["cargo", "test", "--manifest-path", str(project / "src-tauri" / "Cargo.toml")], project)
    run(["npm", "run", "tauri", "build", "--", "--bundles", "app,dmg"], project)

    bundle_root = project / "src-tauri" / "target" / "release" / "bundle"
    apps = sorted((bundle_root / "macos").glob("*.app"), key=lambda item: item.stat().st_mtime, reverse=True)
    dmgs = sorted((bundle_root / "dmg").glob("*.dmg"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not apps or not dmgs:
        raise SystemExit("Tauri did not produce both a .app and a DMG.")
    app = apps[0]
    dmg = dmgs[0]

    if signed_release:
        run(["codesign", "--verify", "--strict", "--verbose=2", str(app)], project)
        run(["spctl", "--assess", "--type", "execute", "--verbose=4", str(app)], project)
        run(["xcrun", "stapler", "validate", str(dmg)], project)

    release_root = (args.release_root or project / "output" / "releases").expanduser().resolve()
    architecture = platform.machine().lower()
    release_dir = release_root / f"{safe_name(product)}_{version}_macOS_{architecture}"
    release_dir.mkdir(parents=True, exist_ok=True)
    app_target = release_dir / f"{safe_name(product)}_{version}_macOS_{architecture}.app"
    dmg_target = release_dir / f"{safe_name(product)}_{version}_macOS_{architecture}.dmg"
    if app_target.exists():
        shutil.rmtree(app_target)
    shutil.copytree(app, app_target)
    shutil.copy2(dmg, dmg_target)
    for guide in GUIDES:
        source = project / guide
        if source.is_file():
            shutil.copy2(source, release_dir / guide)

    report = {
        "product": product,
        "version": version,
        "platform": "macOS",
        "architecture": architecture,
        "macos_runtime_ready": mac_runtime_ready,
        "signed_and_notarized_required": signed_release,
        "app": str(app_target),
        "app_tree_sha256": tree_sha256(app_target),
        "dmg": str(dmg_target),
        "dmg_bytes": dmg_target.stat().st_size,
        "dmg_sha256": file_sha256(dmg_target),
        "release_dir": str(release_dir),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
