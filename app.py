#!/usr/bin/env python3
"""Windows desktop package verifier for the Seedsow editor save."""

from __future__ import annotations

import hashlib
import json
import queue
import re
import threading
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
import tkinter as tk
from tkinter import ttk


REPO = "DialingSpoon527/seedsow-lua-editor"
USER_AGENT = "seedsow-save-pack-verifier/0.2"
ZIP_NAME = "Seedsow-Lua-Editor-Save.zip"
MANIFEST_NAME = "Seedsow-Lua-Editor-Save.manifest.json"
CHECKSUM_NAME = ZIP_NAME + ".sha256"
EXPECTED_GAME = "Seedsow Lullaby US demo 1.0.0"
MAX_ARCHIVE_SIZE = 128 * 1024 * 1024
MAX_UNPACKED_SIZE = 256 * 1024 * 1024
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class VerificationError(RuntimeError):
    pass


def get_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise VerificationError(f"Téléchargement impossible : {error}") from error


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def latest_release() -> dict:
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    try:
        release = json.loads(get_bytes(url))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise VerificationError("GitHub a renvoyé une fiche de version illisible.") from error
    if not isinstance(release, dict):
        raise VerificationError("GitHub a renvoyé une fiche de version inattendue.")
    if not re.fullmatch(r"v\d+\.\d+\.\d+", str(release.get("tag_name", ""))):
        raise VerificationError("La version publiée a un nom inattendu.")
    return release


def asset_url(release: dict, name: str) -> str:
    for asset in release.get("assets", []):
        if asset.get("name") == name:
            url = asset.get("browser_download_url", "")
            if url.startswith("https://github.com/"):
                return url
    raise VerificationError(f"Le paquet publié ne contient pas {name}.")


def validate_archive(zip_bytes: bytes, manifest: dict) -> tuple[int, int]:
    if len(zip_bytes) > MAX_ARCHIVE_SIZE:
        raise VerificationError("Le ZIP dépasse la taille maximale prise en charge.")
    if not isinstance(manifest, dict):
        raise VerificationError("Le manifeste publié n'est pas un objet JSON valide.")
    if manifest.get("kind") != "ready-to-restore-editor-save":
        raise VerificationError("Le manifeste ne décrit pas une sauvegarde éditeur prête.")
    if manifest.get("game") != EXPECTED_GAME:
        raise VerificationError(
            "Cette version est bâtie pour Seedsow Lullaby démo US 1.0.0; "
            "la compatibilité de ta démo européenne n'est pas établie par ce paquet."
        )
    if manifest.get("personal_account_metadata_included") is not False:
        raise VerificationError("Le paquet ne confirme pas l'absence de données personnelles.")
    if manifest.get("user_programs_included") is not False:
        raise VerificationError("Le paquet ne confirme pas l'absence de programmes personnels.")

    expected = manifest.get("save_files")
    if not isinstance(expected, dict) or not expected:
        raise VerificationError("Le manifeste ne contient pas la liste de fichiers attendue.")
    if len(expected) > 2000:
        raise VerificationError("Le manifeste annonce un nombre de fichiers inattendu.")

    seen: set[str] = set()
    installable = 0
    total_bytes = 0
    try:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
            if len(archive.infolist()) > 2000:
                raise VerificationError("Le ZIP contient trop d'entrées.")
            for item in archive.infolist():
                name = item.filename
                if item.is_dir():
                    raise VerificationError(f"Dossier inattendu dans le ZIP : {name!r}")
                relative = PurePosixPath(name)
                if (
                    relative.is_absolute()
                    or len(relative.parts) != 1
                    or ".." in relative.parts
                    or "\\" in name
                ):
                    raise VerificationError(f"Chemin inattendu dans le ZIP : {name!r}")
                if name in seen:
                    raise VerificationError(f"Fichier en double dans le ZIP : {name}")
                seen.add(name)
                if name not in expected:
                    raise VerificationError(f"Fichier non déclaré dans le manifeste : {name}")
                if item.file_size > MAX_UNPACKED_SIZE - total_bytes:
                    raise VerificationError("Le contenu décompressé dépasse la limite prise en charge.")
                data = archive.read(item)
                if sha256(data) != str(expected[name]).lower():
                    raise VerificationError(f"Empreinte incorrecte pour {name}.")
                total_bytes += len(data)
                if name.startswith("."):
                    if name != ".nx_save_meta.bin":
                        raise VerificationError(f"Fichier caché inattendu : {name}")
                else:
                    if not SAFE_NAME.fullmatch(name):
                        raise VerificationError(f"Nom de fichier non sûr : {name!r}")
                    installable += 1
    except zipfile.BadZipFile as error:
        raise VerificationError("Le fichier téléchargé n'est pas un ZIP valide.") from error

    if seen != set(expected):
        missing = sorted(set(expected) - seen)
        raise VerificationError("Fichiers absents du ZIP : " + ", ".join(missing[:8]))
    if installable == 0:
        raise VerificationError("Le paquet ne contient aucun fichier de sauvegarde installable.")
    return installable, total_bytes


