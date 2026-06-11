# Guide d'utilisation quotidienne

---

## Publier un post : 4 étapes

### 1. Préparer l'image

- **Instagram HTT** : image carrée ou portrait (1080×1080 ou 1080×1350), format JPG/PNG, DA HTT
- **TikTok NEXUM** : format portrait (1080×1920 recommandé), format JPG/PNG, DA NEXUM

### 2. Déposer l'image au bon endroit

**Dans le repo `autopost-assets` (public)** :
- Visuels HTT → dossier `htt/`
- Visuels NEXUM → dossier `nexum/`

Nomme tes fichiers de façon claire : `post_001.jpg`, `post_002.jpg`, etc.

```
autopost-assets/
├── htt/
│   ├── post_001.jpg
│   └── post_002.jpg
└── nexum/
    ├── post_001.jpg
    └── post_002.jpg
```

> ⚠️ Les images du repo `autopost-assets` sont **publiques**. C'est nécessaire pour que l'API Meta puisse les télécharger.

### 3. Ajouter la ligne dans posts.csv

Ouvre `posts.csv` dans le repo `autopost` et ajoute une ligne :

```csv
date;heure;plateforme;image;caption;statut
2026-06-20;18:00;instagram;htt/post_001.jpg;"Votre site web mérite mieux 🚀 #artisans #webdesign";planifie
2026-06-20;19:30;tiktok;nexum/post_001.jpg;"La discipline bat le talent. #mindset #trading";planifie
```

**Règles importantes :**
- Date : format `YYYY-MM-DD` (ex: `2026-06-20`)
- Heure : format `HH:MM` en **heure de Paris** (ex: `18:00`)
- Plateforme : `instagram` ou `tiktok` (minuscules)
- Image : chemin depuis le dossier `images/` (ex: `htt/post_001.jpg`)
- Caption : entre guillemets si elle contient des virgules ou des `#`
- Statut : `planifie` pour les posts à venir

### 4. Pusher sur GitHub

Dès que tu pousses `posts.csv`, le workflow de **validation** se déclenche automatiquement. S'il y a une erreur (image manquante, format de date incorrect, etc.), GitHub te l'indique par email.

Si la validation passe → le post partira automatiquement à l'heure prévue (±15 min max).

---

## Comment vérifier que tout tourne

### Voir les publications récentes

Ouvre `published.json` dans le repo `autopost`. Chaque post publié y est enregistré :

```json
{
  "2026-06-20_18:00_instagram_htt/post_001.jpg": {
    "post_id": "17923456789",
    "published_at": "2026-06-20T18:01:34+02:00",
    "platform": "instagram",
    "image": "htt/post_001.jpg"
  }
}
```

### Voir les logs des workflows

1. Va sur GitHub → ton repo `autopost`
2. Clique sur l'onglet **Actions**
3. Clique sur un run récent **Autopost**
4. Ouvre le job **publish** → **Publier les posts dus**
5. Tu vois tous les logs : posts publiés, erreurs, etc.

### Recevoir les notifications Discord

Si tu as configuré `DISCORD_WEBHOOK_URL`, tu reçois une alerte en cas d'échec directement dans ton salon Discord.

---

## Que faire si un post échoue

Le système **réessaie automatiquement** au prochain run (toutes les 15 min). Un post échoué n'est **jamais** marqué comme publié — il sera retenté jusqu'à ce qu'il passe.

Si un post échoue plusieurs fois :

1. Lis le message d'erreur dans les logs Actions ou dans Discord
2. Causes courantes :

   | Erreur | Solution |
   |--------|----------|
   | `Token Meta expiré` | Va dans GitHub → Settings → Secrets → mets à jour `META_ACCESS_TOKEN` |
   | `Token TikTok expiré` | Idem pour `TIKTOK_ACCESS_TOKEN` et `TIKTOK_REFRESH_TOKEN` |
   | `Image introuvable` | Vérifie que l'image est bien dans `autopost-assets` et que le chemin dans le CSV est correct |
   | `Rate limit Meta` | Attends 1h — Meta limite le nombre d'appels par heure |
   | `ffmpeg échec` | L'image est peut-être corrompue ou dans un format non supporté |

3. Une fois corrigé, le post repartira au prochain run automatique, ou tu peux forcer en allant dans Actions → **Run workflow**

---

## Planifier 1 an de posts en avance

Tu peux remplir `posts.csv` avec autant de lignes que tu veux — même un an complet. Le système lit la date/heure à chaque run et ne publie que ce qui est dû.

Exemple pour planifier toute une semaine :

```csv
date;heure;plateforme;image;caption;statut
2026-06-16;18:00;instagram;htt/post_001.jpg;"Post lundi HTT";planifie
2026-06-17;18:00;instagram;htt/post_002.jpg;"Post mardi HTT";planifie
2026-06-18;18:00;instagram;htt/post_003.jpg;"Post mercredi HTT";planifie
2026-06-16;19:30;tiktok;nexum/post_001.jpg;"Post lundi NEXUM";planifie
2026-06-17;19:30;tiktok;nexum/post_002.jpg;"Post mardi NEXUM";planifie
```

---

## Tester sans publier (dry run)

1. Onglet **Actions** → **Autopost** → **Run workflow**
2. Mets `dry_run: true`
3. Clique **Run workflow**
4. Les logs te montrent ce qui **aurait été** publié sans rien publier réellement

---

## Modifier ou annuler un post planifié

- **Modifier** : édite la ligne dans `posts.csv` et push (tant que le post n'est pas encore publié)
- **Annuler** : change le statut de `planifie` à `ignore` dans le CSV et push

---

## Ajouter une nouvelle plateforme (futur)

Pour brancher une nouvelle plateforme (LinkedIn, Twitter, etc.) :
1. Crée `src/linkedin.py` sur le modèle de `instagram.py`
2. Ajoute le cas dans `src/main.py` (`elif platform == "linkedin":`)
3. Ajoute les secrets correspondants dans GitHub
