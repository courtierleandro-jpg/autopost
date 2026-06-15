"""
Publication TikTok via Content Posting API v2.
TIKTOK_DIRECT_POST=false (défaut) → brouillon (INBOX), validation en 1 tap dans l'app.
TIKTOK_DIRECT_POST=true → publication directe (après audit de l'app TikTok).
TIKTOK_FORCE_VIDEO=true → convertit l'image en vidéo 5s via ffmpeg (fallback).
Refresh automatique du token si TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET sont définis.
"""
import logging
import mimetypes
import os
import subprocess
import time

import requests

log = logging.getLogger(__name__)

TIKTOK_API = "https://open.tiktokapis.com/v2"


class TikTokError(Exception):
    pass


class TokenExpiredError(TikTokError):
    pass


def post_to_tiktok(image_path: str, caption: str) -> str:
    """Publie une image sur TikTok. Retourne le publish_id."""
    token = _get_valid_token()
    force_video = os.environ.get("TIKTOK_FORCE_VIDEO", "false").lower() == "true"

    try:
        return _publish_with_token(token, image_path, caption, force_video)
    except TokenExpiredError:
        log.warning("Token TikTok expiré, tentative de refresh et réessai…")
        token = _force_refresh_token()
        return _publish_with_token(token, image_path, caption, force_video)


def _publish_with_token(token: str, image_path: str, caption: str, force_video: bool) -> str:
    if force_video:
        return _post_as_video(token, image_path, caption)
    try:
        return _upload_photo(token, image_path, caption)
    except TikTokError as exc:
        if any(kw in str(exc).upper() for kw in ("PHOTO", "MEDIA_TYPE", "NOT_SUPPORTED")):
            log.warning("Photo API indisponible (%s), conversion vidéo…", exc)
            return _post_as_video(token, image_path, caption)
        raise


# ─── Token management ────────────────────────────────────────────────────────

def _get_valid_token() -> str:
    token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
    if token:
        return token

    refresh = os.environ.get("TIKTOK_REFRESH_TOKEN", "")
    client_key = os.environ.get("TIKTOK_CLIENT_KEY", "")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "")

    if not (refresh and client_key and client_secret):
        raise TikTokError(
            "Configure TIKTOK_ACCESS_TOKEN, ou les 3 variables "
            "TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET + TIKTOK_REFRESH_TOKEN."
        )
    return _refresh_access_token(refresh, client_key, client_secret)


def _force_refresh_token() -> str:
    """Rafraîchit le token même si TIKTOK_ACCESS_TOKEN est présent (fallback sur expiration)."""
    refresh = os.environ.get("TIKTOK_REFRESH_TOKEN", "")
    client_key = os.environ.get("TIKTOK_CLIENT_KEY", "")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "")
    if not (refresh and client_key and client_secret):
        raise TikTokError(
            "Token TikTok expiré et impossible de rafraîchir : "
            "TIKTOK_REFRESH_TOKEN, TIKTOK_CLIENT_KEY et TIKTOK_CLIENT_SECRET requis."
        )
    return _refresh_access_token(refresh, client_key, client_secret)


def _refresh_access_token(refresh_token: str, client_key: str, client_secret: str) -> str:
    log.info("TikTok: rafraîchissement du token…")
    resp = requests.post(
        f"{TIKTOK_API}/oauth/token/",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    data = resp.json()
    token_data = data.get("data", {})
    if "access_token" not in token_data:
        raise TokenExpiredError(
            f"Impossible de rafraîchir le token TikTok : {data}. "
            "Refais l'OAuth et mets à jour TIKTOK_ACCESS_TOKEN + TIKTOK_REFRESH_TOKEN dans les secrets GitHub."
        )

    new_access = token_data["access_token"]
    new_refresh = token_data.get("refresh_token", refresh_token)
    _persist_tokens(new_access, new_refresh)
    return new_access


def _persist_tokens(access_token: str, refresh_token: str) -> None:
    """Met à jour les secrets GitHub via l'API si GITHUB_PAT est disponible."""
    pat = os.environ.get("GITHUB_PAT", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not (pat and repo):
        log.warning(
            "Tokens rafraîchis mais GITHUB_PAT absent — mets à jour manuellement "
            "TIKTOK_ACCESS_TOKEN et TIKTOK_REFRESH_TOKEN dans Settings → Secrets GitHub."
        )
        return
    try:
        _update_github_secret(pat, repo, "TIKTOK_ACCESS_TOKEN", access_token)
        _update_github_secret(pat, repo, "TIKTOK_REFRESH_TOKEN", refresh_token)
        log.info("Secrets TikTok mis à jour dans GitHub.")
    except Exception as exc:
        log.warning("Impossible de mettre à jour les secrets GitHub : %s", exc)


def _update_github_secret(pat: str, repo: str, name: str, value: str) -> None:
    try:
        from nacl import encoding, public
    except ImportError:
        raise TikTokError("PyNaCl requis : pip install PyNaCl")

    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
    }
    r = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers, timeout=10,
    )
    r.raise_for_status()
    key_data = r.json()

    pub_key = public.PublicKey(key_data["key"].encode(), encoding.Base64Encoder())
    encrypted = public.SealedBox(pub_key).encrypt(
        value.encode(), encoding.Base64Encoder()
    ).decode()

    r = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        headers=headers,
        json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
        timeout=10,
    )
    r.raise_for_status()


