#!/usr/bin/env python3
"""Provider-neutral bridge for an explicitly configured external image model."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def load_provider(config_path: Path, config: dict[str, Any]):
    provider_value = config.get("provider_file")
    if not isinstance(provider_value, str) or not provider_value.strip():
        raise ValueError("config.provider_file must name a local Python provider module")
    provider_path = Path(provider_value).expanduser()
    if not provider_path.is_absolute():
        provider_path = (config_path.parent / provider_path).resolve()
    if not provider_path.is_file():
        raise ValueError(f"Provider module does not exist: {provider_path}")

    entrypoint = config.get("entrypoint", "generate_image")
    if not isinstance(entrypoint, str) or not entrypoint.isidentifier():
        raise ValueError("config.entrypoint must be a Python identifier")

    spec = importlib.util.spec_from_file_location("desktop_pet_external_image_provider", provider_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load provider module: {provider_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generate = getattr(module, entrypoint, None)
    if not callable(generate):
        raise ValueError(f"Provider module has no callable {entrypoint}()")
    return provider_path, entrypoint, generate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config_path = args.config.expanduser().resolve()
    config = load_json(config_path)
    provider_path, entrypoint, generate = load_provider(config_path, config)

    api_key_env = config.get("api_key_env")
    if not isinstance(api_key_env, str) or not api_key_env.strip():
        raise ValueError("config.api_key_env must name an environment variable")

    if args.check:
        print(json.dumps({
            "ok": True,
            "provider_file": str(provider_path),
            "entrypoint": entrypoint,
            "api_key_env": api_key_env,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.request is None:
        raise ValueError("--request is required unless --check is used")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(f"Missing API key environment variable: {api_key_env}")

    request = load_json(args.request.expanduser().resolve())
    settings = config.get("settings", {})
    if not isinstance(settings, dict):
        raise ValueError("config.settings must be a JSON object")
    result = generate(request=request, api_key=api_key, settings=settings)
    if not isinstance(result, dict) or not isinstance(result.get("outputs"), list):
        raise ValueError("Provider must return a dict containing an outputs list")
    missing = [str(path) for value in result["outputs"] if not (path := Path(value)).is_file()]
    if missing:
        raise ValueError("Provider reported missing output files: " + ", ".join(missing))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
