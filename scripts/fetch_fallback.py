#!/usr/bin/env python3
"""Fetch and verify the locked Latin fallback used in every generated family."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/crosspoint-reader/crosspoint-reader/master/lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-Regular.ttf"
SHA256 = "fe8c022f48d8dd29f17b744d16f9346f4357e16f7d4f7be58b000ae7c291b614"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "vendor" / "NotoSans-Regular.ttf"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.output.is_file() and digest(args.output) == SHA256:
        print(f"Verified existing fallback: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, suffix=".download", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with urllib.request.urlopen(URL, timeout=180) as response, temporary_path.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        actual = digest(temporary_path)
        if actual != SHA256:
            raise RuntimeError(f"Fallback SHA-256 {actual} does not match locked {SHA256}")
        temporary_path.replace(args.output)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    print(f"Fetched locked fallback: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