# ─── Photo upload ─────────────────────────────────────────────────────────────

def _upload_photo(token: str, image_path: str, caption: str) -> str:
    """Upload une image via TikTok Content Posting API (media_type=PHOTO)."""
    file_size = os.path.getsize(image_path)
    direct = os.environ.get("TIKTOK_DIRECT_POST", "false").lower() == "true"
    post_mode = "DIRECT_POST" if direct else "INBOX"
    privacy = "PUBLIC_TO_EVERYONE" if direct else "SELF_ONLY"

    log.info("TikTok photo: %s, %d bytes, mode=%s", os.path.basename(image_path), file_size, post_mode)

    init_resp = requests.post(
        f"{TIKTOK_API}/post/publish/content/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": caption[:2200],
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "photo_cover_index": 0,
                "photo_images": [{"file_size": file_size}],
            },
            "post_mode": post_mode,
            "media_type": "PHOTO",
        },
        timeout=30,
    )
    _raise_for_tiktok_error(init_resp, "init photo")

    init_data = init_resp.json()["data"]
    publish_id = init_data["publish_id"]
    # L'API peut retourner upload_url ou photo_upload_urls[0]
    upload_url = init_data.get("upload_url") or (init_data.get("photo_upload_urls") or [None])[0]
    if not upload_url:
        raise TikTokError(f"Pas d'URL d'upload dans la réponse TikTok : {init_data}")

    log.info("TikTok photo: upload vers %s…", upload_url[:70])
    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": mime, "Content-Length": str(file_size)},
            timeout=60,
        )
    if put_resp.status_code not in (200, 201, 204):
        raise TikTokError(f"Upload image TikTok échoué (HTTP {put_resp.status_code}): {put_resp.text[:200]}")

    _wait_for_publish(token, publish_id)
    return publish_id


# ─── Video fallback ───────────────────────────────────────────────────────────

def _post_as_video(token: str, image_path: str, caption: str) -> str:
    """Convertit l'image en vidéo 5s et upload en brouillon TikTok."""
    video_path = _image_to_video(image_path)
    try:
        return _upload_video(token, video_path, caption)
    finally:
        if os.path.exists(video_path):
            os.unlink(video_path)


def _image_to_video(image_path: str) -> str:
    output = os.path.splitext(image_path)[0] + "_tmp.mp4"
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            output,
        ],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise TikTokError(f"ffmpeg échec : {result.stderr.decode()[:300]}")
    return output


def _upload_video(token: str, video_path: str, caption: str) -> str:
    file_size = os.path.getsize(video_path)
    direct = os.environ.get("TIKTOK_DIRECT_POST", "false").lower() == "true"
    privacy = "PUBLIC_TO_EVERYONE" if direct else "SELF_ONLY"

    endpoint = (
        f"{TIKTOK_API}/post/publish/video/init/"
        if direct
        else f"{TIKTOK_API}/post/publish/inbox/video/init/"
    )
    log.info("TikTok video: %d bytes, direct=%s", file_size, direct)

    init_resp = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": min(file_size, 10 * 1024 * 1024),
                "total_chunk_count": 1,
            },
            "post_info": {
                "title": caption[:2200],
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
        },
        timeout=30,
    )
    _raise_for_tiktok_error(init_resp, "init vidéo")

    init_data = init_resp.json()["data"]
    publish_id = init_data["publish_id"]
    upload_url = init_data["upload_url"]

    with open(video_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size),
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            },
            timeout=120,
        )
    if put_resp.status_code not in (200, 201, 204):
        raise TikTokError(f"Upload vidéo TikTok échoué (HTTP {put_resp.status_code}): {put_resp.text[:200]}")

    _wait_for_publish(token, publish_id)
    return publish_id


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _wait_for_publish(token: str, publish_id: str, max_attempts: int = 12) -> None:
    for attempt in range(max_attempts):
        time.sleep(3)
        resp = requests.post(
            f"{TIKTOK_API}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"publish_id": publish_id},
            timeout=15,
        )
        if resp.status_code != 200:
            continue
        status = resp.json().get("data", {}).get("status", "")
        log.info("TikTok: statut = %s (tentative %d/%d)", status, attempt + 1, max_attempts)
        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            return
        if "FAILED" in status or "ERROR" in status:
            reason = resp.json().get("data", {}).get("fail_reason", "inconnu")
            raise TikTokError(f"Publication TikTok échouée : {status} — {reason}")
    log.warning("TikTok: statut non confirmé après %d tentatives (publish_id=%s)", max_attempts, publish_id)


def _raise_for_tiktok_error(resp: requests.Response, action: str) -> None:
    if resp.status_code == 200:
        return
    try:
        err = resp.json().get("error", {})
        code = str(err.get("code", ""))
        msg = err.get("message", resp.text[:200])
    except Exception:
        code, msg = "", resp.text[:200]

    if resp.status_code == 401 or code in ("access_token_invalid", "access_token_expired"):
        raise TokenExpiredError(
            f"Token TikTok expiré — mets à jour TIKTOK_ACCESS_TOKEN et TIKTOK_REFRESH_TOKEN. Détail: {msg}"
        )
    raise TikTokError(f"Erreur TikTok {action} (HTTP {resp.status_code}): {msg}")
