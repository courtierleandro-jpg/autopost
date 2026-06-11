"""
Rafraîchit le Meta Long-Lived Token (validité 60 jours → renouveler tous les ~50 jours).
Exécuté automatiquement le 1er de chaque mois par GitHub Actions (refresh_meta_token.yml).
Nécessite : META_ACCESS_TOKEN, META_APP_ID, META_APP_SECRET.
Nécessite pour auto-update : GITHUB_PAT (fine-grained PAT avec secrets:write sur ce repo).
"""
import logging
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(__file__))
from notify import send_notification
from tiktok import _update_github_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    token = os.environ.get("META_ACCESS_TOKEN", "")
    app_id = os.environ.get("META_APP_ID", "")
    app_secret = os.environ.get("META_APP_SECRET", "")

    if not all([token, app_id, app_secret]):
        log.error("META_ACCESS_TOKEN, META_APP_ID et META_APP_SECRET sont requis.")
        sys.exit(1)

    log.info("Rafraîchissement du token Meta…")
    resp = requests.get(
        "https://graph.facebook.com/v21.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
        timeout=15,
    )

    if resp.status_code != 200:
        msg = resp.text[:300]
        log.error("Échec rafraîchissement : %s", msg)
        send_notification(
            f"❌ **Meta Token** — Impossible de rafraîchir\n```{msg}```",
            level="error",
        )
        sys.exit(1)

    new_token = resp.json().get("access_token", "")
    if not new_token:
        log.error("Pas de token dans la réponse : %s", resp.json())
        sys.exit(1)

    log.info("Nouveau token Meta obtenu.")

    pat = os.environ.get("GITHUB_PAT", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    if pat and repo:
        try:
            _update_github_secret(pat, repo, "META_ACCESS_TOKEN", new_token)
            log.info("Secret META_ACCESS_TOKEN mis à jour dans GitHub.")
            send_notification("✅ **Meta Token** — Rafraîchi et sauvegardé avec succès.", level="info")
        except Exception as exc:
            log.warning("Mise à jour secret GitHub échouée : %s", exc)
            send_notification(
                f"⚠️ **Meta Token** — Rafraîchi mais non sauvegardé.\n"
                f"Mets à jour `META_ACCESS_TOKEN` manuellement.\n```{exc}```",
                level="warning",
            )
    else:
        log.warning("GITHUB_PAT absent — mets à jour META_ACCESS_TOKEN manuellement dans les secrets GitHub.")
        send_notification(
            "⚠️ **Meta Token** — Rafraîchi mais GITHUB_PAT absent.\n"
            "Mets à jour `META_ACCESS_TOKEN` manuellement dans Settings → Secrets.",
            level="warning",
        )


if __name__ == "__main__":
    main()
