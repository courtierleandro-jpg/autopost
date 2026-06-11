"""
Notifications Discord via webhook (optionnel).
Si DISCORD_WEBHOOK_URL est absent, on log seulement — jamais d'erreur bloquante.
"""
import logging
import os

import requests

log = logging.getLogger(__name__)


def send_notification(message: str, level: str = "info") -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        return

    colors = {"info": 0x00AE86, "warning": 0xFFA500, "error": 0xFF0000}
    color = colors.get(level, 0x808080)

    try:
        resp = requests.post(
            webhook_url,
            json={
                "embeds": [{
                    "description": message,
                    "color": color,
                    "footer": {"text": "autopost 🤖"},
                }]
            },
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Impossible d'envoyer la notif Discord : %s", exc)
