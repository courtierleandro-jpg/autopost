"""
Publication Instagram via Meta Graph API v21.0.
Flow : créer container (image_url + caption) → pause 5s → publier.
L'image doit être publiquement accessible (IMAGES_BASE_URL → repo autopost-assets).
"""
import logging
import os
import time

import requests

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v21.0"


class InstagramError(Exception):
    pass


class TokenExpiredError(InstagramError):
    pass


class RateLimitError(InstagramError):
    pass


def post_to_instagram(image_path: str, caption: str) -> str:
    """Publie une image sur Instagram. Retourne l'ID du post publié."""
    token = os.environ.get("META_ACCESS_TOKEN", "")
    user_id = os.environ.get("IG_USER_ID", "")
    base_url = os.environ.get("IMAGES_BASE_URL", "").rstrip("/")

    missing = [k for k, v in {
        "META_ACCESS_TOKEN": token,
        "IG_USER_ID": user_id,
        "IMAGES_BASE_URL": base_url,
    }.items() if not v]
    if missing:
        raise InstagramError(f"Variables manquantes : {', '.join(missing)}")

    image_url = _build_image_url(image_path, base_url)
    log.info("Instagram: image URL = %s", image_url)

    container_id = _create_container(user_id, token, image_url, caption)
    log.info("Instagram: container %s créé, pause avant publication…", container_id)
    time.sleep(5)

    post_id = _publish_container(user_id, token, container_id)
    return post_id


def _build_image_url(image_path: str, base_url: str) -> str:
    parts = image_path.replace("\\", "/").split("/images/")
    relative = parts[-1] if len(parts) > 1 else os.path.basename(image_path)
    return f"{base_url}/{relative}"


def _create_container(user_id: str, token: str, image_url: str, caption: str) -> str:
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    _raise_for_error(resp, "création container")
    return resp.json()["id"]


def _publish_container(user_id: str, token: str, container_id: str) -> str:
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=30,
    )
    _raise_for_error(resp, "publication container")
    return resp.json()["id"]


def _raise_for_error(resp: requests.Response, action: str) -> None:
    if resp.status_code == 200:
        return
    try:
        err = resp.json().get("error", {})
        code = err.get("code", 0)
        msg = err.get("message", resp.text[:200])
    except Exception:
        code, msg = 0, resp.text[:200]

    if code == 190:
        raise TokenExpiredError(
            f"Token Meta expiré — renouvelle META_ACCESS_TOKEN (voir docs/SETUP_META.md). Détail: {msg}"
        )
    if resp.status_code == 429 or code in (4, 17, 32):
        raise RateLimitError(
            f"Rate limit Meta atteint — réessaie dans quelques minutes. Détail: {msg}"
        )
    raise InstagramError(f"Erreur {action} (HTTP {resp.status_code}): {msg}")
