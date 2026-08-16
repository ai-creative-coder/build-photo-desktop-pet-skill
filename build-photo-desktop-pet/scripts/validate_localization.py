#!/usr/bin/env python3
"""Validate the confirmed language and current-release localization decision."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_SURFACES = {
    "motion_bubbles",
    "state_labels",
    "context_menu",
    "settings_panel",
    "tray_menu",
    "accessibility_labels",
    "native_errors_and_permissions",
    "installer_ui",
    "user_guide",
    "state_trigger_guide",
}
REQUIRED_FILES = {
    "src/petMotions.ts",
    "src/petStates.ts",
    "src/IdlePreview.tsx",
    "src/App.tsx",
    "src-tauri/src/lib.rs",
    "src-tauri/tauri.windows.conf.json",
    "DESKTOP_PET_USER_GUIDE.txt",
    "DESKTOP_PET_STATE_TRIGGER_GUIDE.md",
}
DEFAULT_CHINESE_PHRASES = (
    "随机更换状态",
    "消息提醒：已开启",
    "消息提醒：已关闭",
    "退出桌宠",
    "提醒与行为",
    "恢复默认设置",
    "桌宠设置",
    "喝水提醒",
    "休息提醒",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_simplified_chinese(locale: str) -> bool:
    return locale.lower() in {"zh-cn", "zh-hans", "zh-sg"}


def validate_localization(project: Path) -> list[str]:
    errors: list[str] = []
    spec_path = project / "project-spec.json"
    decision_path = project / "output" / "reviews" / "localization-decision.json"
    if not spec_path.is_file():
        return ["project-spec.json is missing"]
    spec = read_json(spec_path)
    language = str(spec.get("pet_language", "")).strip()
    locale = str(spec.get("pet_locale", "")).strip()
    if spec.get("language_confirmed") is not True:
        errors.append("project-spec.language_confirmed must be true")
    if not language:
        errors.append("project-spec.pet_language is missing")
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", locale):
        errors.append("project-spec.pet_locale must be a BCP 47-style tag")
    if spec.get("localization_ready") is not True:
        errors.append("project-spec.localization_ready must be true")
    if not decision_path.is_file():
        errors.append("output/reviews/localization-decision.json is missing")
        return errors

    decision = read_json(decision_path)
    if decision.get("ok") is not True:
        errors.append("localization decision ok must be true")
    if str(decision.get("version", "")) != str(spec.get("version", "")):
        errors.append("localization decision version does not match project-spec")
    if str(decision.get("pet_language", "")).strip() != language:
        errors.append("localization decision language does not match project-spec")
    if str(decision.get("pet_locale", "")).strip().lower() != locale.lower():
        errors.append("localization decision locale does not match project-spec")

    surfaces = decision.get("surfaces")
    if not isinstance(surfaces, dict):
        errors.append("localization decision surfaces must be an object")
    else:
        for name in sorted(REQUIRED_SURFACES):
            if surfaces.get(name) is not True:
                errors.append(f"localization surface {name} must be true")

    reviewed = decision.get("reviewed_files")
    reviewed_set = set(reviewed) if isinstance(reviewed, list) else set()
    for relative in sorted(REQUIRED_FILES):
        if relative not in reviewed_set:
            errors.append(f"required localized file was not reviewed: {relative}")
        if not (project / relative).is_file():
            errors.append(f"required localized file is missing: {relative}")

    if locale and not is_simplified_chinese(locale):
        for relative in sorted(REQUIRED_FILES):
            path = project / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for phrase in DEFAULT_CHINESE_PHRASES:
                if phrase in text:
                    errors.append(f"default Simplified Chinese copy remains in {relative}: {phrase}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    errors = validate_localization(project)
    print(json.dumps({"ok": not errors, "project": str(project), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
