"""
Module IA — Phase 2 (non implémenté — architecture préparée).

Interface prévue :

    generate_caption(platform, image_path, brand, context=None) -> str
        Génère une caption adaptée à la brand identity.
        brand="htt"   → ton pro, artisans/PME Île-de-France, SEO local, emojis OK
        brand="nexum" → ton percutant, mindset/discipline/trading, jamais d'emoji

    fill_monthly_plan(brand, year, month, theme_overrides=None) -> list[dict]
        Remplit le CSV pour un mois entier.
        Retourne une liste de dicts compatibles avec le format posts.csv.

    suggest_visuals(brand, month, n=10) -> list[dict]
        Propose des briefs visuels à faire valider avant génération.

Pour implémenter :
    - Utiliser l'API Anthropic (claude-sonnet-4-6) via le SDK anthropic
    - Un prompt system par brand (voir brand_prompts dict ci-dessous)
    - Entrée : image_path optionnel (vision) ou thème texte
    - Sortie : caption prête à copier dans posts.csv

brand_prompts = {
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
"""
