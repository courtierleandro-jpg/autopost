# CLAUDE.md — autopost

Tu es l'assistant de **courtierleandro-jpg** sur le projet **autopost**.
Ce projet publie automatiquement des posts Instagram et TikTok via GitHub Actions, sans serveur, sans abonnement — coût : 0€.

---

## C'est quoi autopost ?

L'utilisateur remplit un fichier `posts.csv` avec ses posts planifiés (date, heure, image, texte).
GitHub Actions tourne toutes les 15 minutes, regarde si un post est dû, et le publie automatiquement sur Instagram ou TikTok.

**Flux complet :**
```
posts.csv (planning)
    ↓ GitHub Actions (toutes les 15 min)
    ↓ src/main.py → instagram.py ou tiktok.py
    ↓ Publication sur la plateforme
    ↓ published.json (log anti-doublon)
```

**Deux marques :**
- **HTT Digital** → Instagram (`brand="htt"`) — agence web pour artisans/PME Île-de-France, ton pro, emojis OK
- **NEXUM Mindset** → TikTok (`brand="nexum"`) — développement personnel/trading/discipline, ton percutant, jamais d'emoji

---

## posts.csv — le fichier central

C'est **la seule chose à remplir au quotidien**. Il contient tous les posts planifiés.

### Format

```csv
date;heure;plateforme;image;caption;statut
2026-07-07;18:00;instagram;htt/post_001.jpg;"Votre site web mérite mieux 🚀 #artisans #webdesign";planifie
2026-07-07;19:30;tiktok;nexum/post_001.jpg;"La discipline bat le talent. Chaque jour.";planifie
```

**Séparateur** : `;` (pas de virgule)

### Colonnes

| Colonne | Format | Exemple | Notes |
|---------|--------|---------|-------|
| `date` | `YYYY-MM-DD` | `2026-07-07` | Date de publication |
| `heure` | `HH:MM` | `18:00` | **Heure de Paris** (pas UTC) |
| `plateforme` | texte | `instagram` ou `tiktok` | Tout en minuscules |
| `image` | chemin | `htt/post_001.jpg` | Relatif au dossier `images/` (= repo autopost-assets) |
| `caption` | texte | `"Mon texte #hashtag"` | Entre guillemets si contient `;` ou `#` |
| `statut` | texte | `planifie` | Voir valeurs ci-dessous |

### Valeurs du statut

- `planifie` → le post sera publié à l'heure prévue
- `publie` → déjà publié (mis à jour automatiquement dans published.json, pas dans le CSV)
- `ignore` → annulé, ne sera jamais publié

### Règles importantes

- L'heure est en **heure de Paris** — le système gère l'heure d'été automatiquement
- La fenêtre de publication est de **±30 minutes** : si le workflow rate le créneau exact, il rattrape dans les 30 min suivantes
- Un post déjà dans `published.json` ne sera **jamais republié**, même si on remet le statut à `planifie`
- On peut planifier **des mois à l'avance** — le CSV peut contenir 1 an de posts

### Exemple de planning hebdomadaire

```csv
date;heure;plateforme;image;caption;statut
2026-07-07;18:00;instagram;htt/post_001.jpg;"Lundi HTT";planifie
2026-07-09;18:00;instagram;htt/post_002.jpg;"Mercredi HTT";planifie
2026-07-11;18:00;instagram;htt/post_003.jpg;"Vendredi HTT";planifie
2026-07-07;19:30;tiktok;nexum/post_001.jpg;"Lundi NEXUM";planifie
2026-07-09;19:30;tiktok;nexum/post_002.jpg;"Mercredi NEXUM";planifie
```

---

## Les images — repo autopost-assets

Les images **ne sont pas** dans ce repo. Elles sont dans le repo public **autopost-assets** :

```
autopost-assets/
├── htt/          → visuels Instagram HTT Digital
│   ├── post_001.jpg
│   └── post_002.jpg
└── nexum/        → visuels TikTok NEXUM Mindset
    ├── post_001.jpg
    └── post_002.jpg
```

- Format recommandé : JPG ou PNG
- Instagram : carré 1080×1080 ou portrait 1080×1350
- TikTok : portrait 1080×1920
- Le repo doit avoir **GitHub Pages activé** pour que Meta puisse télécharger les images via URL publique

