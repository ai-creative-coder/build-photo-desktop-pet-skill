#!/usr/bin/env python3
"""Create project app icons from the current user's approved standing chibi base."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_subject(path: Path) -> Image.Image:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if maximum == 0:
        raise SystemExit("The standing-base image is fully transparent.")
    if minimum == 255:
        raise SystemExit("Use the approved RGBA standing base, not an opaque or chroma-key image.")
    bounds = alpha.getbbox()
    if not bounds:
        raise SystemExit("No visible subject was found.")
    return rgba.crop(bounds)


def compose_icon(subject: Image.Image, size: int = 1024) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    margin = round(size * 0.055)
    radius = round(size * 0.22)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=(255, 235, 198, 255),
        outline=(224, 159, 70, 255),
        width=max(2, round(size * 0.012)),
    )

    max_width = round(size * 0.70)
    max_height = round(size * 0.80)
    scale = min(max_width / subject.width, max_height / subject.height)
    target = (
        max(1, round(subject.width * scale)),
        max(1, round(subject.height * scale)),
    )
    resized = subject.resize(target, Image.Resampling.LANCZOS)
    x = (size - resized.width) // 2
    baseline = round(size * 0.91)
    y = baseline - resized.height
    canvas.alpha_composite(resized, (x, y))
    return canvas


def save_review(master: Image.Image, path: Path) -> None:
    sizes = (256, 128, 64, 32)
    padding = 24
    width = sum(sizes) + padding * (len(sizes) + 1)
    height = max(sizes) + padding * 2
    review = Image.new("RGB", (width, height), (238, 238, 238))
    x = padding
    for size in sizes:
        preview = master.resize((size, size), Image.Resampling.LANCZOS).convert("RGB")
        review.paste(preview, (x, padding + max(sizes) - size))
        x += size + padding
    path.parent.mkdir(parents=True, exist_ok=True)
    review.save(path, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="Approved neutral standing RGBA base")
    parser.add_argument("--project", required=True, type=Path, help="Generated desktop-pet project")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    project = args.project.expanduser().resolve()
    spec_path = project / "project-spec.json"
    icons_dir = project / "src-tauri" / "icons"
    if not source.is_file():
        raise SystemExit(f"Standing-base image not found: {source}")
    if not spec_path.is_file() or not icons_dir.is_dir():
        raise SystemExit("The target is not a generated desktop-pet project.")

    subject = load_subject(source)
    master = compose_icon(subject)
    png = icons_dir / "icon.png"
    ico = icons_dir / "icon.ico"
    icns = icons_dir / "icon.icns"
    master.resize((512, 512), Image.Resampling.LANCZOS).save(png, optimize=True)
    master.save(
        ico,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    master.save(icns, format="ICNS")

    review = project / "output" / "reviews" / "program-icon-review.png"
    save_review(master, review)

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec.update(
        {
            "custom_icon_ready": True,
            "custom_icon_source_role": "approved-neutral-standing-base",
            "custom_icon_source_sha256": sha256(source),
            "custom_icon_files": [
                "src-tauri/icons/icon.png",
                "src-tauri/icons/icon.ico",
                "src-tauri/icons/icon.icns",
            ],
            "custom_icon_review": "output/reviews/program-icon-review.png",
        }
    )
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "source_sha256": spec["custom_icon_source_sha256"],
                "icons": [str(png), str(ico), str(icns)],
                "review": str(review),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
