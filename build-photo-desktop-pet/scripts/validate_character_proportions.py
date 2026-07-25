#!/usr/bin/env python3
"""Validate an upright chibi base from explicit top/chin/sole landmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--top-y", required=True, type=int, help="Highest hair/hat point.")
    parser.add_argument("--chin-y", required=True, type=int, help="Bottom of the chin.")
    parser.add_argument("--baseline-y", required=True, type=int, help="Shared sole baseline.")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--min-heads", type=float, default=2.6)
    parser.add_argument("--max-heads", type=float, default=2.7)
    parser.add_argument("--min-head-fraction", type=float, default=0.37)
    parser.add_argument("--max-head-fraction", type=float, default=0.39)
    args = parser.parse_args()

    image = Image.open(args.image).convert("RGBA")
    errors = []
    if not (0 <= args.top_y < args.chin_y < args.baseline_y < image.height):
        errors.append(
            "Landmarks must satisfy 0 <= top_y < chin_y < baseline_y < image height"
        )

    total_height = args.baseline_y - args.top_y
    head_height = args.chin_y - args.top_y
    heads_tall = total_height / head_height if head_height > 0 else 0.0
    head_fraction = head_height / total_height if total_height > 0 else 0.0

    if not (args.min_heads <= heads_tall <= args.max_heads):
        errors.append(
            f"heads_tall {heads_tall:.4f} is outside "
            f"{args.min_heads:.2f}–{args.max_heads:.2f}"
        )
    if not (args.min_head_fraction <= head_fraction <= args.max_head_fraction):
        errors.append(
            f"head_fraction {head_fraction:.4%} is outside "
            f"{args.min_head_fraction:.0%}–{args.max_head_fraction:.0%}"
        )

    report = {
        "ok": not errors,
        "image": str(args.image),
        "canvas": list(image.size),
        "landmarks": {
            "top_y": args.top_y,
            "chin_y": args.chin_y,
            "baseline_y": args.baseline_y,
        },
        "measurements": {
            "total_height_px": total_height,
            "head_height_px": head_height,
            "heads_tall": round(heads_tall, 4),
            "head_fraction": round(head_fraction, 4),
        },
        "allowed": {
            "heads_tall": [args.min_heads, args.max_heads],
            "head_fraction": [args.min_head_fraction, args.max_head_fraction],
        },
        "errors": errors,
    }

    report_path = args.report or args.image.with_name(
        f"{args.image.stem}-proportion-validation.json"
    )
    overlay_path = args.overlay or args.image.with_name(
        f"{args.image.stem}-proportion-overlay.png"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    guides = [
        (args.top_y, (255, 62, 62, 255), "TOP"),
        (args.chin_y, (255, 204, 44, 255), "CHIN"),
        (args.baseline_y, (42, 174, 255, 255), "SOLE"),
    ]
    for y, color, label in guides:
        draw.line((0, y, image.width - 1, y), fill=color, width=3)
        draw.rectangle((6, max(0, y - 22), 72, y), fill=(0, 0, 0, 180))
        draw.text((10, max(0, y - 19)), label, fill=color)
    overlay.save(overlay_path)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
