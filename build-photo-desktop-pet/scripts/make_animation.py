#!/usr/bin/env python3
"""Validate 12 RGBA frames and export APNG, WebP, storyboard and audit data."""

from __future__ import annotations

import argparse
import binascii
import json
import struct
import zlib
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    body = chunk_type + payload
    return (
        struct.pack(">I", len(payload))
        + body
        + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)
    )


def save_full_frame_apng(
    path: Path, frames: list[Image.Image], frame_ms: int
) -> None:
    """Write 12 explicit full RGBA frames without duplicate-frame collapsing."""
    width, height = frames[0].size
    chunks = [
        b"\x89PNG\r\n\x1a\n",
        png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
        ),
        png_chunk(b"acTL", struct.pack(">II", len(frames), 0)),
    ]
    sequence = 0
    for index, frame in enumerate(frames):
        chunks.append(
            png_chunk(
                b"fcTL",
                struct.pack(
                    ">IIIIIHHBB",
                    sequence,
                    width,
                    height,
                    0,
                    0,
                    frame_ms,
                    1000,
                    0,
                    0,
                ),
            )
        )
        sequence += 1
        rgba = frame.convert("RGBA").tobytes()
        stride = width * 4
        scanlines = b"".join(
            b"\x00" + rgba[offset : offset + stride]
            for offset in range(0, len(rgba), stride)
        )
        compressed = zlib.compress(scanlines, level=9)
        if index == 0:
            chunks.append(png_chunk(b"IDAT", compressed))
        else:
            chunks.append(
                png_chunk(b"fdAT", struct.pack(">I", sequence) + compressed)
            )
            sequence += 1
    chunks.append(png_chunk(b"IEND", b""))
    path.write_bytes(b"".join(chunks))


def pixel_data(image: Image.Image):
    getter = getattr(image, "get_flattened_data", None)
    return getter() if getter else image.getdata()


def lower_anchor(alpha: Image.Image) -> tuple[float | None, int | None]:
    bbox = alpha.getbbox()
    if not bbox:
        return None, None
    _, top, _, bottom = bbox
    region_top = max(top, bottom - max(1, round((bottom - top) * 0.22)))
    points = []
    pixels = alpha.load()
    for y in range(region_top, bottom):
        for x in range(alpha.width):
            if pixels[x, y] >= 32:
                points.append((x, y))
    if not points:
        return None, None
    return sum(x for x, _ in points) / len(points), max(y for _, y in points)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--asset-name", required=True, help="Output filename without extension")
    parser.add_argument("--frame-ms", type=int, default=140)
    parser.add_argument("--width", type=int, default=384)
    parser.add_argument("--height", type=int, default=341)
    args = parser.parse_args()

    frame_paths = sorted(args.frames_dir.glob("frame-*.png"))
    errors: list[str] = []
    warnings: list[str] = []
    if len(frame_paths) != 12:
        errors.append(f"Expected 12 frame-*.png files; found {len(frame_paths)}")

    frames: list[Image.Image] = []
    metrics = []
    for index, path in enumerate(frame_paths, start=1):
        image = Image.open(path)
        if image.mode != "RGBA":
            errors.append(f"{path.name}: mode is {image.mode}, expected RGBA")
            image = image.convert("RGBA")
        if image.size != (args.width, args.height):
            errors.append(f"{path.name}: size is {image.size}, expected {(args.width, args.height)}")
        rgba = image.copy()
        alpha = rgba.getchannel("A")
        corners = [alpha.getpixel((0, 0)), alpha.getpixel((args.width - 1, 0)), alpha.getpixel((0, args.height - 1)), alpha.getpixel((args.width - 1, args.height - 1))] if rgba.size == (args.width, args.height) else []
        if corners and any(corners):
            errors.append(f"{path.name}: one or more corners are not transparent")
        bbox = alpha.getbbox()
        anchor_x, baseline_y = lower_anchor(alpha)
        visible = sum(1 for value in pixel_data(alpha) if value >= 32)
        hidden_rgb = sum(
            1 for r, g, b, a in pixel_data(rgba) if a == 0 and (r != 0 or g != 0 or b != 0)
        )
        if hidden_rgb:
            warnings.append(f"{path.name}: {hidden_rgb} fully transparent pixels retain hidden RGB")
        metrics.append({
            "frame": index,
            "file": path.name,
            "bbox": bbox,
            "visible_alpha_pixels": visible,
            "lower_anchor_x": round(anchor_x, 3) if anchor_x is not None else None,
            "baseline_y": baseline_y,
            "hidden_rgb_pixels": hidden_rgb,
        })
        frames.append(rgba)

    if errors:
        print(json.dumps({"ok": False, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    apng_path = args.out_dir / f"{args.asset_name}.png"
    webp_path = args.out_dir / f"{args.asset_name}.webp"
    storyboard_path = args.out_dir / f"{args.asset_name}-storyboard.png"
    onion_path = args.out_dir / f"{args.asset_name}-onion-skin.png"

    save_full_frame_apng(apng_path, frames, args.frame_ms)
    frames[0].save(
        webp_path,
        save_all=True,
        append_images=frames[1:],
        duration=[args.frame_ms] * len(frames),
        loop=0,
        lossless=True,
        quality=100,
        method=6,
    )

    storyboard = Image.new("RGBA", (args.width * 4, args.height * 3), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        storyboard.alpha_composite(frame, ((index % 4) * args.width, (index // 4) * args.height))
    storyboard.save(storyboard_path)

    onion = Image.new("RGBA", frames[0].size, (0, 0, 0, 0))
    for frame in frames:
        layer = frame.copy()
        layer.putalpha(layer.getchannel("A").point(lambda a: round(a / len(frames))))
        onion = Image.alpha_composite(onion, layer)
    onion.save(onion_path)

    decoded = [frame.convert("RGBA") for frame in ImageSequence.Iterator(Image.open(apng_path))]
    if len(decoded) != 12:
        errors.append(f"APNG decoded to {len(decoded)} frames instead of 12; add a legitimate tiny change in an allowed dynamic region")
    else:
        for index, (expected, actual) in enumerate(zip(frames, decoded), start=1):
            if ImageChops.difference(expected, actual).getbbox() is not None:
                errors.append(f"APNG frame {index} differs from source frame")

    anchors = [m["lower_anchor_x"] for m in metrics if m["lower_anchor_x"] is not None]
    baselines = [m["baseline_y"] for m in metrics if m["baseline_y"] is not None]
    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "frame_count": len(frames),
        "canvas": [args.width, args.height],
        "frame_ms": args.frame_ms,
        "anchor_x_range": round(max(anchors) - min(anchors), 3) if anchors else None,
        "baseline_y_range": max(baselines) - min(baselines) if baselines else None,
        "metrics": metrics,
        "outputs": [str(apng_path), str(webp_path), str(storyboard_path), str(onion_path)],
    }
    (args.out_dir / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
