# Guide d'installation — Instagram / Meta Graph API

Ce guide te permet de connecter ton compte Instagram HTT Digital à l'autopost.
Temps estimé : **30-40 minutes**.

---

## Étape 1 — Convertir le compte Instagram en compte Professionnel

Si ce n'est pas déjà fait :

1. Ouvre l'app Instagram sur ton téléphone
2. Va sur ton profil HTT Digital → **☰ (3 lignes en haut à droite)**
3. **Paramètres et confidentialité**
4. **Type de compte et outils** → **Passer à un compte professionnel**
5. Choisis **Entreprise** (pas Créateur)
6. Catégorie : **Services aux entreprises** ou **Marketing et publicité**
7. Confirme ton email/téléphone

---

## Étape 2 — Créer une Page Facebook et la lier à Instagram

L'API Meta exige une Page Facebook liée. Si tu n'en as pas :

1. Sur Facebook (bureau ou app) → clic sur ton profil en haut à droite
2. **Créer une Page**
3. Nom : **HTT Digital** — Catégorie : **Services aux entreprises**
4. Crée la page (pas besoin de la remplir complètement)

Lier la page à Instagram :
1. Sur Instagram : **Paramètres** → **Compte** → **Page Facebook liée**
2. Sélectionne la page HTT Digital que tu viens de créer
3. Confirme

---

## Étape 3 — Créer l'application Meta

1. Va sur **[developers.facebook.com](https://developers.facebook.com)**
2. Connecte-toi avec ton compte Facebook perso (celui qui gère HTT Digital)
3. Clique sur **Mes applications** (en haut à droite)
4. Clique sur **Créer une application**
5. Type d'utilisation : **Autre** → Suivant
6. Type d'app : **Entreprise** → Suivant
7. Remplis :
   - Nom de l'application : `HTT Autopost`
   - Email de contact : ton email
   - Compte Business (optionnel, tu peux ignorer)
8. Clique **Créer une application** et résous le captcha si demandé

---

## Étape 4 — Activer Instagram Graph API + permissions

Sur le tableau de bord de ton application :

1. Dans la colonne gauche : **Tableau de bord de l'application**
2. Trouve **Instagram Graph API** et clique **Configurer**
3. Si ce n'est pas là, va dans **Ajouter un produit** → cherche **Instagram** → **Configurer**

Permissions nécessaires :
1. Va dans **Paramètres de l'application → Avancé**
2. Puis dans le menu gauche : **Instagram Graph API → Autorisations et fonctionnalités**
3. Demande les permissions suivantes (clique **Demander un accès avancé** sur chacune) :
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_show_list`

> ⚠️ Pour un usage **personnel** (ton propre compte), tu n'as PAS besoin de passer la révision Meta. Les tokens générés fonctionneront directement pour les comptes liés à l'application.

---

## Étape 5 — Récupérer le token d'accès long-lived (60 jours)

### 5a — Token court (valide 1h)

1. Dans ton app Meta, va dans **Outils → Explorateur de l'API Graph** (menu gauche ou [ici](https://developers.facebook.com/tools/explorer/))
2. En haut à droite : sélectionne ton application `HTT Autopost`
3. Coche **Générer un token d'accès utilisateur**
4. Dans la fenêtre qui s'ouvre, sélectionne les pages de ton compte et accorde les permissions :
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_show_list`
5. Clique **Générer un token d'accès** → autorise → copie le token (commence par `EAA...`)

### 5b — Convertir en token long-lived (60 jours)

Ouvre un onglet et copie cette URL en remplaçant les valeurs :

```
https://graph.facebook.com/v21.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=TON_APP_ID
  &client_secret=TON_APP_SECRET
  &fb_exchange_token=TOKEN_COURT_DU_5A
```

Pour trouver `APP_ID` et `APP_SECRET` :
- Dans ton app Meta → **Paramètres → Basique**
- `APP_ID` = le grand numéro en haut
- `APP_SECRET` = clique sur **Afficher** à côté de "Clé secrète de l'application"

Colle l'URL complète dans ton navigateur → tu obtiens un JSON avec le token long-lived (60 jours). Copie la valeur `access_token`.

---

## Étape 6 — Récupérer ton IG User ID

Dans l'Explorateur de l'API Graph, avec ton token long-lived :

1. Champ de requête : `me/accounts`
2. Clique **Soumettre**
3. Dans les résultats, cherche la page HTT Digital → copie son `id`
4. Maintenant requête : `ID_PAGE_ICI?fields=instagram_business_account`
5. Copie la valeur `id` dans `instagram_business_account` → **c'est ton IG_USER_ID**

---

## Étape 7 — Créer le repo d'assets publics (autopost-assets)

L'API Instagram exige une URL publique pour les images. Solution gratuite : un repo GitHub public.

1. Sur GitHub, clique **New repository**
2. Nom : `autopost-assets`
3. Visibilité : **Public** ⚠️ (les images seront accessibles publiquement — c'est voulu)
4. Initialise avec un README
5. Crée les dossiers `htt/` et `nexum/` (crée un fichier `.gitkeep` dans chacun)
6. Dans les **Settings** du repo → **Pages** → Source : `Deploy from a branch` → Branch : `main` → `/` (root)
7. Attends 1-2 min → ton URL de base sera : `https://TON_USERNAME.github.io/autopost-assets/`

> Note : les images seront publiques AVANT la date de publication. Elles sont destinées à être publiées de toute façon, mais si ça te pose problème, contacte-moi pour une solution alternative.

Ajoute `IMAGES_BASE_URL` dans les secrets GitHub avec cette valeur :
`https://TON_USERNAME.github.io/autopost-assets`

---

## Étape 8 — Ajouter les secrets dans GitHub

Dans ton repo privé `autopost` :
1. **Settings** (onglet en haut)
2. **Secrets and variables** → **Actions**
3. Clique **New repository secret** pour chaque valeur :

| Secret | Valeur |
|--------|--------|
| `META_ACCESS_TOKEN` | Token long-lived du step 5b |
| `IG_USER_ID` | ID Instagram du step 6 |
| `META_APP_ID` | App ID de ton app Meta |
| `META_APP_SECRET` | App Secret de ton app Meta |
| `IMAGES_BASE_URL` | `https://TON_USERNAME.github.io/autopost-assets` |

---

## Renouvellement du token (tous les 50 jours)

Le token long-lived expire après 60 jours. **Le workflow `refresh_meta_token.yml` le renouvelle automatiquement le 1er de chaque mois** si tu as configuré `GITHUB_PAT`.

### Créer le GITHUB_PAT (optionnel mais recommandé) :
1. GitHub → ton profil → **Settings**
2. **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
3. **Generate new token**
4. Nom : `autopost-secrets-writer`
5. Repository access : **Only select repositories** → sélectionne `autopost`
6. Permissions : **Repository permissions** → **Secrets** → **Read and write**
7. Génère et ajoute le token comme secret `GITHUB_PAT`

Sans `GITHUB_PAT` : tu recevras une notif Discord tous les mois te rappelant de mettre à jour le token manuellement.

---

## Vérification finale

Pour tester sans publier :
1. Va sur ton repo → onglet **Actions**
2. Clique **Autopost** → **Run workflow** → `dry_run: true` → **Run**
3. Vérifie les logs — tu dois voir "Aucun post à publier" ou les posts simulés

Pour un vrai test :
1. Ajoute une ligne dans `posts.csv` avec la date/heure actuelle
2. Déclenche le workflow manuellement (sans dry_run)
3. Vérifie sur Instagram dans 1-2 minutes
