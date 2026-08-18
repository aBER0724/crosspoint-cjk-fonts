from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()

    document = json.loads(args.manifest.read_text(encoding="utf-8"))
    document["baseUrl"] = args.base_url.rstrip("/") + "/"
    args.manifest.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(hashlib.sha256(args.manifest.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
