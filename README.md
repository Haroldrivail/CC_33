# 🗳️ Mini-Système de Vote Électronique avec RSA

> **Projet académique** - Conception d'un système de vote électronique sécurisé où les votes sont chiffrés avec RSA pour assurer la confidentialité et l'intégrité des données.

---

## 📋 Table des matières

1. [Problématique et Objectifs](#-problématique-et-objectifs)
2. [Architecture du Système](#-architecture-du-système)
3. [Installation et Démarrage](#-installation-et-démarrage)
4. [Structure du Projet](#-structure-du-projet)
5. [Fonctionnement du Chiffrement RSA](#-fonctionnement-du-chiffrement-rsa)
6. [Flux de Vote Sécurisé](#-flux-de-vote-sécurisé)
7. [Documentation Technique](#-documentation-technique)
8. [API REST](#-api-rest)
9. [Sécurité et Anonymat](#-sécurité-et-anonymat)
10. [Guide d'Utilisation](#-guide-dutilisation)

---

## 🎯 Problématique et Objectifs

### Problématique

> **Comment concevoir un système de vote électronique où les votes sont chiffrés avec RSA pour garantir la confidentialité et l'intégrité des suffrages ?**

### Objectifs

| Objectif            | Description                                              |
| ------------------- | -------------------------------------------------------- |
| **Confidentialité** | Les votes sont chiffrés et illisibles pendant le scrutin |
| **Intégrité**       | Impossible de modifier un vote après soumission          |
| **Anonymat**        | Aucun lien entre l'électeur et son bulletin              |
| **Unicité**         | Un électeur = Un vote (pas de double vote)               |
| **Vérifiabilité**   | Résultats déchiffrables uniquement par l'autorité        |

### Livrables

- ✅ Système fonctionnel complet
- ✅ Interface web (électeur + administration)
- ✅ Implémentation RSA native en Python
- ✅ Documentation technique complète

---

## 🏗️ Architecture du Système

### Technologies utilisées

| Composant           | Technologie                 | Justification              |
| ------------------- | --------------------------- | -------------------------- |
| **Frontend**        | HTML/CSS/JavaScript Vanilla | Léger, sans dépendances    |
| **Backend**         | Python `http.server` natif  | Pas de framework externe   |
| **Base de données** | SQLite                      | Portable, intégrée         |
| **Chiffrement**     | RSA implémenté manuellement | Compréhension pédagogique  |
| **Hachage**         | SHA-256                     | Sécurité des mots de passe |

### Schéma d'architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTÈME DE VOTE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         HTTP/JSON          ┌──────────────────────┐      │
│   │   FRONTEND   │ ◄────────────────────────► │      BACKEND         │      │
│   │              │                            │                      │      │
│   │ • index.html │    Clé publique RSA        │ • server.py          │      │
│   │ • vote.html  │ ◄─────────────────────     │ • rsa.py             │      │
│   │ • admin.html │                            │ • database.py        │      │
│   │ • app.js     │    Vote chiffré            │                      │      │
│   │              │ ─────────────────────►     │ ┌──────────────────┐ │      │
│   └──────────────┘                            │ │   vote_system.db │ │      │
│                                               │ │   (SQLite)       │ │      │
│                                               │ └──────────────────┘ │      │
│                                               └──────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation et Démarrage

### Prérequis

- **Python 3.10+** (ou version plus récente)

### Bibliothèques utilisées

| Bibliothèque   | Type            | Utilisation                 |
| -------------- | --------------- | --------------------------- |
| `sqlite3`      | Standard Python | Base de données             |
| `hashlib`      | Standard Python | Hachage SHA-256             |
| `json`         | Standard Python | Format des données API      |
| `http.server`  | Standard Python | Serveur web                 |
| `socketserver` | Standard Python | Gestion des connexions      |
| `random`       | Standard Python | Generation aleatoire        |
| `string`       | Standard Python | Caracteres pour les salts   |
| `base64`       | Standard Python | Encodage des votes chiffres |
| `math`         | Standard Python | Calculs mathematiques       |
| `sympy`        | **A installer** | Test de primalite pour RSA  |

### Installation

```bash
# 1. Telecharger ou cloner le projet
cd CC_33

# 2. Installer la seule dependance externe
pip install sympy

# 3. Lancer le serveur
python server.py
```

### Lancer le projet

```bash
# Demarrer le serveur (cree automatiquement la base de donnees)
python server.py

# Le serveur demarre sur http://localhost:8000
# Pour arreter le serveur : Ctrl + C
```

### Accès à l'application

| Page           | URL                                  | Description                |
| -------------- | ------------------------------------ | -------------------------- |
| Accueil        | http://localhost:8000                | Connexion/Inscription      |
| Vote           | http://localhost:8000/vote.html      | Interface de vote          |
| Résultats      | http://localhost:8000/resultats.html | Consultation des résultats |
| Administration | http://localhost:8000/admin.html     | Gestion des élections      |

### Identifiants par défaut

```
👤 Administrateur : admin / admin123
```

---

## 📁 Structure du Projet

```
CC_33/
│
├── 📄 server.py              # Serveur HTTP + routage API REST
├── 📄 rsa.py                 # Implémentation complète du chiffrement RSA
├── 📄 database.py            # Gestion SQLite + modèles de données
├── 📄 README.md              # Documentation (ce fichier)
├── 📦 vote_system.db         # Base de données (créée automatiquement)
│
└── 📂 static/                # Fichiers frontend
    ├── 📄 index.html         # Page de connexion/inscription
    ├── 📄 vote.html          # Interface de vote
    ├── 📄 resultats.html     # Affichage des résultats
    ├── 📄 admin.html         # Interface d'administration
    │
    ├── 📂 css/
    │   └── 📄 style.css      # Styles de l'application
    │
    └── 📂 js/
        └── 📄 app.js         # Logique client JavaScript
```

---

## 🔐 Fonctionnement du Chiffrement RSA

### Principe mathématique

Le RSA repose sur la **difficulté de factoriser** un grand nombre en ses facteurs premiers.

#### Génération des clés

```
1. Choisir deux nombres premiers distincts : p et q
2. Calculer le module : n = p × q
3. Calculer l'indicatrice d'Euler : φ(n) = (p-1)(q-1)
4. Choisir e tel que : 1 < e < φ(n) et pgcd(e, φ(n)) = 1
5. Calculer d (inverse modulaire) : e × d ≡ 1 (mod φ(n))

   ┌─────────────────────────────────────────┐
   │  Clé publique  : (n, e)  → Chiffrement  │
   │  Clé privée    : (n, d)  → Déchiffrement│
   └─────────────────────────────────────────┘
```

#### Chiffrement et Déchiffrement

| Opération         | Formule          | Qui peut le faire ?                |
| ----------------- | ---------------- | ---------------------------------- |
| **Chiffrement**   | $c = m^e \mod n$ | Tout le monde (clé publique)       |
| **Déchiffrement** | $m = c^d \mod n$ | Uniquement l'autorité (clé privée) |

### Implémentation dans `rsa.py`

| Fonction                                           | Rôle                                                      |
| -------------------------------------------------- | --------------------------------------------------------- |
| `generer_nombre_premier(min, max)`                 | Génère un nombre premier aléatoire avec test de primalité |
| `euclide_etendu(e, φ(n))`                          | Calcule l'inverse modulaire de `e` modulo `φ(n)`          |
| `generer_cles(taille_min, taille_max)`             | Génère une paire de clés RSA complète                     |
| `chiffrer_rsa(message, n, e)`                      | Chiffre un entier : $c = m^e \mod n$                      |
| `dechiffrer_rsa(chiffre, n, d)`                    | Déchiffre un entier : $m = c^d \mod n$                    |
| `generer_cles_rsa()`                               | Wrapper pour générer des clés au format dictionnaire      |
| `cles_vers_json()`                                 | Sérialise les clés en JSON pour transmission HTTP         |
| `json_vers_cle_publique()`                         | Désérialise une clé publique depuis JSON                  |
| `json_vers_cle_privee()`                           | Désérialise une clé privée depuis JSON                    |
| `chiffrer_vote(candidat_id, electeur_id, cle_pub)` | Chiffre un bulletin de vote complet                       |
| `dechiffrer_vote(vote_chiffre, cle_priv)`          | Déchiffre un bulletin pour le dépouillement               |
| `signer_message(message, cle_priv)`                | Signe un message pour garantir l'authenticité             |

### Exemple de flux RSA

```python
# 1. Génération des clés pour une élection
cle_publique, cle_privee = generer_cles_rsa(5000, 20000)
# cle_publique = {"n": 123456789, "e": 65537}
# cle_privee   = {"n": 123456789, "d": 987654321}

# 2. L'électeur chiffre son vote avec la clé publique
bulletin = chiffrer_vote(option_id=3, electeur_id="hash_jeton", cle_pub=cle_publique)
# bulletin = {"vote_chiffre": "base64...", "hash": "sha256..."}

# 3. Au dépouillement, l'admin déchiffre avec la clé privée
vote_clair = dechiffrer_vote(bulletin["vote_chiffre"], cle_privee)
# vote_clair = {"candidat_id": 3, "electeur_id": "hash_jeton"}
```

---

## 🔄 Flux de Vote Sécurisé

### Diagramme de séquence

```
  ÉLECTEUR                    SERVEUR                      BASE DE DONNÉES
     │                           │                               │
     │  1. Connexion             │                               │
     │ ─────────────────────────►│  Vérifier identifiants        │
     │                           │ ─────────────────────────────►│
     │                           │◄───────────────────────────── │
     │◄───────────────────────── │                               │
     │                           │                               │
     │  2. Demande de jeton      │                               │
     │ ─────────────────────────►│  Générer jeton anonyme        │
     │                           │  (hash déterministe)          │
     │                           │ ─────────────────────────────►│
     │  Jeton reçu               │                               │
     │◄───────────────────────── │                               │
     │                           │                               │
     │  3. Récupérer clé publique│                               │
     │ ─────────────────────────►│                               │
     │  Clé publique reçue       │                               │
     │◄───────────────────────── │                               │
     │                           │                               │
     │  4. CHIFFREMENT LOCAL     │                               │
     │  vote_chiffré = m^e mod n │                               │
     │                           │                               │
     │  5. Envoi vote chiffré    │                               │
     │ ─────────────────────────►│  Stocker bulletin anonyme     │
     │                           │ ─────────────────────────────►│
     │  Confirmation             │  Marquer jeton utilisé        │
     │◄───────────────────────── │ ─────────────────────────────►│
     │                           │                               │

     ═══════════════════════════════════════════════════════════════
                        APRÈS CLÔTURE DU VOTE
     ═══════════════════════════════════════════════════════════════

  ADMIN                       SERVEUR                      BASE DE DONNÉES
     │                           │                               │
     │  6. Lancer décompte       │                               │
     │ ─────────────────────────►│  Récupérer clé privée         │
     │                           │ ─────────────────────────────►│
     │                           │◄───────────────────────────── │
     │                           │                               │
     │                           │  Récupérer bulletins          │
     │                           │ ─────────────────────────────►│
     │                           │◄───────────────────────────── │
     │                           │                               │
     │                           │  DÉCHIFFREMENT                │
     │                           │  m = c^d mod n                │
     │                           │                               │
     │                           │  Comptabiliser résultats      │
     │                           │ ─────────────────────────────►│
     │  Résultats                │                               │
     │◄───────────────────────── │                               │
```

### Étapes détaillées

| Étape | Action                          | Garantie de sécurité         |
| ----- | ------------------------------- | ---------------------------- |
| 1     | Authentification de l'électeur  | Mot de passe hashé SHA-256   |
| 2     | Attribution d'un jeton anonyme  | Lien électeur-vote cassé     |
| 3     | Transmission de la clé publique | Seul le chiffrement possible |
| 4     | Chiffrement côté client         | Vote illisible en transit    |
| 5     | Stockage du bulletin chiffré    | Confidentialité en base      |
| 6     | Dépouillement avec clé privée   | Seul l'admin peut déchiffrer |

---

## 📚 Documentation Technique

### Modèle de données (SQLite)

```sql
┌─────────────────────────────────────────────────────────────────────┐
│                        SCHÉMA DE LA BASE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐         ┌──────────────┐         ┌─────────────┐ │
│  │  electeurs   │         │    votes     │         │   options   │ │
│  ├──────────────┤         ├──────────────┤         ├─────────────┤ │
│  │ id (PK)      │         │ id (PK)      │◄────────│ vote_id(FK) │ │
│  │ nom          │         │ titre        │         │ id (PK)     │ │
│  │ prenom       │         │ description  │         │ libelle     │ │
│  │ email        │         │ salt         │         │ description │ │
│  │ mot_de_passe │         │ cle_publique │         └─────────────┘ │
│  └──────────────┘         │ cle_privee   │                         │
│         │                 │ statut       │                         │
│         │                 └──────────────┘                         │
│         │                        │                                 │
│         │    ┌───────────────────┼───────────────────┐             │
│         ▼    ▼                   ▼                   ▼             │
│  ┌──────────────┐         ┌──────────────┐   ┌─────────────┐       │
│  │   jetons     │         │  bulletins   │   │  resultats  │       │
│  ├──────────────┤         ├──────────────┤   ├─────────────┤       │
│  │ id (PK)      │         │ id (PK)      │   │ id (PK)     │       │
│  │ vote_id (FK) │         │ vote_id (FK) │   │ vote_id(FK) │       │
│  │ jeton_hash   │◄────────│ jeton_hash   │   │ option_id   │       │
│  │ utilise      │         │ bulletin_    │   │ nombre_     │       │
│  └──────────────┘         │   chiffre    │   │   bulletins │       │
│                           └──────────────┘   └─────────────┘       │
│                                                                     │
│  ┌────────────────┐                                                 │
│  │ administrateurs│                                                 │
│  ├────────────────┤                                                 │
│  │ id (PK)        │                                                 │
│  │ username       │                                                 │
│  │ mot_de_passe   │                                                 │
│  └────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Tables et leurs rôles

| Table             | Rôle                       | Données sensibles      |
| ----------------- | -------------------------- | ---------------------- |
| `electeurs`       | Informations des votants   | Mot de passe (hashé)   |
| `votes`           | Campagnes électorales      | Clé privée RSA         |
| `options`         | Candidats/choix possibles  | -                      |
| `jetons`          | Tokens anonymes pour voter | Hash du jeton          |
| `bulletins`       | Votes chiffrés             | Bulletin (chiffré RSA) |
| `resultats`       | Décompte final             | -                      |
| `administrateurs` | Comptes admin              | Mot de passe (hashé)   |

### Système de jetons (anonymat)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MÉCANISME D'ANONYMAT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Génération du jeton (déterministe)                              │
│     ┌───────────────────────────────────────────────────────────┐   │
│     │  jeton = SHA256( salt_election + electeur_id + vote_id )  │   │
│     └───────────────────────────────────────────────────────────┘   │
│                                                                     │
│  2. Stockage du hash du jeton                                       │
│     ┌───────────────────────────────────────────────────────────┐   │
│     │  jeton_hash = SHA256( jeton )                             │   │
│     └───────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ⚠️  Le serveur ne stocke JAMAIS le jeton en clair !               │
│  ⚠️  Seul le hash est conservé → lien électeur-vote cassé          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 API REST

### Endpoints GET (lecture)

| Endpoint                          | Description                | Réponse                      |
| --------------------------------- | -------------------------- | ---------------------------- |
| `GET /api/options`                | Liste toutes les options   | `{options: [...]}`           |
| `GET /api/options/vote?vote_id=X` | Options d'un vote          | `{options: [...]}`           |
| `GET /api/electeurs`              | Liste des électeurs        | `{electeurs: [...]}`         |
| `GET /api/votes`                  | Liste des campagnes        | `{votes: [...]}`             |
| `GET /api/vote/actif`             | Vote en cours              | `{vote: {...}}`              |
| `GET /api/statistiques`           | Stats globales             | `{statistiques: {...}}`      |
| `GET /api/resultats`              | Résultats du dépouillement | `{resultats: [...]}`         |
| `GET /api/bulletins`              | Bulletins (chiffrés)       | `{bulletins: [...]}`         |
| `GET /api/bulletins/count`        | Nombre de bulletins        | `{count: N}`                 |
| `GET /api/generer-cles`           | Génère une paire RSA       | `{cle_publique, cle_privee}` |

### Endpoints POST (écriture)

| Endpoint                          | Payload                              | Description               |
| --------------------------------- | ------------------------------------ | ------------------------- |
| `POST /api/auth/electeur`         | `{email, mot_de_passe}`              | Connexion électeur        |
| `POST /api/auth/admin`            | `{username, mot_de_passe}`           | Connexion admin           |
| `POST /api/electeurs/inscription` | `{nom, prenom, email, mot_de_passe}` | Inscription               |
| `POST /api/jeton`                 | `{electeur_id, vote_id}`             | Demander un jeton         |
| `POST /api/voter`                 | `{jeton, option_id}`                 | Soumettre un vote chiffré |
| `POST /api/votes`                 | `{titre, description}`               | Créer une campagne        |
| `POST /api/votes/statut`          | `{id, statut}`                       | Changer le statut         |
| `POST /api/options`               | `{vote_id, libelle, description}`    | Ajouter une option        |
| `POST /api/options/supprimer`     | `{id}`                               | Supprimer une option      |
| `POST /api/decompte`              | `{vote_id}`                          | Lancer le dépouillement   |

### Exemple d'appel API

```javascript
// Voter (côté client)
const response = await fetch("/api/voter", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    jeton: "abc123...",
    option_id: 2,
  }),
});
const result = await response.json();
// { success: true, bulletin_id: 42 }
```

---

## 🛡️ Sécurité et Anonymat

### Garanties de sécurité

| Propriété            | Mécanisme                     | Protection contre          |
| -------------------- | ----------------------------- | -------------------------- |
| **Confidentialité**  | Chiffrement RSA des bulletins | Écoute du trafic, accès DB |
| **Intégrité**        | Hash SHA-256                  | Modification des votes     |
| **Anonymat**         | Système de jetons hashés      | Traçabilité des électeurs  |
| **Unicité**          | Jeton à usage unique          | Double vote                |
| **Authentification** | Mots de passe hashés          | Usurpation d'identité      |

### Points de sécurité implémentés

```
✅ Mots de passe jamais stockés en clair (SHA-256)
✅ Votes chiffrés avec RSA avant envoi
✅ Clé privée stockée uniquement côté serveur
✅ Jeton anonyme = rupture du lien électeur-vote
✅ Un jeton = un seul vote possible
✅ Bulletins illisibles sans la clé privée
✅ Dépouillement uniquement par l'administrateur
```

### Limites connues

```
⚠️  Pas de chiffrement HTTPS (environnement de développement)
⚠️  Taille des clés RSA limitée pour les performances
⚠️  Pas d'audit trail cryptographique (blockchain)
⚠️  Pas de multi-factor authentication
```

---

## 📖 Guide d'Utilisation

### Pour les électeurs

```
1. 📝 S'inscrire sur la page d'accueil
   └── Renseigner : nom, prénom, email, mot de passe

2. 🔑 Se connecter avec ses identifiants

3. 🗳️ Accéder à la page de vote
   └── Le système génère automatiquement un jeton anonyme

4. ✅ Sélectionner un candidat et valider
   └── Le vote est chiffré avant envoi

5. 📊 Consulter les résultats (après clôture)
```

### Pour les administrateurs

```
1. 🔐 Se connecter sur /admin.html (admin / admin123)

2. 📋 Créer une nouvelle campagne de vote
   └── Titre + Description

3. 👥 Ajouter les options/candidats

4. ▶️  Activer le vote
   └── Les électeurs peuvent désormais voter

5. ⏹️  Terminer le vote
   └── Bloque les nouveaux votes

6. 🔓 Lancer le dépouillement
   └── Déchiffre les bulletins avec la clé privée
   └── Calcule et affiche les résultats
```

### Cycle de vie d'une élection

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  en_attente  │ ──► │    active    │ ──► │   terminee   │ ──► │  dépouillée  │
│              │     │              │     │              │     │              │
│ Config.      │     │ Votes        │     │ Votes        │     │ Résultats    │
│ Options      │     │ acceptés     │     │ bloqués      │     │ publiés      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 🧪 Tests et Validation

### Tester le chiffrement RSA

```bash
python rsa.py
```

Ce script exécute des tests automatiques :

- Génération de clés
- Chiffrement/déchiffrement d'un message
- Vérification de l'intégrité

### Tester le système complet

1. Lancer le serveur : `python server.py`
2. Créer une élection dans l'admin
3. Ajouter des options
4. Activer le vote
5. S'inscrire comme électeur et voter
6. Terminer et dépouiller

---

## 📝 Crédits et Licence

**Projet académique** réalisé dans le cadre d'un exercice sur la cryptographie appliquée.

| Élément    | Détail                     |
| ---------- | -------------------------- |
| Langage    | Python 3.10+               |
| Dépendance | sympy (tests de primalité) |
| Licence    | Éducative                  |

---

## 📚 Références

- [RSA (cryptosystème) - Wikipedia](https://fr.wikipedia.org/wiki/Chiffrement_RSA)
- [Algorithme d'Euclide étendu](https://fr.wikipedia.org/wiki/Algorithme_d%27Euclide_%C3%A9tendu)
- [Fonction indicatrice d'Euler](https://fr.wikipedia.org/wiki/Indicatrice_d%27Euler)
