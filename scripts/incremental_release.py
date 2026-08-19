#!/usr/bin/env python3
"""Plan, assemble, and verify incremental updates to the fixed font Release.

The Release remains a complete catalog, but only families whose byte-producing
inputs changed are rebuilt. Existing assets are reused through their recorded
manifest hashes and a per-family build fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
BUILD_INPUT_PATHS = (
    "scripts/build_fonts.py",
    "scripts/fontconvert_sdcard.py",
    "scripts/cpfont_version.py",
)
BUILD_REQUIREMENT_PREFIXES = ("freetype-py==", "fonttools==")
BUILD_FAMILY_KEYS = ("name", "intervals", "force_autohint", "source")
BUILD_EPOCH = 1
RUNNER_IMAGE = "ubuntu-24.04"
FALLBACK_SHA_PATTERN = re.compile(rb'^SHA256\s*=\s*"([0-9a-f]{64})"', re.MULTILINE)


def normalized_bytes(data: bytes) -> bytes:
    """Make source fingerprints independent of the checkout line-ending mode."""
    return data.replace(b"\r\n", b"\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256_bytes(encoded)


def repository_bytes(path: str, ref: str | None = None) -> bytes:
    if ref:
        try:
            return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Cannot read {path} from Git ref {ref}") from error
    return (ROOT / path).read_bytes()


def load_document(path: Path = CONFIG) -> dict:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"Invalid catalog document: {path}")
    return document


def load_document_at_ref(ref: str) -> dict:
    document = yaml.safe_load(repository_bytes("config/fonts.yaml", ref))
    if not isinstance(document, dict):
        raise RuntimeError(f"Invalid catalog document at {ref}")
    return document


def catalog_sizes(document: dict) -> list[int]:
    return list(dict.fromkeys([*document["ui_sizes"], *document["reader_sizes"]]))


def build_requirements(ref: str | None = None) -> list[str]:
    text = repository_bytes("requirements.txt", ref).decode("utf-8")
    return sorted(
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(BUILD_REQUIREMENT_PREFIXES)
    )


def fallback_sha256(ref: str | None = None) -> str:
    match = FALLBACK_SHA_PATTERN.search(repository_bytes("scripts/fetch_fallback.py", ref))
    if match is None:
        raise RuntimeError("Cannot find the locked fallback SHA-256")
    return match.group(1).decode("ascii")


def toolchain_fingerprint_inputs(ref: str | None = None) -> dict:
    return {
        "buildEpoch": BUILD_EPOCH,
        "runnerImage": RUNNER_IMAGE,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "requirements": build_requirements(ref),
        "scripts": {
            path: sha256_bytes(normalized_bytes(repository_bytes(path, ref)))
            for path in BUILD_INPUT_PATHS
        },
    }


def family_build_inputs(document: dict, family: dict, ref: str | None = None) -> dict:
    return {
        "family": {key: family[key] for key in BUILD_FAMILY_KEYS if key in family},
        "sizes": catalog_sizes(document),
        "fallbackSha256": fallback_sha256(ref),
        "toolchain": toolchain_fingerprint_inputs(ref),
    }


def family_fingerprint(document: dict, family: dict, ref: str | None = None) -> str:
    return canonical_hash(family_build_inputs(document, family, ref))


def expected_family_filenames(document: dict, name: str) -> list[str]:
    return [f"{name}_{size}.cpfont" for size in catalog_sizes(document)]


def manifest_family_map(manifest: dict | None) -> dict[str, dict]:
    if not manifest:
        return {}
    families = manifest.get("families", [])
    if not isinstance(families, list):
        raise RuntimeError("Manifest families must be a list")
    result: dict[str, dict] = {}
    for family in families:
        name = family.get("name")
        if not isinstance(name, str) or not name:
            raise RuntimeError("Manifest contains an unnamed family")
        if name in result:
            raise RuntimeError(f"Manifest contains duplicate family {name}")
        result[name] = family
    return result


def validate_manifest_family(document: dict, family: dict) -> None:
    name = family["name"]
    files = family.get("files", [])
    actual_names = [entry.get("name") for entry in files]
    expected_names = expected_family_filenames(document, name)
    if actual_names != expected_names:
        raise RuntimeError(f"{name}: files {actual_names!r} do not match {expected_names!r}")
    for entry in files:
        if not isinstance(entry.get("size"), int) or entry["size"] <= 0:
            raise RuntimeError(f"{entry.get('name', name)}: invalid size")
        digest = entry.get("sha256", "")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RuntimeError(f"{entry.get('name', name)}: invalid SHA-256")


def source_cache_key(family: dict, *, ref: str | None = None) -> str:
    source = family["source"]
    if source.get("sha256"):
        return source["sha256"]
    path = source["path"]
    data = repository_bytes(path, ref) if ref else (ROOT / path).read_bytes()
    payload = {
        "fileSha256": sha256_bytes(data),
        "archiveMember": source.get("archive_member"),
        "variable": source.get("variable"),
    }
    return canonical_hash(payload)


def build_index_document(
    document: dict,
    manifest: dict | None = None,
    *,
    ref: str | None = None,
    commit: str | None = None,
) -> dict:
    manifest_by_name = manifest_family_map(manifest)
    families: dict[str, dict] = {}
    for family in document.get("families", []):
        name = family["name"]
        entry: dict[str, Any] = {
            "fingerprint": family_fingerprint(document, family, ref),
            "sourceSha256": source_cache_key(family, ref=ref),
        }
        if name in manifest_by_name:
            validate_manifest_family(document, manifest_by_name[name])
            entry["files"] = manifest_by_name[name]["files"]
        families[name] = entry
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "buildEpoch": BUILD_EPOCH,
        "families": families,
    }
    if commit:
        result["commit"] = commit
    if ref:
        result["bootstrapRef"] = ref
    return result


def validate_previous_release(manifest: dict, index: dict) -> None:
    if manifest.get("version") != 2:
        raise RuntimeError("Previous manifest version must be 2")
    manifest_by_name = manifest_family_map(manifest)
    index_families = index.get("families", {})
    if not isinstance(index_families, dict):
        raise RuntimeError("Previous build index families must be an object")
    if set(manifest_by_name) != set(index_families):
        raise RuntimeError("Previous manifest and build index family sets do not match")
    for name, family in manifest_by_name.items():
        # The previous catalog can have a different global size contract. Check
        # filename shape and index/manifest agreement rather than current sizes.
        files = family.get("files", [])
        if not files:
            raise RuntimeError(f"{name}: previous manifest has no files")
        indexed_files = index_families[name].get("files")
        if indexed_files is not None and indexed_files != files:
            raise RuntimeError(f"{name}: previous build index files do not match the manifest")


def plan_release(
    current_document: dict,
    previous_index: dict | None,
    previous_manifest: dict | None = None,
    *,
    force_all: bool = False,
) -> dict:
    current_families = current_document.get("families", [])
    current_by_name = {family["name"]: family for family in current_families}
    previous_fingerprints = (previous_index or {}).get("families", {})
    previous_manifest_by_name = manifest_family_map(previous_manifest)
    previous_manifest_names = set(previous_manifest_by_name)
    if previous_index and previous_manifest:
        validate_previous_release(previous_manifest, previous_index)

    build: list[str] = []
    reuse: list[str] = []
    fingerprints: dict[str, str] = {}
    for family in current_families:
        name = family["name"]
        fingerprint = family_fingerprint(current_document, family)
        fingerprints[name] = fingerprint
        previous = previous_fingerprints.get(name, {})
        reusable = (
            not force_all
            and name in previous_manifest_names
            and previous.get("fingerprint") == fingerprint
        )
        (reuse if reusable else build).append(name)

    previous_names = set(previous_fingerprints) | previous_manifest_names
    remove = sorted(previous_names - set(current_by_name))
    changed_existing = [name for name in build if name in previous_manifest_names]
    new = [name for name in build if name not in previous_manifest_names]
    metadata_changed = [
        name
        for name in reuse
        if normalized_public_family(previous_manifest_by_name.get(name, {}))
        != public_family_metadata(current_by_name[name])
    ]
    needs_release_update = bool(build or remove or metadata_changed)
    return {
        "schemaVersion": 1,
        "build": build,
        "reuse": reuse,
        "new": new,
        "changedExisting": changed_existing,
        "metadataChanged": metadata_changed,
        "remove": remove,
        "fingerprints": fingerprints,
        "forceAll": force_all,
        "hasPreviousRelease": previous_manifest is not None,
        "needsReleaseUpdate": needs_release_update,
    }


def public_family_metadata(config_family: dict) -> dict:
    result = {"description": config_family["description"]}
    if config_family.get("source_url"):
        result["sourceUrl"] = config_family["source_url"]
    return result


def normalized_public_family(family: dict) -> dict:
    result = {"description": family.get("description")}
    if family.get("sourceUrl"):
        result["sourceUrl"] = family["sourceUrl"]
    if any(key in family for key in ("license", "licenseType", "licenseStatus", "licenseUrl")):
        result["legacyLicenseMetadata"] = True
    return result


def merge_manifest(
    current_document: dict,
    previous_manifest: dict | None,
    built_manifest: dict | None,
    *,
    base_url: str | None = None,
) -> dict:
    previous_by_name = manifest_family_map(previous_manifest)
    built_by_name = manifest_family_map(built_manifest)
    resolved_base_url = base_url or (previous_manifest or built_manifest or {}).get("baseUrl")
    if not isinstance(resolved_base_url, str) or not resolved_base_url.endswith("/"):
        raise RuntimeError("A trailing-slash base URL is required")

    families: list[dict] = []
    for config_family in current_document.get("families", []):
        name = config_family["name"]
        source = built_by_name.get(name) or previous_by_name.get(name)
        if source is None:
            raise RuntimeError(f"{name}: no built or reusable manifest entry")
        entry = {
            "name": name,
            **public_family_metadata(config_family),
            "styles": source.get("styles", []),
            "files": source.get("files", []),
        }
        validate_manifest_family(current_document, entry)
        families.append(entry)

    return {"version": 2, "baseUrl": resolved_base_url, "families": families}


def asset_map(document: dict | list) -> dict[str, dict]:
    assets = document.get("assets", []) if isinstance(document, dict) else document
    if not isinstance(assets, list):
        raise RuntimeError("Release assets must be a list")
    return {asset["name"]: asset for asset in assets if isinstance(asset, dict) and asset.get("name")}


def verify_asset_metadata(manifest: dict, assets: dict[str, dict] | dict | list) -> None:
    by_name = assets if isinstance(assets, dict) and "assets" not in assets else asset_map(assets)
    errors: list[str] = []
    for family in manifest.get("families", []):
        for entry in family.get("files", []):
            filename = entry["name"]
            asset = by_name.get(filename)
            if asset is None:
                errors.append(f"missing {filename}")
            elif asset.get("size") != entry["size"]:
                errors.append(f"{filename}: asset size {asset.get('size')} != {entry['size']}")
    if errors:
        raise RuntimeError("; ".join(errors))


def verify_local_files(manifest: dict, directory: Path, families: list[str]) -> None:
    by_name = manifest_family_map(manifest)
    errors: list[str] = []
    for name in families:
        family = by_name.get(name)
        if family is None:
            errors.append(f"manifest is missing {name}")
            continue
        for entry in family.get("files", []):
            path = directory / entry["name"]
            if not path.is_file():
                errors.append(f"missing {entry['name']}")
                continue
            if path.stat().st_size != entry["size"]:
                errors.append(f"{entry['name']}: size mismatch")
            elif sha256_file(path) != entry["sha256"]:
                errors.append(f"{entry['name']}: SHA-256 mismatch")
    if errors:
        raise RuntimeError("; ".join(errors))


def family_files(manifest: dict, families: list[str]) -> list[str]:
    by_name = manifest_family_map(manifest)
    result: list[str] = []
    for name in families:
        if name not in by_name:
            raise RuntimeError(f"Manifest is missing {name}")
        result.extend(entry["name"] for entry in by_name[name].get("files", []))
    return result


def obsolete_files(previous_manifest: dict | None, current_manifest: dict) -> list[str]:
    previous = {
        entry["name"]
        for family in (previous_manifest or {}).get("families", [])
        for entry in family.get("files", [])
    }
    current = {
        entry["name"]
        for family in current_manifest.get("families", [])
        for entry in family.get("files", [])
    }
    return sorted(previous - current)


def write_json_atomic(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(document, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
    temporary_path.replace(path)


def read_json(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def command_plan(args: argparse.Namespace) -> int:
    current = load_document(args.config)
    previous_manifest = read_json(args.previous_manifest)
    previous_index = read_json(args.previous_index)
    if previous_manifest is not None and previous_index is None:
        if not args.bootstrap_ref:
            raise RuntimeError("Previous Release has no build index and no bootstrap ref was provided")
        bootstrap_document = load_document_at_ref(args.bootstrap_ref)
        previous_index = build_index_document(
            bootstrap_document,
            previous_manifest,
            ref=args.bootstrap_ref,
        )
        if args.previous_index:
            write_json_atomic(args.previous_index, previous_index)
    elif previous_index is not None and previous_manifest is None:
        raise RuntimeError("Previous build index exists without a Release manifest")

    plan = plan_release(
        current,
        previous_index,
        previous_manifest,
        force_all=args.force_all,
    )
    write_json_atomic(args.output, plan)
    if args.github_output:
        write_github_output(
            args.github_output,
            {
                "families_json": json.dumps(plan["build"], separators=(",", ":")),
                "changed_existing_json": json.dumps(plan["changedExisting"], separators=(",", ":")),
                "new_json": json.dumps(plan["new"], separators=(",", ":")),
                "has_builds": str(bool(plan["build"])).lower(),
                "has_previous_release": str(plan["hasPreviousRelease"]).lower(),
                "needs_font_publish": str(bool(plan["build"] or plan["remove"])).lower(),
                "release_update_needed": str(plan["needsReleaseUpdate"]).lower(),
            },
        )
    print(
        f"Incremental plan: build={len(plan['build'])}, reuse={len(plan['reuse'])}, "
        f"remove={len(plan['remove'])}"
    )
    return 0


def command_merge(args: argparse.Namespace) -> int:
    current = load_document(args.config)
    previous_manifest = read_json(args.previous_manifest)
    built_manifest = read_json(args.built_manifest)
    manifest = merge_manifest(
        current,
        previous_manifest,
        built_manifest,
        base_url=args.base_url,
    )
    write_json_atomic(args.manifest_output, manifest)
    index = build_index_document(current, manifest, commit=args.commit)
    write_json_atomic(args.index_output, index)
    print(
        f"Assembled {len(manifest['families'])} families and "
        f"{sum(len(family['files']) for family in manifest['families'])} files."
    )
    return 0


def command_verify_assets(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    assets = read_json(args.assets)
    if manifest is None or assets is None:
        raise RuntimeError("Manifest and assets JSON are required")
    verify_asset_metadata(manifest, asset_map(assets))
    required = args.require or []
    by_name = asset_map(assets)
    missing = [name for name in required if name not in by_name]
    if missing:
        raise RuntimeError("Missing Release metadata assets: " + ", ".join(missing))
    print(f"Verified Release metadata for {sum(len(f['files']) for f in manifest['families'])} font files.")
    return 0


def parse_families_json(value: str) -> list[str]:
    families = json.loads(value)
    if not isinstance(families, list) or not all(isinstance(name, str) for name in families):
        raise RuntimeError("families-json must be a JSON string list")
    return families


def command_verify_files(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    if manifest is None:
        raise RuntimeError("Manifest is required")
    families = parse_families_json(args.families_json)
    verify_local_files(manifest, args.directory, families)
    print(f"Verified {len(families)} downloaded families.")
    return 0


def command_list_files(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    if manifest is None:
        raise RuntimeError("Manifest is required")
    for filename in family_files(manifest, parse_families_json(args.families_json)):
        print(filename)
    return 0


def command_obsolete_files(args: argparse.Namespace) -> int:
    current = read_json(args.current_manifest)
    if current is None:
        raise RuntimeError("Current manifest is required")
    for filename in obsolete_files(read_json(args.previous_manifest), current):
        print(filename)
    return 0


def command_source_sha(args: argparse.Namespace) -> int:
    document = load_document(args.config)
    family = next((item for item in document.get("families", []) if item["name"] == args.family), None)
    if family is None:
        raise RuntimeError(f"Unknown family: {args.family}")
    print(source_cache_key(family))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--config", type=Path, default=CONFIG)
    plan.add_argument("--previous-manifest", type=Path)
    plan.add_argument("--previous-index", type=Path)
    plan.add_argument("--bootstrap-ref")
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--github-output", type=Path)
    plan.add_argument("--force-all", action="store_true")
    plan.set_defaults(function=command_plan)

    merge = subparsers.add_parser("merge")
    merge.add_argument("--config", type=Path, default=CONFIG)
    merge.add_argument("--previous-manifest", type=Path)
    merge.add_argument("--built-manifest", type=Path)
    merge.add_argument("--base-url")
    merge.add_argument("--manifest-output", type=Path, required=True)
    merge.add_argument("--index-output", type=Path, required=True)
    merge.add_argument("--commit", default=os.environ.get("GITHUB_SHA"))
    merge.set_defaults(function=command_merge)

    verify_assets = subparsers.add_parser("verify-assets")
    verify_assets.add_argument("--manifest", type=Path, required=True)
    verify_assets.add_argument("--assets", type=Path, required=True)
    verify_assets.add_argument("--require", action="append")
    verify_assets.set_defaults(function=command_verify_assets)

    verify_files = subparsers.add_parser("verify-files")
    verify_files.add_argument("--manifest", type=Path, required=True)
    verify_files.add_argument("--directory", type=Path, required=True)
    verify_files.add_argument("--families-json", required=True)
    verify_files.set_defaults(function=command_verify_files)

    list_files = subparsers.add_parser("list-files")
    list_files.add_argument("--manifest", type=Path, required=True)
    list_files.add_argument("--families-json", required=True)
    list_files.set_defaults(function=command_list_files)

    obsolete = subparsers.add_parser("obsolete-files")
    obsolete.add_argument("--previous-manifest", type=Path)
    obsolete.add_argument("--current-manifest", type=Path, required=True)
    obsolete.set_defaults(function=command_obsolete_files)

    source_sha = subparsers.add_parser("source-sha")
    source_sha.add_argument("family")
    source_sha.add_argument("--config", type=Path, default=CONFIG)
    source_sha.set_defaults(function=command_source_sha)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.function(args)
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