def download_and_verify(output_dir: Path) -> tuple[Path, str, int, int]:
    release = latest_release()
    tag = release["tag_name"]
    zip_bytes = get_bytes(asset_url(release, ZIP_NAME))
    manifest_bytes = get_bytes(asset_url(release, MANIFEST_NAME))
    checksum_bytes = get_bytes(asset_url(release, CHECKSUM_NAME))
    try:
        manifest = json.loads(manifest_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise VerificationError("Le manifeste publié n'est pas un JSON valide.") from error

    checksum = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum_bytes)
    if not checksum:
        raise VerificationError("Le fichier de sommes SHA-256 est illisible.")
    digest = sha256(zip_bytes)
    if digest != checksum.group(1).decode("ascii").lower():
        raise VerificationError("Le ZIP ne correspond pas à sa somme SHA-256 publiée.")
    if digest != str(manifest.get("sha256", "")).lower():
        raise VerificationError("Le ZIP ne correspond pas au hash indiqué dans le manifeste.")
    count, size = validate_archive(zip_bytes, manifest)

    target_dir = output_dir / tag
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / ZIP_NAME
    zip_path.write_bytes(zip_bytes)
    (target_dir / MANIFEST_NAME).write_bytes(manifest_bytes)
    (target_dir / CHECKSUM_NAME).write_bytes(checksum_bytes)
    return zip_path, tag, count, size


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Seedsow — vérificateur de paquet")
        self.geometry("720x520")
        self.minsize(640, 460)
        self.output_dir = Path(__file__).resolve().parent / "downloads"
        self.messages: queue.Queue[tuple[bool, object]] = queue.Queue()
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Seedsow Save Pack", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            root,
            text="Télécharger et vérifier le paquet public de l’éditeur avant toute installation.",
            wraplength=660,
        ).pack(anchor="w", pady=(5, 18))

        warning = ttk.LabelFrame(root, text="État de l’import sur ta console", padding=12)
        warning.pack(fill="x", pady=(0, 16))
        ttk.Label(
            warning,
            text=(
                "Cette version vérifie et prépare le ZIP sur Windows; elle n’écrit rien sur la Switch.\n"
                "Aucune interface publique d’import depuis une Switch 2 standard sans SmileBASIC "
                "n’est documentée pour l’instant."
            ),
            wraplength=630,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(
            warning,
            text=(
                "Attention : le paquet disponible vise la démo US 1.0.0. La compatibilité de la "
                "démo européenne de ta console reste à confirmer."
            ),
            wraplength=630,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        self.download_button = ttk.Button(
            root, text="Télécharger et vérifier la dernière version", command=self._start
        )
        self.download_button.pack(anchor="w")
        self.status = ttk.Label(root, text="Prêt.", wraplength=660, justify="left")
        self.status.pack(anchor="w", pady=(14, 8))

        self.details = tk.Text(root, height=9, wrap="word", state="disabled", font=("Consolas", 10))
        self.details.pack(fill="both", expand=True)
        ttk.Label(
            root,
            text=f"Dossier de sortie : {self.output_dir}",
            wraplength=660,
        ).pack(anchor="w", pady=(10, 0))

    def _start(self) -> None:
        self.download_button.configure(state="disabled")
        self.status.configure(text="Téléchargement depuis GitHub et vérification des empreintes…")
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()
        self.after(150, self._poll)

    def _worker(self) -> None:
        try:
            result = download_and_verify(self.output_dir)
            self.messages.put((True, result))
        except (VerificationError, OSError, KeyError, TypeError, ValueError) as error:
            self.messages.put((False, str(error)))

    def _poll(self) -> None:
        try:
            success, result = self.messages.get_nowait()
        except queue.Empty:
            self.after(150, self._poll)
            return
        self.download_button.configure(state="normal")
        if not success:
            self.status.configure(text="Vérification échouée; aucun paquet certifié n’a été préparé.")
            self._set_details(str(result))
            return

        path, tag, count, size = result
        self.status.configure(text="Paquet téléchargé et vérifié. Aucun fichier n’a été envoyé à la console.")
        self._set_details(
            f"Version : {tag}\n"
            f"Fichiers de sauvegarde vérifiés : {count}\n"
            f"Taille décompressée : {size:,} octets\n"
            f"Paquet : {path}\n\n"
            "Étape console : indisponible dans cette version pour une Switch 2 standard "
            "sans SmileBASIC."
        )

    def _set_details(self, value: str) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", value)
        self.details.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()

