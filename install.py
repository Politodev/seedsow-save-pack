#!/usr/bin/env python3
"""Experimental direct installer for the Seedsow Lua Editor on Switch 2.

This is a small front end for the public ns2-savekit restore tools. It does not
contain or start ns2jb. The user must already have a live, supported savekit
session and must explicitly confirm before any save write is attempted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


REPO = "DialingSpoon527/seedsow-lua-editor"
TITLE_ID = "010042d022aea000"  # Seedsow Lullaby US demo
TARGET_GAME = "Seedsow Lullaby US demo 1.0.0"
USER_AGENT = "seedsow-direct-import/0.1 experimental"
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def fail(message: str) -> None:
    raise RuntimeError(message)


def request_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        fail(f"Download failed for {url}: {error}")


def get_latest_release() -> dict:
    raw = request_bytes(
        f"https://api.github.com/repos/{REPO}/releases/latest"
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        fail(f"GitHub returned an unreadable release record: {error}")


def release_asset_url(release: dict, name: str) -> str:
    for asset in release.get("assets", []):
        if asset.get("name") == name:
            return asset["browser_download_url"]
    fail(f"Release {release.get('tag_name')} has no {name} asset")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_and_unpack(release: dict, workspace: Path) -> tuple[Path, dict]:
    tag = str(release.get("tag_name", ""))
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        fail(f"Unexpected release tag: {tag!r}")

    zip_name = "Seedsow-Lua-Editor-Save.zip"
    manifest_name = "Seedsow-Lua-Editor-Save.manifest.json"
    checksum_name = zip_name + ".sha256"
    package_dir = workspace / "package" / tag
    package_dir.mkdir(parents=True, exist_ok=True)

    zip_bytes = request_bytes(release_asset_url(release, zip_name))
    metadata_bytes = request_bytes(release_asset_url(release, manifest_name))
    checksum_bytes = request_bytes(release_asset_url(release, checksum_name))
    try:
        package_manifest = json.loads(metadata_bytes)
    except json.JSONDecodeError as error:
        fail(f"Release manifest is invalid JSON: {error}")

    archive_hash = sha256(zip_bytes)
    external_match = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum_bytes)
    if not external_match:
        fail("Release checksum file does not contain a SHA-256 digest")
    external_hash = external_match.group(1).decode("ascii").lower()
    manifest_hash = str(package_manifest.get("sha256", "")).lower()
    if archive_hash != external_hash or archive_hash != manifest_hash:
        fail("The save ZIP does not match both published SHA-256 records")
    if package_manifest.get("kind") != "ready-to-restore-editor-save":
        fail("The release manifest is not a prepared editor save")
    if package_manifest.get("game") != TARGET_GAME:
        fail(
            "This prototype only accepts the tested "
            f"{TARGET_GAME} package; release says "
            f"{package_manifest.get('game')!r}"
        )
    if package_manifest.get("personal_account_metadata_included") is not False:
        fail("The package manifest does not confirm personal account data is absent")
    if package_manifest.get("user_programs_included") is not False:
        fail("The package manifest does not confirm user programs are absent")

    zip_path = package_dir / zip_name
    zip_path.write_bytes(zip_bytes)
    (package_dir / manifest_name).write_bytes(metadata_bytes)
    (package_dir / checksum_name).write_bytes(checksum_bytes)

    expected = package_manifest.get("save_files")
    if not isinstance(expected, dict) or not expected:
        fail("The release manifest has no save-file hash list")
    extracted = workspace / "editor-save" / tag
    extracted.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    with zipfile.ZipFile(zip_path) as archive:
        for item in archive.infolist():
            name = item.filename
            if item.is_dir():
                continue
            relative = PurePosixPath(name)
            if relative.is_absolute() or len(relative.parts) != 1 or ".." in relative.parts:
                fail(f"Refusing an unexpected archive path: {name!r}")
            if name in seen:
                fail(f"Duplicate file in release archive: {name}")
            seen.add(name)
            if name not in expected:
                fail(f"Release archive contains an unlisted file: {name}")
            data = archive.read(item)
            if sha256(data) != str(expected[name]).lower():
                fail(f"File hash mismatch inside release archive: {name}")
            # JKSV metadata is for the original restore workflow, not a game file.
            if name.startswith("."):
                if name != ".nx_save_meta.bin":
                    fail(f"Unexpected hidden package file: {name}")
                continue
            if not SAFE_NAME.fullmatch(name):
                fail(f"Unsafe save filename in release archive: {name!r}")
            (extracted / name).write_bytes(data)
    if seen != set(expected):
        missing = sorted(set(expected) - seen)
        fail("Release archive and manifest differ; missing: " + ", ".join(missing[:8]))
    if not any(extracted.iterdir()):
        fail("The release archive contained no installable save files")
    return extracted, package_manifest


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("\n$ " + " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def check_savekit(savekit: Path, run_dir: Path) -> None:
    required = (
        savekit / "tools" / "save-pull-root.cjs",
        savekit / "tools" / "save-write-stage.cjs",
        run_dir / "switch2" / "current-acquisition.json",
        run_dir / "switch2" / "ro" / "root" / "current-root.json",
    )
    absent = [str(path) for path in required if not path.is_file()]
    if absent:
        fail("Missing savekit files or live run records:\n  " + "\n  ".join(absent))
    try:
        acquisition = json.loads(required[2].read_text(encoding="utf-8"))
        root = json.loads(required[3].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Could not read the active run records: {error}")
    if root.get("session") != acquisition.get("session") or root.get("pid") != 1:
        fail("The run does not contain a matching promoted savekit root")
    if not root.get("rootHandle"):
        fail("The run has no promoted savekit root handle")


def create_write_manifest(
    source: Path, backup: Path, workspace: Path, tag: str, package_manifest: dict
) -> tuple[Path, int, int]:
    backup_names = {
        path.name for path in backup.iterdir() if path.is_file() and path.name != "manifest.json"
    }
    files = []
    replace_count = 0
    total_bytes = 0
    for path in sorted(source.iterdir()):
        if not path.is_file():
            fail(f"Unexpected directory in unpacked save: {path.name}")
        name = path.name
        if not SAFE_NAME.fullmatch(name):
            fail(f"Unsafe save filename: {name!r}")
        data = path.read_bytes()
        is_replace = name in backup_names
        replace_count += int(is_replace)
        total_bytes += len(data)
        files.append(
            {
                "path": "/" + name,
                "local": str(path.resolve()),
                "replace": is_replace,
                "size": len(data),
                "sha256": sha256(data),
            }
        )
    manifest = {
        "purpose": "install Seedsow Lua Editor save on Switch 2",
        "release": package_manifest.get("release", tag),
        "game": package_manifest["game"],
        "source": str(source.resolve()),
        "backup": str(backup.resolve()),
        "files": files,
    }
    output = workspace / "write-manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output, replace_count, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare or install the official Seedsow editor save directly on Switch 2."
    )
    parser.add_argument("--savekit", required=True, type=Path, help="ns2-savekit checkout")
    parser.add_argument("--run", required=True, type=Path, help="live patched ns2jb run folder")
    parser.add_argument("--uid", required=True, help="target AccountUid as 32 raw-byte hex digits")
    parser.add_argument(
        "--workspace",
        type=Path,
        help="local staging folder (default: <savekit>/saves/seedsow-direct-<UTC timestamp>)",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="after backup and review, offer to write the editor save",
    )
    args = parser.parse_args()

    uid = args.uid.removeprefix("0x").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", uid):
        fail("--uid must contain exactly 32 hexadecimal digits")
    savekit = args.savekit.resolve()
    run_dir = args.run.resolve()
    check_savekit(savekit, run_dir)

    if args.workspace:
        workspace = args.workspace.resolve()
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        workspace = savekit / "saves" / f"seedsow-direct-{stamp}"
    if workspace.exists() and any(workspace.iterdir()):
        fail(f"Workspace already exists and is not empty: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)

    release = get_latest_release()
    source, package_manifest = fetch_and_unpack(release, workspace)
    print(f"Official editor package: {release['tag_name']} ({TARGET_GAME})")
    print(f"Verified ZIP SHA-256: {package_manifest['sha256']}")
    print(f"Save files to install: {len(list(source.iterdir()))}")

    backup = workspace / "pre-install-save"
    backup.mkdir(parents=True, exist_ok=False)
    pull = savekit / "tools" / "save-pull-root.cjs"
    run(
        [
            "node",
            str(pull),
            str(run_dir),
            TITLE_ID,
            str(backup),
            uid,
            "--space",
            "1",
            "--type",
            "1",
        ]
    )
    if not any(path.is_file() and path.name != "manifest.json" for path in backup.iterdir()):
        fail("The backup pull returned no save files; the installer will not write")

    manifest_path, replacements, total_bytes = create_write_manifest(
        source, backup, workspace, release["tag_name"], package_manifest
    )
    print("\nInstall plan")
    print(f"  Target title: {TITLE_ID} ({TARGET_GAME})")
    print(f"  Target account: {uid}")
    print(f"  Package files: {len(list(source.iterdir()))} ({total_bytes:,} bytes)")
    print(f"  Existing files to replace: {replacements}")
    print(f"  New files to add: {len(list(source.iterdir())) - replacements}")
    print(f"  Backup kept at: {backup}")
    print(f"  Manifest: {manifest_path}")
    if replacements != 9:
        fail(
            "Expected the nine-file clean demo baseline from the hardware proof, "
            f"but found {replacements} overlapping files. No save write was attempted. "
            "Use a clean Seedsow demo save and review the backup before continuing."
        )
    if not args.install:
        print("\nPreview complete. No console save was written; rerun with --install to continue.")
        return 0

    print(
        "\nThis writes the editor package over nine files in the selected Seedsow save. "
        "The complete pre-install save is preserved in the backup above."
    )
    confirmation = input(f'Type "INSTALL {TITLE_ID.upper()}" to write: ').strip()
    if confirmation != f"INSTALL {TITLE_ID.upper()}":
        print("Cancelled. No console save was written.")
        return 2

    write = savekit / "tools" / "save-write-stage.cjs"
    run(
        [
            "node",
            str(write),
            str(run_dir),
            TITLE_ID,
            uid,
            str(backup),
            str(manifest_path),
            "--space",
            "1",
            "--type",
            "1",
        ]
    )
    print(
        "\nThe write tool read back and hashed every installed file. "
        "Start Seedsow, load slot 1, then close and reopen the game and load slot 1 again."
    )
    print(f"Keep this recovery copy: {backup}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

