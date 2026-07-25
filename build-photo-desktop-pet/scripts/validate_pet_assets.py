#!/usr/bin/env python3
"""Validate the final 13-state asset contract consumed by the Tauri template."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence


EXPECTED = {
    "idle.png": 12,
    "click.png": 12,
    "drag.png": 12,
    "stretch.png": 12,
    "thinking.png": 12,
    "coding.png": 12,
    "processing.png": 12,
    "debugging.png": 12,
    "error.png": 12,
    "drink-water.png": 12,
    "task-complete.png": 12,
    "new-message.png": 12,
    "break-reminder.png": 12,
}

MOTION_CONTRACT_NAMES = ("motion-contract.json", "motion-contract-v2.json")


def pixel_data(image: Image.Image):
    getter = getattr(image, "get_flattened_data", None)
    return getter() if getter else image.getdata()


def lower_baseline(alpha: Image.Image) -> int | None:
    bbox = alpha.getbbox()
    if not bbox:
        return None
    _, top, _, bottom = bbox
    region_top = max(top, bottom - max(1, round((bottom - top) * 0.22)))
    pixels = alpha.load()
    rows = [
        y
        for y in range(region_top, bottom)
        if any(pixels[x, y] >= 32 for x in range(alpha.width))
    ]
    return max(rows) if rows else None


def changed_pixel_count(first: Image.Image, other: Image.Image) -> int:
    difference = ImageChops.difference(first.convert("RGBA"), other.convert("RGBA"))
    return sum(1 for pixel in pixel_data(difference) if max(pixel) > 8)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assets_dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--width", type=int, default=384)
    parser.add_argument("--height", type=int, default=341)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    details = {}
    expected_assets = dict(EXPECTED)
    if not (args.assets_dir / "idle.png").exists() and (args.assets_dir / "idle.webp").exists():
        expected_assets.pop("idle.png")
        expected_assets["idle.webp"] = 12
    motion_contract = None
    motion_contract_path = None
    for candidate in MOTION_CONTRACT_NAMES:
        path = args.assets_dir / candidate
        if path.exists():
            motion_contract_path = path
            try:
                motion_contract = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{candidate}: cannot parse motion contract ({exc})")
            break
    if motion_contract is None and motion_contract_path is None:
        errors.append(
            "Missing motion-contract.json: semantic expression/joint/prop changes "
            "and fixed-anchor declarations are required"
        )

    for name, expected_frames in expected_assets.items():
        path = args.assets_dir / name
        if not path.exists():
            errors.append(f"Missing asset: {name}")
            continue
        try:
            source = Image.open(path)
            frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(source)]
        except Exception as exc:  # Pillow gives format-specific exceptions.
            errors.append(f"{name}: cannot decode ({exc})")
            continue
        if len(frames) != expected_frames:
            errors.append(f"{name}: decoded {len(frames)} frames, expected {expected_frames}")
        baselines = []
        for index, frame in enumerate(frames, start=1):
            if frame.size != (args.width, args.height):
                errors.append(f"{name} frame {index}: size {frame.size}, expected {(args.width, args.height)}")
                continue
            alpha = frame.getchannel("A")
            corners = [alpha.getpixel((0, 0)), alpha.getpixel((args.width - 1, 0)), alpha.getpixel((0, args.height - 1)), alpha.getpixel((args.width - 1, args.height - 1))]
            if any(corners):
                errors.append(f"{name} frame {index}: non-transparent corner")
            baseline = lower_baseline(alpha)
            if baseline is not None:
                baselines.append(baseline)

        baseline_range = max(baselines) - min(baselines) if baselines else None
        if baseline_range != 0:
            errors.append(
                f"{name}: stable lower baseline drifts by {baseline_range} px; expected 0"
            )

        unique_frames = len(
            {hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames}
        )
        max_changed_pixels = (
            max(changed_pixel_count(frames[0], frame) for frame in frames[1:])
            if len(frames) > 1
            else 0
        )
        visible_first = (
            sum(1 for value in pixel_data(frames[0].getchannel("A")) if value >= 32)
            if frames
            else 0
        )
        meaningful_threshold = max(160, round(visible_first * 0.005))
        if unique_frames < 3:
            errors.append(
                f"{name}: only {unique_frames} unique frames; expected at least 3 clean semantic key poses"
            )
        if max_changed_pixels < meaningful_threshold:
            errors.append(
                f"{name}: maximum visible change is {max_changed_pixels} pixels; "
                f"expected at least {meaningful_threshold} (one-pixel uniqueness hacks do not pass)"
            )

        state = Path(name).stem
        plan = motion_contract.get(state) if isinstance(motion_contract, dict) else None
        if not isinstance(plan, dict):
            errors.append(f"{name}: motion contract has no '{state}' plan")
        else:
            semantic_changes = plan.get("semantic_changes")
            if not isinstance(semantic_changes, list) or len(semantic_changes) < 2:
                errors.append(
                    f"{name}: motion plan must declare at least two expression/joint/prop changes"
                )
            fixed_anchor = plan.get("fixed_anchor")
            if not isinstance(fixed_anchor, dict):
                errors.append(f"{name}: motion plan is missing fixed_anchor")
            elif (
                fixed_anchor.get("whole_subject_translation") is not False
                or fixed_anchor.get("whole_subject_scaling") is not False
            ):
                errors.append(
                    f"{name}: whole-subject translation/scaling must both be false"
                )
        file_size = path.stat().st_size
        if file_size > 4_000_000:
            warnings.append(f"{name}: {file_size} bytes; review compression")
        details[name] = {
            "frames": len(frames),
            "unique_frames": unique_frames,
            "max_changed_pixels": max_changed_pixels,
            "meaningful_change_threshold": meaningful_threshold,
            "baseline_y_range": baseline_range,
            "bytes": file_size,
            "canvas": list(frames[0].size) if frames else None,
        }

    allowed_extras = set(MOTION_CONTRACT_NAMES) | {"asset-validation.json"}
    extras = sorted(
        p.name
        for p in args.assets_dir.iterdir()
        if p.is_file()
        and p.name not in expected_assets
        and p.name not in allowed_extras
        and not p.name.startswith(".")
    ) if args.assets_dir.exists() else []
    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "motion_contract": str(motion_contract_path) if motion_contract_path else None,
        "assets": details,
        "extra_files": extras,
    }
    target = args.report or (args.assets_dir / "asset-validation.json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
