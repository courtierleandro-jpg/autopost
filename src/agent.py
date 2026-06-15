"""
Module IA — Phase 2 : génération de captions et planning mensuel via Gemini Flash.

generate_caption(platform, image_path, brand, context=None) -> str
    Génère une caption adaptée à la brand identity.
    brand="htt"   → ton pro, artisans/PME Île-de-France, SEO local, emojis OK
    brand="nexum" → ton percutant, mindset/discipline/trading, jamais d'emoji

fill_monthly_plan(brand, year, month, theme_overrides=None) -> list[dict]
    Génère un planning mensuel (lun/mer/ven) pour la brand.
    Retourne des dicts compatibles avec le format posts.csv.

suggest_visuals(brand, month, n=10) -> list[dict]
    Propose n briefs visuels actionnables pour un graphiste.

Requis : variable d'environnement GOOGLE_API_KEY (secret GitHub à ajouter).
Modèle : gemini-2.0-flash (vision incluse, ~20x moins cher qu'Anthropic).
"""
import json
import logging
import mimetypes
import os
from datetime import date, timedelta

from google import genai
from google.genai import types

log = logging.getLogger(__name__)

MODEL = "gemini-2.0-flash"

BRAND_PROMPTS = {
    "htt": (
        "Tu es le copywriter de HTT Digital, agence web pour artisans et PME en Île-de-France. "
        "Ton ton est professionnel mais accessible, orienté SEO local. "
        "Tu peux utiliser des emojis pertinents. Max 2200 caractères, max 30 hashtags."
    ),
    "nexum": (
        "Tu es le copywriter de NEXUM Mindset, marque de développement personnel axée trading et discipline. "
        "Ton ton est percutant, direct, inspirant. N'utilise JAMAIS d'emoji. "
        "Phrases courtes, impactantes. Max 2200 caractères."
    ),
}

PLATFORM_HINTS = {
    "instagram": "Caption pour Instagram : valorise l'image, appel à l'action clair, hashtags pertinents.",
    "tiktok": "Caption pour TikTok : accroche immédiate, texte court et percutant, 1-3 hashtags max.",
}

DEFAULT_TIMES = {
    "instagram": "18:00",
    "tiktok": "19:30",
}


def _client() -> genai.Client:
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY absent — ajoute-le en variable d'environnement "
            "ou comme secret GitHub (Settings → Secrets → Actions)."
        )
    return genai.Client(api_key=key)


def _generate(system: str, user_parts: list, max_tokens: int = 1024) -> str:
    """Appel Gemini avec system instruction et contenu utilisateur."""
    response = _client().models.generate_content(
        model=MODEL,
        contents=[types.Content(role="user", parts=user_parts)],
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()


def _parse_json_response(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_caption(
    platform: str,
    image_path: str | None,
    brand: str,
    context: str | None = None,
) -> str:
    """
    Génère une caption prête à publier.
    Si image_path est fourni et le fichier existe, analyse l'image via vision.
    """
    if brand not in BRAND_PROMPTS:
        raise ValueError(f"Brand inconnue : '{brand}'. Valeurs : {list(BRAND_PROMPTS)}")
    if platform not in PLATFORM_HINTS:
        raise ValueError(f"Plateforme inconnue : '{platform}'. Valeurs : {list(PLATFORM_HINTS)}")

    parts: list = []

    if image_path and os.path.exists(image_path):
        mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        with open(image_path, "rb") as f:
            parts.append(types.Part.from_bytes(data=f.read(), mime_type=mime))

    user_text = PLATFORM_HINTS[platform]
    if context:
        user_text += f"\n\nContexte / thème : {context}"
    if parts:
        user_text += "\n\nAnalyse l'image et génère la caption. Réponds uniquement avec la caption."
    else:
        user_text += "\n\nGénère une caption percutante. Réponds uniquement avec la caption."
    parts.append(types.Part.from_text(text=user_text))

    caption = _generate(BRAND_PROMPTS[brand], parts, max_tokens=1024)
    log.info("Caption générée pour %s/%s (%d chars)", brand, platform, len(caption))
    return caption


def fill_monthly_plan(
    brand: str,
    year: int,
    month: int,
    theme_overrides: dict | None = None,
) -> list[dict]:
    """
    Génère un planning mensuel de posts (lun/mer/ven) pour la brand.
    theme_overrides : {date_str: "thème du jour"} pour surcharger certaines dates.
    Retourne une liste de dicts prêts à être écrits dans posts.csv.
    """
    if brand not in BRAND_PROMPTS:
        raise ValueError(f"Brand inconnue : '{brand}'.")

    platform = "instagram" if brand == "htt" else "tiktok"
    heure = DEFAULT_TIMES[platform]

    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    post_dates = [
        start + timedelta(days=i)
        for i in range((end - start).days)
        if (start + timedelta(days=i)).weekday() in (0, 2, 4)
    ]

    themes_info = ""
    if theme_overrides:
        lines = [f"  - {d} : {t}" for d, t in theme_overrides.items()]
        themes_info = "\nThèmes imposés pour certaines dates :\n" + "\n".join(lines)

    prompt = (
        f"Génère un planning de {len(post_dates)} posts {platform.capitalize()} pour {brand.upper()} "
        f"sur le mois {month:02d}/{year}.\n"
        f"Dates : {', '.join(str(d) for d in post_dates)}"
        f"{themes_info}\n\n"
        f"Réponds UNIQUEMENT avec un JSON array sans markdown :\n"
        f'[{{"date": "YYYY-MM-DD", "caption": "..."}}]'
    )

    raw = _generate(BRAND_PROMPTS[brand], [types.Part.from_text(text=prompt)], max_tokens=4096)
    entries = _parse_json_response(raw)

    plan = [
        {
            "date": e["date"],
            "heure": heure,
            "plateforme": platform,
            "image": f"{brand}/post_{i:03d}.jpg",
            "caption": e["caption"],
            "statut": "planifie",
        }
        for i, e in enumerate(entries, start=1)
    ]
    log.info("Planning généré : %d posts pour %s %02d/%d", len(plan), brand, month, year)
    return plan


def suggest_visuals(brand: str, month: int, n: int = 10) -> list[dict]:
    """
    Propose n briefs visuels actionnables pour un graphiste.
    Retourne une liste de dicts : {titre, format, description, moodboard, cta}.
    """
    if brand not in BRAND_PROMPTS:
        raise ValueError(f"Brand inconnue : '{brand}'.")

    month_names = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    month_name = month_names[month] if 1 <= month <= 12 else str(month)
    platform = "Instagram" if brand == "htt" else "TikTok"

    prompt = (
        f"Propose {n} briefs visuels pour {brand.upper()} en {month_name}, pour {platform}.\n"
        f"Chaque brief doit être directement actionnable pour un graphiste.\n\n"
        f"Réponds UNIQUEMENT avec un JSON array sans markdown :\n"
        f'[{{\n'
        f'  "titre": "Titre court du visuel",\n'
        f'  "format": "carré 1080x1080" | "portrait 1080x1350" | "portrait 1080x1920",\n'
        f'  "description": "Éléments visuels, couleurs, ambiance",\n'
        f'  "moodboard": "mot1, mot2, mot3",\n'
        f'  "cta": "Call-to-action suggéré"\n'
        f"}}]"
    )

    raw = _generate(BRAND_PROMPTS[brand], [types.Part.from_text(text=prompt)], max_tokens=3000)
    briefs = _parse_json_response(raw)
    log.info("%d briefs visuels générés pour %s/%02d", len(briefs), brand, month)
    return briefs
