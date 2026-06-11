"""
Validation de posts.csv avant publication.
Exit code 1 si des erreurs sont détectées (bloque le workflow GitHub Actions).
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
POSTS_CSV = BASE_DIR / "posts.csv"
IMAGES_DIR = BASE_DIR / "images"

IG_CAPTION_MAX = 2200
IG_HASHTAG_MAX = 30
TIKTOK_CAPTION_MAX = 2200
VALID_PLATFORMS = {"instagram", "tiktok"}
VALID_STATUTS = {"planifie", "publie", "ignore"}

errors: list = []
warnings: list = []


def main() -> None:
    print(f"Validation de {POSTS_CSV}…\n")

    try:
        with POSTS_CSV.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
    except FileNotFoundError:
        print("ERREUR : posts.csv introuvable.")
        sys.exit(1)
    except Exception as exc:
        print(f"ERREUR lecture posts.csv : {exc}")
        sys.exit(1)

    required_headers = {"date", "heure", "plateforme", "image", "caption", "statut"}
    if rows:
        missing = required_headers - set(rows[0].keys())
        if missing:
            errors.append(f"Colonnes manquantes dans l'en-tête : {sorted(missing)}")

    keys_seen: set = set()
    for i, row in enumerate(rows, start=2):
        _validate_row(i, row, keys_seen)

    if warnings:
        print(f"⚠️  {len(warnings)} avertissement(s) :")
        for w in warnings:
            print(f"   • {w}")
        print()

    if errors:
        print(f"❌ {len(errors)} erreur(s) :")
        for e in errors:
            print(f"   • {e}")
        print()
        sys.exit(1)
    else:
        print(f"✓ {len(rows)} ligne(s) validée(s) sans erreur.")


def _validate_row(line: int, row: dict, keys_seen: set) -> None:
    date_str = row.get("date", "").strip()
    heure_str = row.get("heure", "").strip()
    platform = row.get("plateforme", "").strip().lower()
    image = row.get("image", "").strip()
    caption = row.get("caption", "").strip()
    statut = row.get("statut", "").strip().lower()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        errors.append(f"Ligne {line}: date invalide '{date_str}' — format attendu YYYY-MM-DD")

    try:
        datetime.strptime(heure_str, "%H:%M")
    except ValueError:
        errors.append(f"Ligne {line}: heure invalide '{heure_str}' — format attendu HH:MM")

    if platform not in VALID_PLATFORMS:
        errors.append(f"Ligne {line}: plateforme '{platform}' invalide — valeurs : {sorted(VALID_PLATFORMS)}")

    if statut not in VALID_STATUTS:
        errors.append(f"Ligne {line}: statut '{statut}' invalide — valeurs : {sorted(VALID_STATUTS)}")

    if image:
        img_path = IMAGES_DIR / image
        if not img_path.exists():
            errors.append(f"Ligne {line}: image introuvable → images/{image}")
    else:
        errors.append(f"Ligne {line}: colonne 'image' vide")

    key = f"{date_str}_{heure_str}_{platform}_{image}"
    if key in keys_seen:
        errors.append(f"Ligne {line}: doublon détecté ({date_str} {heure_str} {platform} {image})")
    keys_seen.add(key)

    if not caption:
        warnings.append(f"Ligne {line}: caption vide")
        return

    if platform == "instagram":
        if len(caption) > IG_CAPTION_MAX:
            errors.append(
                f"Ligne {line}: caption Instagram trop longue ({len(caption)} chars, max {IG_CAPTION_MAX})"
            )
        hashtag_count = len(re.findall(r"#\w+", caption))
        if hashtag_count > IG_HASHTAG_MAX:
            warnings.append(
                f"Ligne {line}: {hashtag_count} hashtags Instagram (recommandé ≤ {IG_HASHTAG_MAX})"
            )

    elif platform == "tiktok":
        if len(caption) > TIKTOK_CAPTION_MAX:
            errors.append(
                f"Ligne {line}: caption TikTok trop longue ({len(caption)} chars, max {TIKTOK_CAPTION_MAX})"
            )


if __name__ == "__main__":
    main()
