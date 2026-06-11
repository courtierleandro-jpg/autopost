# Autopost — HTT Digital + NEXUM Mindset

Système de publication automatique pour Instagram et TikTok.
Coût d'hébergement : **0€** (GitHub Actions).

## Architecture

```
posts.csv          → planning éditorial (source de vérité)
published.json     → log anti-doublon des posts publiés
images/            → visuels locaux (miroir de autopost-assets)
src/main.py        → logique principale : lit CSV, publie, loggue
src/instagram.py   → Meta Graph API v21.0
src/tiktok.py      → TikTok Content Posting API v2
src/notify.py      → notifications Discord
src/validate.py    → validation CSV (déclenché à chaque push)
src/agent.py       → Phase 2 : génération IA des captions (placeholder)
```

## Workflows GitHub Actions

| Workflow | Déclenchement | Rôle |
|----------|---------------|------|
| `publish.yml` | Toutes les 15 min (cron UTC) | Publie les posts dus |
| `validate.yml` | À chaque push de posts.csv ou images/ | Valide le format du planning |
| `refresh_meta_token.yml` | 1er du mois à 7h UTC | Renouvelle le token Meta (60 jours) |

## Mise en route

1. Lis et suis **[docs/SETUP_META.md](docs/SETUP_META.md)** — Instagram / Meta (~30 min)
2. Lis et suis **[docs/SETUP_TIKTOK.md](docs/SETUP_TIKTOK.md)** — TikTok (~30 min)
3. Utilisation quotidienne : **[docs/USAGE.md](docs/USAGE.md)**

## Variables d'environnement (secrets GitHub)

| Secret | Description | Requis pour |
|--------|-------------|-------------|
| `META_ACCESS_TOKEN` | Token long-lived Meta (60 jours) | Instagram |
| `IG_USER_ID` | ID du compte Instagram professionnel | Instagram |
| `META_APP_ID` | App ID Meta (pour le refresh mensuel) | Instagram |
| `META_APP_SECRET` | App Secret Meta (pour le refresh mensuel) | Instagram |
| `IMAGES_BASE_URL` | URL de base des images publiques | Instagram |
| `TIKTOK_CLIENT_KEY` | Client Key de l'app TikTok | TikTok |
| `TIKTOK_CLIENT_SECRET` | Client Secret de l'app TikTok | TikTok |
| `TIKTOK_ACCESS_TOKEN` | Access token TikTok (24h) | TikTok |
| `TIKTOK_REFRESH_TOKEN` | Refresh token TikTok (1 an) | TikTok |
| `TIKTOK_DIRECT_POST` | `true` = publication directe (après audit) | TikTok |
| `TIKTOK_FORCE_VIDEO` | `true` = toujours convertir image → vidéo | TikTok |
| `DISCORD_WEBHOOK_URL` | Webhook pour les alertes d'échec | Optionnel |
| `GITHUB_PAT` | PAT avec secrets:write (auto-refresh tokens) | Optionnel |

## Format posts.csv

```csv
date;heure;plateforme;image;caption;statut
2026-06-15;18:00;instagram;htt/post_001.jpg;"Caption Instagram #hashtag";planifie
2026-06-15;19:30;tiktok;nexum/post_001.jpg;"Caption TikTok";planifie
```

- Séparateur `;`
- Heure en **heure de Paris** (Europe/Paris)
- Statuts : `planifie` | `publie` | `ignore`
