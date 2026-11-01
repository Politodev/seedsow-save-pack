# Seedsow Save Pack

A small open-source Windows utility for downloading and checking the published Seedsow Lua Editor save package.

## Status

This repository currently contains two separate pieces:

- The Windows app downloads the latest published editor-save ZIP, verifies its published SHA-256 values, validates the manifest and checks each archived filename and file hash. It saves the verified files in a local downloads folder.
- The experimental install.py script wraps parts of the public ns2-savekit project. It can write save files only when a compatible ns2jb session is already running. The documented way to start that session currently uses SmileBASIC. This is not a stock-console, no-SmileBASIC installer.

The Windows app does not connect to a console, read a save, repair a save, or install anything. A public, reproducible save-import interface for a standard Switch 2 without SmileBASIC is not currently documented. That missing interface is the main work remaining for a one-click importer.

## Run on Windows

Requirements: Python 3.10 or later with Tcl/Tk.

1. Download or clone this repository.
2. Double-click START WINDOWS.cmd.
3. Select “Télécharger et vérifier la dernière version”.

The verified package and its manifest/checksum files are stored under downloads.

## What is verified

The app checks that:

- the ZIP hash matches both the published checksum file and the release manifest;
- the package manifest describes an editor save and does not claim to contain personal account metadata or user programs;
- every ZIP member is listed in the manifest and matches its SHA-256 hash;
- archive paths and filenames are safe and the archive stays within size limits.

The checks establish consistency with values published alongside the release. They are not a cryptographic signature from the editor maintainer.

## Game compatibility

The published starter package is built for Seedsow Lullaby US demo 1.0.0. The editor project lists EU demo compatibility as a community report, not an independently reproduced result; its exact regional demo title ID remains unresolved. Do not treat a successful package check as proof that another edition or region can load it.

See the editor project's compatibility notes:
https://github.com/DialingSpoon527/seedsow-lua-editor/blob/main/docs/compatibility.md

## Experimental direct installer

install.py is separate from the Windows verifier. It is experimental, targets the US demo title ID, and requires ns2-savekit plus an already active supported ns2jb session. Do not use it with a different title or edition. It does not start ns2jb or provide a no-SmileBASIC entry point.

The ns2-savekit project documents its current workflow and requirements:
https://github.com/dougchansan/ns2-savekit

The installer takes an AccountUid as an argument. Treat that identifier and any console logs as private; do not post them in issues.

## Development

The Windows verifier uses only the Python standard library. No third-party Python packages are required.

- app.py — Windows package-verification UI
- install.py — experimental direct-install wrapper
- START WINDOWS.cmd — Windows launcher

Please do not submit console save dumps, account identifiers, or personal backups in issues or pull requests.

## License

MIT. See LICENSE.

