# 📘 DevBook – Plateforme touristique camerounaise (Django)

## 🧭 Table des matières

1. [Environnement et configuration initiale](#1-environnement-et-configuration-initiale)
2. [Intégration des fichiers statiques](#2-intégration-des-fichiers-statiques)
3. [Apps Django](#3-apps-django)
4. [Leaflet pour la cartographie](#4-leaflet-pour-la-cartographie)
5. [Wallet & mock de paiement](#5-wallet--mock-de-paiement)
6. [Checklist générale & bonnes pratiques](#6-checklist-générale--bonnes-pratiques)

---

## 1. Environnement et configuration initiale

### Arborescence recommandée

```plaintext
tourisme/
├── config/
│   ├── settings.py
│   └── urls.py
├── apps/
│   ├── users/
│   ├── guides/
│   ├── business/
│   ├── tours/
│   ├── core/
│   ├── rooms/
│   ├── vehicles/
│   ├── orders/
│   ├── reviews/
│   └── wallets/
├── static/
│   └── vendor/
│       ├── bootstrap/
│       └── fontawesome/
├── templates/
├── manage.py
├── requirements.txt
└── .env.example
```

### Fichiers clés

* `requirements.txt` : dépendances (`Django`, `djangorestframework`, `django-leaflet`, etc.)
* `config/settings.py` : configuration SQLite, apps, statiques, médias, DRF, Leaflet
* `config/urls.py` : point d’entrée global, inclut les URLs des apps
* `manage.py` : script de gestion
* `.env.example` : variables d’environnement

---

## 2. Intégration des fichiers statiques

### Structure

```plaintext
static/vendor/
├── bootstrap/
└── fontawesome/
```

Place ici les fichiers CSS/JS téléchargés depuis les sources officielles de Bootstrap et FontAwesome.

### `templates/base.html`

* Intégration de Bootstrap & FontAwesome via `{% load static %}` et `{% static %}`
* Blocs structurés :

  * `{% block title %}` (titre de page)
  * `{% block content %}` (contenu principal)
  * `{% block scripts %}` (JS supplémentaires)
* Navbar responsive, footer minimal
* Lazy loading et fallback pour les images (`onerror`)

---

## 3. Apps Django

Chaque app est organisée de manière homogène :

```plaintext
apps/<app_name>/
├── admin.py          # Enregistrement des modèles dans l’admin
├── apps.py           # Configuration de l’app
├── __init__.py
├── models/
│   ├── __init__.py   # Import central des modèles
│   └── *.py          # Fichiers de modèles
├── services/
│   ├── __init__.py   # Logique métier réutilisable
│   └── *.py          # Services spécifiques
├── views/
│   ├── __init__.py
│   └── web.py        # Vues web (HTML)
├── forms.py          # Formulaires Bootstrap
├── serializers.py    # Pour API DRF si besoin
├── urls.py           # Routes propres à l’app
├── templates/
│   └── <app_name>/   # Templates HTML de l’app
├── migrations/
│   └── __init__.py
└── tests/            # Tests d'intégration et fonctionnels (pas d’unit tests)
    └── __init__.py
```

> **Remarque** : Nous n’incluons pas de tests unitaires isolés (`tests.py`), mais plutôt un dossier `tests/` pour les tests d’intégration et comportementaux.

### Relations entre modèles

* **OneToOneField** : pour étendre un modèle unique (ex. profil utilisateur)
* **ForeignKey** : pour les liaisons un-à-plusieurs (ex. réservation → tour)
* **ManyToManyField** : pour les associations multiples (ex. guide ↔ langues)

---

### 3.1 users

* **Modèle** : custom `User` basé sur `AbstractUser`
* **Fonctionnalités** : inscription, connexion, gestion des rôles (`guide`, `client`, `business`)
* **Fichiers** : `models/user.py`, `forms.py`, `admin.py`, `urls.py`, `views/web.py`, templates `users/*.html`

### 3.2 guides

* **Modèles** : `GuideProfile` (`OneToOneField` → `User`), `Language`, `Specialization`
* **Relations** : `ManyToManyField` → `Language`, `Specialization`
* **Fichiers** : `models/profile.py`, `services/guide_services.py`, etc.

### 3.3 business

* **Modèles** : `Business`, `Address`, `BusinessStatus`
* **Fonctionnalités** : profil entreprise, géolocalisation

### 3.4 tours

* **Modèles** : `Tour`, `TourImage`, `TourSchedule`
* **Fonctionnalités** : packages, galeries, calendrier

### 3.5 bookings

* **Modèles** : `Booking` (statuts : `draft`, `confirmed`, `canceled`)
* **Flux** : création, confirmation, annulation

### 3.6 rooms

* **Modèles** : `AccommodationType`, `Accommodation`, `Room`
* **Fonctionnalités** : disponibilité, réservations d’hébergement

### 3.7 vehicles

* **Modèles** : `VehicleCategory`, `Vehicle`, `RentalContract`
* **Fonctionnalités** : location de véhicules, contrats

### 3.8 orders

* **Modèles** : `Order`, `OrderItem`
* **Fonctionnalités** : commandes de restaurant, historique

### 3.9 reviews

* **Modèles** : `Review` générique lié à tout contenu via `GenericForeignKey`
* **Statuts** : `pending`, `approved`, `rejected`

### 3.10 wallets

* **Modèles** : `Wallet`, `Transaction`
* **Fonctionnalités** : solde, historique, recharge

---

## 4. Leaflet pour la cartographie

1. Ajouter `django-leaflet` à `INSTALLED_APPS` dans `config/settings.py`
2. Créer `templates/includes/leaflet_map.html` :

   * Inclusions CSS/JS de Leaflet
   * `<div id="map"></div>` configuré via JS
3. Dans les templates concernées, inclure :

   ```django
   {% include "includes/leaflet_map.html" %}
   ```

Lien utile : [https://django-leaflet.readthedocs.io](https://django-leaflet.readthedocs.io)

---

## 5. Wallet & mock de paiement

### Structure API

```plaintext
apps/wallets/api/
├── __init__.py
├── serializers.py
├── views.py      # endpoints `initiate/`, `confirm/`
└── urls.py
```

* `initiate/` démarre une simulation de paiement
* `confirm/` valide la transaction (simulateur interne)

### Services

* `apps/wallets/services/payment_mock.py` : logique simulée (e.g. `sleep(MOCK_PAYMENT_DELAY)`)

### Formulaire de recharge

* `templates/wallets/recharge.html` : montant, méthode mobile money (MTN, Orange)
* Flux : soumission → appel API interne → mise à jour du solde

---

## 6. Checklist générale & bonnes pratiques

### Fichiers à inclure

* `.gitignore` : ignorer `db.sqlite3`, `.env`, `__pycache__`, `/media/`, `/static/`
* `.env.example` : variables d’environnement
* `CONTRIBUTING.md` : processus de contribution, style guide

### Migrations

* Chaque app dispose d’un dossier `migrations/`
* Ne pas modifier manuellement les fichiers de migration générés
* Nommer clairement (`0002_add_field_wallet.py`)

---

## 📦 Bonus : seed de la base de données

Créer une commande custom `manage.py seed_data` ou un script `seed.py` pour :

* Injecter des guides camerounais avec langues locales
* Créer des tours dans différentes régions (Littoral, Nord, Ouest)
* Ajouter des hébergements typiques, véhicules et menus locaux

---

Fin du DevBook ✅