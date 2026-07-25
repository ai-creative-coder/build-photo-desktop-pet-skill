#!/usr/bin/env python3
"""Block desktop-pet packaging until the final visual review manifest passes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATES = {
    "idle", "click", "drag", "stretch", "thinking", "coding", "processing",
    "debugging", "error", "drink-water", "task-complete", "new-message",
    "break-reminder",
}
CHECKS = {
    "no_ghosting",
    "no_shaking_or_bobbing",
    "no_irregular_scaling",
    "no_action_cropping",
    "continuous_motion",
    "no_deformation_or_fragments",
    "no_floor_or_character_drop_shadow",
    "actual_size_loop_reviewed",
    "native_runtime_reviewed",
}


def validate_review(project: Path) -> list[str]:
    project = project.expanduser().resolve()
    review_path = project / "output" / "reviews" / "release-quality-decision.json"
    config_path = project / "src-tauri" / "tauri.conf.json"
    styles_path = project / "src" / "styles.css"
    errors: list[str] = []
    if not review_path.is_file():
        return [f"Missing final review manifest: {review_path}"]
    if not config_path.is_file():
        return [f"Missing Tauri config: {config_path}"]
    if not styles_path.is_file():
        return [f"Missing runtime stylesheet: {styles_path}"]

    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"Cannot read final review manifest: {error}"]

    if review.get("ok") is not True:
        errors.append("review.ok must be true")
    if review.get("version") != config.get("version"):
        errors.append("review.version must match src-tauri/tauri.conf.json")
    reviewed_states = review.get("states_reviewed")
    if not isinstance(reviewed_states, list) or set(reviewed_states) != STATES:
        errors.append("states_reviewed must contain all 13 states exactly once")
    checks = review.get("checks")
    if not isinstance(checks, dict):
        errors.append("review.checks must be an object")
    else:
        for name in sorted(CHECKS):
            if checks.get(name) is not True:
                errors.append(f"review.checks.{name} must be true")
    styles = styles_path.read_text(encoding="utf-8")
    if "drop-shadow(" in styles:
        errors.append("src/styles.css still contains a drop-shadow filter")
    for selector in (".integrated-pet-stage::after", ".idle-preview-stage::after"):
        if selector in styles:
            errors.append(f"src/styles.css still contains synthetic ground shadow selector {selector}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    errors = validate_review(args.project)
    report = {"ok": not errors, "errors": errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
