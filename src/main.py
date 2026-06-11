"""
Point d'entrée du système autopost.
Lit posts.csv, identifie les posts dus (fenêtre 30 min), publie via le module approprié.
"""
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytz

sys.path.insert(0, os.path.dirname(__file__))
from instagram import post_to_instagram
from tiktok import post_to_tiktok
from notify import send_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

PARIS_TZ = pytz.timezone("Europe/Paris")
TOLERANCE_MIN = 30
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

BASE_DIR = Path(__file__).parent.parent
POSTS_CSV = BASE_DIR / "posts.csv"
PUBLISHED_JSON = BASE_DIR / "published.json"
IMAGES_DIR = BASE_DIR / "images"


def load_published() -> dict:
    if PUBLISHED_JSON.exists():
        return json.loads(PUBLISHED_JSON.read_text(encoding="utf-8"))
    return {}


def save_published(data: dict) -> None:
    PUBLISHED_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_posts() -> list:
    with POSTS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def post_key(post: dict) -> str:
    return f"{post['date']}_{post['heure']}_{post['plateforme']}_{post['image']}"


def is_due(post: dict, now: datetime) -> bool:
    try:
        dt = PARIS_TZ.localize(
            datetime.strptime(f"{post['date']} {post['heure']}", "%Y-%m-%d %H:%M")
        )
    except ValueError:
        return False
    delta = (now - dt).total_seconds() / 60
    return 0 <= delta <= TOLERANCE_MIN


def main() -> None:
    now = datetime.now(pytz.utc).astimezone(PARIS_TZ)
    log.info("Démarrage — %s (heure Paris)%s", now.strftime("%Y-%m-%d %H:%M"),
             " [DRY RUN]" if DRY_RUN else "")

    try:
        posts = load_posts()
    except FileNotFoundError:
        log.error("posts.csv introuvable dans %s", BASE_DIR)
        sys.exit(1)

    published = load_published()

    due = [
        p for p in posts
        if p.get("statut", "").strip().lower() == "planifie"
        and post_key(p) not in published
        and is_due(p, now)
    ]

    if not due:
        log.info("Aucun post à publier pour ce créneau.")
        return

    log.info("%d post(s) à publier.", len(due))

    for post in due:
        key = post_key(post)
        platform = post["plateforme"].strip().lower()
        image_path = IMAGES_DIR / post["image"].strip()
        caption = post["caption"].strip()

        if DRY_RUN:
            log.info("[DRY RUN] %s — %s | caption: %.60s…", platform, post["image"], caption)
            continue

        if not image_path.exists():
            log.error("Image introuvable : %s — post ignoré.", image_path)
            send_notification(
                f"⚠️ **Image manquante**\n`{post['image']}` introuvable — post ignoré.",
                level="warning",
            )
            continue

        try:
            if platform == "instagram":
                post_id = post_to_instagram(str(image_path), caption)
            elif platform == "tiktok":
                post_id = post_to_tiktok(str(image_path), caption)
            else:
                log.error("Plateforme inconnue : %s", platform)
                continue

            published[key] = {
                "post_id": post_id,
                "published_at": now.isoformat(),
                "platform": platform,
                "image": post["image"],
            }
            save_published(published)
            log.info("[OK] %s — %s (ID: %s)", platform, post["image"], post_id)

        except Exception as exc:
            log.error("[ECHEC] %s — %s : %s", platform, post["image"], exc)
            send_notification(
                f"❌ **Autopost ÉCHEC**\n"
                f"`{platform.upper()}` — `{post['image']}`\n"
                f"```\n{str(exc)[:500]}\n```",
                level="error",
            )


if __name__ == "__main__":
    main()