---

## Architecture du code

```
src/
├── main.py              → point d'entrée : lit CSV, publie, loggue
├── instagram.py         → Meta Graph API v21.0
├── tiktok.py            → TikTok Content Posting API v2 (photo + fallback vidéo)
├── agent.py             → génération IA des captions via Gemini Flash (Phase 2)
├── notify.py            → alertes Discord en cas d'échec
├── validate.py          → validation du CSV (déclenché à chaque push)
└── refresh_meta_token.py → renouvellement mensuel du token Meta

.github/workflows/
├── publish.yml          → toutes les 15 min, publie les posts dus
├── validate.yml         → à chaque push de posts.csv, vérifie le format
└── refresh_meta_token.yml → 1er du mois, renouvelle le token Meta (60 jours)

posts.csv                → planning éditorial (à remplir)
published.json           → log des posts déjà publiés (ne pas modifier à la main)
```

---

## Tâches courantes

### Planifier un post
1. Uploader l'image dans `autopost-assets/htt/` ou `autopost-assets/nexum/`
2. Ajouter une ligne dans `posts.csv`
3. Pusher `posts.csv` → la validation se déclenche automatiquement

### Annuler un post planifié
Changer `planifie` → `ignore` dans `posts.csv` et pusher.

### Générer des captions avec l'IA (Phase 2)
```python
from src.agent import generate_caption, fill_monthly_plan, suggest_visuals

# Caption pour une image existante
caption = generate_caption("instagram", "images/htt/post_001.jpg", "htt")

# Planning complet d'un mois
plan = fill_monthly_plan("htt", 2026, 8)  # août 2026

# Briefs visuels pour un graphiste
briefs = suggest_visuals("nexum", month=8, n=10)
```
Nécessite le secret GitHub `GOOGLE_API_KEY` (Google AI Studio, gratuit).

### Tester sans publier (dry run)
GitHub → Actions → Autopost → Run workflow → `dry_run: true`

### Voir les posts publiés
Ouvrir `published.json` dans le repo.

### Forcer une publication immédiate
Ajouter une ligne dans `posts.csv` avec la date/heure actuelle (±30 min) et pusher.

---

## Secrets GitHub à configurer

Settings → Secrets and variables → Actions → New repository secret

| Secret | Requis pour | Notes |
|--------|-------------|-------|
| `META_ACCESS_TOKEN` | Instagram | Token 60 jours, voir docs/SETUP_META.md |
| `IG_USER_ID` | Instagram | ID du compte pro Instagram |
| `META_APP_ID` | Instagram | App ID Meta |
| `META_APP_SECRET` | Instagram | App Secret Meta |
| `IMAGES_BASE_URL` | Instagram | `https://courtierleandro-jpg.github.io/autopost-assets` |
| `TIKTOK_CLIENT_KEY` | TikTok | Voir docs/SETUP_TIKTOK.md |
| `TIKTOK_CLIENT_SECRET` | TikTok | |
| `TIKTOK_ACCESS_TOKEN` | TikTok | Expire toutes les 24h (auto-refresh si refresh token présent) |
| `TIKTOK_REFRESH_TOKEN` | TikTok | Expire dans 1 an |
| `GOOGLE_API_KEY` | agent.py (IA) | Google AI Studio → gratuit |
| `DISCORD_WEBHOOK_URL` | Notifications | Optionnel |
| `GITHUB_PAT` | Auto-refresh tokens | Recommandé — fine-grained PAT secrets:write |

---

## En cas d'erreur

| Message | Cause | Solution |
|---------|-------|----------|
| `Token Meta expiré` | META_ACCESS_TOKEN > 60 jours | Mettre à jour le secret (ou attendre le refresh mensuel si GITHUB_PAT configuré) |
| `Token TikTok expiré` | TIKTOK_ACCESS_TOKEN périmé | Le système tente un refresh automatique si TIKTOK_REFRESH_TOKEN est présent |
| `Image introuvable` | Image absente de autopost-assets | Vérifier que le fichier existe dans autopost-assets avec le bon chemin |
| `Rate limit Meta` | Trop d'appels API | Attendre 1h, ça repart tout seul |
| `GOOGLE_API_KEY absent` | Secret manquant | Ajouter la clé dans les secrets GitHub |
