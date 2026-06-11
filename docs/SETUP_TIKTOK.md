# Guide d'installation — TikTok Content Posting API

Ce guide te permet de connecter ton compte TikTok NEXUM Mindset à l'autopost.
Temps estimé : **30-45 minutes**.

---

## Contexte important

TikTok distingue deux modes de publication :

- **Mode INBOX (brouillon)** — par défaut tant que ton app n'est pas auditée par TikTok. Le post atterrit dans l'onglet "Brouillons" de ton app TikTok. Tu le valides en 1 tap avant publication. C'est le mode configuré par défaut.
- **Mode DIRECT_POST** — publication directe sans validation manuelle. Disponible après audit de l'app TikTok (processus de quelques semaines). Pour l'activer : mets le secret `TIKTOK_DIRECT_POST` à `true`.

---

## Étape 1 — Créer une application sur TikTok for Developers

1. Va sur **[developers.tiktok.com](https://developers.tiktok.com)**
2. Connecte-toi avec le compte TikTok NEXUM Mindset (ou un compte admin)
3. En haut à droite : **Mon espace** → **Applications**
4. Clique **Créer une application**
5. Remplis :
   - Nom de l'application : `NEXUM Autopost`
   - Plateforme : **Web**
   - URL du site web : `https://github.com/TON_USERNAME/autopost` (ou ton site)
   - Description : `Outil d'automatisation de publication de contenu`
6. Clique **Créer**

---

## Étape 2 — Activer le Content Posting API

Sur le tableau de bord de ton application :

1. Va dans **Produits** (menu gauche)
2. Cherche **Content Posting API** et clique **Ajouter**
3. Lis les conditions et accepte
4. Tu dois maintenant voir **Content Posting API** dans tes produits actifs

### Configurer les permissions OAuth :

Dans ton application → **Configuration OAuth** :

1. **Redirect URI** : ajoute `https://localhost/callback` (on en a besoin pour le premier OAuth)
2. **Scopes** (permissions) : active :
   - `user.info.basic`
   - `video.upload`
   - `video.publish` (si disponible)
3. Sauvegarde

### Récupérer tes identifiants d'application :

Dans **Détails de l'application** → **Identifiants** :
- Copie le **Client Key** (`TIKTOK_CLIENT_KEY`)
- Clique **Afficher** → copie le **Client Secret** (`TIKTOK_CLIENT_SECRET`)

---

## Étape 3 — Faire le premier OAuth (obtenir les tokens)

Cette étape est la seule "technique". Elle doit être faite une seule fois.

### 3a — Construire l'URL d'autorisation

Remplace les valeurs et ouvre cette URL dans ton navigateur **en étant connecté sur le compte TikTok NEXUM** :

```
https://www.tiktok.com/v2/auth/authorize/
  ?client_key=TON_CLIENT_KEY
  &response_type=code
  &scope=user.info.basic,video.upload,video.publish
  &redirect_uri=https://localhost/callback
  &state=autopost_init
```

⚠️ Colle tout sur une seule ligne (sans espaces) dans la barre d'adresse.

### 3b — Autoriser l'application

1. TikTok te demande d'autoriser `NEXUM Autopost` — clique **Autoriser**
2. Tu es redirigé vers `https://localhost/callback?code=XXXX&state=autopost_init`
3. La page va afficher une erreur (normal — localhost n'existe pas) — c'est OK
4. **Copie le code dans l'URL** : la valeur après `code=` et avant `&state`

Exemple : si l'URL est `https://localhost/callback?code=abc123xyz&state=...` → copie `abc123xyz`

### 3c — Échanger le code contre les tokens

Ouvre le terminal (ou PowerShell) et exécute cette commande en remplaçant les valeurs :

```bash
curl -X POST "https://open.tiktokapis.com/v2/oauth/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_key=TON_CLIENT_KEY&client_secret=TON_CLIENT_SECRET&code=LE_CODE_DU_3B&grant_type=authorization_code&redirect_uri=https://localhost/callback"
```

Tu reçois un JSON comme :
```json
{
  "data": {
    "access_token": "act.xxxxx...",
    "refresh_token": "rft.xxxxx...",
    "expires_in": 86400,
    "refresh_expires_in": 31536000,
    ...
  }
}
```

- Copie `access_token` → **TIKTOK_ACCESS_TOKEN**
- Copie `refresh_token` → **TIKTOK_REFRESH_TOKEN**

> Le `access_token` expire après **24 heures**. Le `refresh_token` est valide **1 an**. Le système renouvelle automatiquement l'access_token à chaque run si `TIKTOK_REFRESH_TOKEN` est présent.

---

## Étape 4 — Ajouter les secrets dans GitHub

Dans ton repo privé `autopost` :
1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** pour chaque valeur :

| Secret | Valeur | Obligatoire |
|--------|--------|-------------|
| `TIKTOK_CLIENT_KEY` | Client Key de l'app TikTok | Oui |
| `TIKTOK_CLIENT_SECRET` | Client Secret de l'app TikTok | Oui |
| `TIKTOK_ACCESS_TOKEN` | `access_token` du step 3c | Oui |
| `TIKTOK_REFRESH_TOKEN` | `refresh_token` du step 3c | Oui |
| `TIKTOK_DIRECT_POST` | `false` (par défaut) ou `true` après audit | Non |
| `TIKTOK_FORCE_VIDEO` | `false` (par défaut) | Non |

---

## Étape 5 — Comprendre le mode brouillon

Tant que ton app n'est pas auditée par TikTok (`TIKTOK_DIRECT_POST=false`) :

1. Le post est envoyé dans **Boîte de réception** → **Brouillons** de l'app TikTok
2. Tu reçois une notification push sur ton téléphone
3. Tu ouvres l'app TikTok → trouves le brouillon → tape **Publier**
4. C'est tout — 1 tap par post

---

## Étape 6 — Fallback image → vidéo

Si l'API Photo TikTok n'est pas disponible pour ton app (app non encore auditée), le système convertit automatiquement l'image en une vidéo de 5 secondes via ffmpeg.

Pour forcer ce mode dès le départ (évite les tentatives de photo qui échouent) :
- Mets le secret `TIKTOK_FORCE_VIDEO` à `true`

---

## Étape 7 — Demander l'audit TikTok (pour la publication directe)

Quand tu veux passer en publication 100% automatique :

1. Dans ton app TikTok → **Soumission** → **Demander l'accès avancé**
2. Remplis le formulaire : cas d'usage, exemple de contenu, etc.
3. Délai : 1-4 semaines
4. Une fois approuvé, mets `TIKTOK_DIRECT_POST` à `true` dans les secrets GitHub

---

## Vérification

Pour tester :
1. Ajoute un post TikTok dans `posts.csv` avec la date/heure actuelle
2. Déclenche le workflow **Autopost** manuellement depuis l'onglet Actions
3. Dans ~1 minute, ouvre l'app TikTok → vérifie que le brouillon est arrivé
