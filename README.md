# Seedsow Save Pack

A small open-source Windows utility for downloading and checking the published Seedsow Lua Editor save package.

## Status

This repository currently contains two separate pieces:

- The Windows app downloads the latest published editor-save ZIP, verifies its published SHA-256 values, validates the manifest and checks each archived filename and file hash. It can also place an unchanged copy of the verified ZIP under `downloads/<version>/JKSV/saves/` for JKSV's save-import flow.
- The experimental install.py script wraps parts of the public ns2-savekit project. It can write save files only when a compatible ns2jb session is already running. The documented way to start that session currently uses SmileBASIC. This is not a stock-console, no-SmileBASIC installer.

The Windows app does not connect to a console, read or repair a save, or write anything to a console. JKSV preparation only creates a file to copy to an SD card. JKSV must already be runnable on the target console; this project does not provide a way to launch homebrew on a standard Switch 2. Direct import without SmileBASIC is still unavailable in this version.

## Run on Windows

Requirements: Python 3.10 or later with Tcl/Tk.

1. Download or clone this repository.
2. Double-click START WINDOWS.cmd.
3. Select “Télécharger et vérifier” or “Préparer pour JKSV”.

The verified package and its manifest/checksum files are stored under `downloads/<version>`. The second button also places a copy of the ZIP in `downloads/<version>/JKSV/saves/`.

## What is verified

The app checks that:

- the ZIP hash matches both the published checksum file and the release manifest;
- the package manifest describes an editor save and does not claim to contain personal account metadata or user programs;
- every ZIP member is listed in the manifest and matches its SHA-256 hash;
- archive paths and filenames are safe and the archive stays within size limits.

The checks establish consistency with values published alongside the release. They are not a cryptographic signature from the editor maintainer.

## Import with JKSV

“Préparer pour JKSV” keeps the verified ZIP unchanged and places it under `JKSV/saves/`. The package includes the `.nx_save_meta.bin` file expected by JKSV's save-import function.

1. Copy the app's prepared `JKSV` folder to the root of a modified Switch 1's SD card, merging it with an existing `JKSV` folder if needed. If JKSV uses a custom output folder, put `saves` under that folder.
2. On a console where JKSV can already run, back up the current game save first.
3. Use JKSV's save-import function and select the prepared Seedsow archive.

JKSV is homebrew that runs on the console; the PC app does not launch JKSV or restore the save itself. If you only have a standard Switch 2 and no modified Switch 1, this route cannot be used with your current hardware. The package was built for US demo 1.0.0. Two community reports say it also works with UK/EU demo 1.0.0 on Switch 2 system version 23.0.1 after JKSV restore on Switch 1 and local transfer. This project has not reproduced those trials; review the report before using another edition: https://github.com/DialingSpoon527/seedsow-lua-editor/issues/2

JKSV project and source: https://github.com/J-D-K/JKSV

## Game compatibility

The published starter package is built for Seedsow Lullaby US demo 1.0.0. Two community reports say it also works with UK/EU demo 1.0.0, after JKSV restore on Switch 1 and transfer to a Switch 2 on system version 23.0.1. This repository has not reproduced that result, and package verification does not prove another edition or region can load it.

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

