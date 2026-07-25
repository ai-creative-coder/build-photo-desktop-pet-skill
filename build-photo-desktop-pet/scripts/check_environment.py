#!/usr/bin/env python3
"""Check the local toolchain required to build a Windows or macOS desktop pet."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys


def version(executable: str | None, args: list[str]) -> str | None:
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, *args], capture_output=True, text=True, timeout=10, check=False
        )
    except OSError:
        return None
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--target", choices=("auto", "windows", "macos"), default="auto")
    args = parser.parse_args()

    host_system = platform.system()
    target = args.target
    if target == "auto":
        target = "windows" if host_system == "Windows" else "macos" if host_system == "Darwin" else "unsupported"

    executables = {
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "cargo": shutil.which("cargo"),
        "rustc": shutil.which("rustc"),
        "powershell": shutil.which("powershell") or shutil.which("pwsh"),
        "xcode_select": shutil.which("xcode-select"),
        "xcrun": shutil.which("xcrun"),
        "codesign": shutil.which("codesign"),
        "spctl": shutil.which("spctl"),
    }
    report = {
        "host_system": host_system,
        "target": target,
        "python": {
            "ok": sys.version_info >= (3, 10),
            "version": platform.python_version(),
            "path": sys.executable,
        },
        "pillow": importlib.util.find_spec("PIL") is not None,
        "tools": {
            "node": {"path": executables["node"], "version": version(executables["node"], ["--version"])},
            "npm": {"path": executables["npm"], "version": version(executables["npm"], ["--version"])},
            "cargo": {"path": executables["cargo"], "version": version(executables["cargo"], ["--version"])},
            "rustc": {"path": executables["rustc"], "version": version(executables["rustc"], ["--version"])},
            "powershell": {"path": executables["powershell"]},
            "xcode_select": {"path": executables["xcode_select"]},
            "xcrun": {"path": executables["xcrun"]},
            "codesign": {"path": executables["codesign"]},
            "spctl": {"path": executables["spctl"]},
        },
        "external_requirements": [
            "Codex built-in image_gen tool, or a user-configured and explicitly approved external image provider/API through external_image_provider.py"
        ],
    }
    missing = []
    if target == "windows":
        report["external_requirements"].append(
            "Microsoft WebView2 runtime (the installer may bootstrap it)"
        )
        if host_system != "Windows":
            missing.append("Windows host")
    elif target == "macos":
        report["external_requirements"].extend(
            [
                "Xcode Command Line Tools",
                "Developer ID and notarization credentials for shareable distribution",
            ]
        )
        if host_system != "Darwin":
            missing.append("macOS host")
    else:
        missing.append("supported target")
    if not report["python"]["ok"]:
        missing.append("Python >= 3.10")
    if not report["pillow"]:
        missing.append("Pillow")
    common_tools = ("node", "npm", "cargo", "rustc")
    target_tools = ("powershell",) if target == "windows" else ("xcode_select", "xcrun", "codesign", "spctl")
    for name in (*common_tools, *target_tools):
        details = report["tools"][name]
        if not details["path"]:
            missing.append(name)
    report["ok"] = not missing
    report["missing"] = missing

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Environment ready: {'yes' if report['ok'] else 'no'}")
        print(f"Host: {host_system}")
        print(f"Target: {target}")
        print(f"Python: {report['python']['version']} ({report['python']['path']})")
        print(f"Pillow: {report['pillow']}")
        for name, details in report["tools"].items():
            print(f"{name}: {details.get('version') or details.get('path') or 'missing'}")
        if missing:
            print("Missing: " + ", ".join(missing))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
