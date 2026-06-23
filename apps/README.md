# Projet Tourisme


**ExploreMboa** est une solution web développée avec Python/Django qui centralise et simplifie la réservation de services touristiques en connectant les voyageurs à un écosystème diversifié de prestataires (guides, hôtels, agences de location de véhicules et restaurants). La plateforme intègre un système d'authentification multi-rôles, un moteur de réservation unifié couvrant les visites guidées, l'hébergement, la location de véhicules et la restauration, ainsi qu'un système de paiement sécurisé avec gestion des commissions et des remboursements. Elle propose également un système d'évaluation et de notation pour garantir la qualité des services, un portefeuille électronique pour les utilisateurs, et des fonctionnalités avancées de signalement des zones à risque, le tout reposant sur une base de données PostgreSQL optimisée avec une architecture scalable déployable via Docker.

## Prérequis

- Python 3.8+
- pip
- virtualenv (recommandé)

## Installation

1. Cloner le dépôt :
```bash
mkdir no_de_votre_dossier
cd no_de votre_dossier
git clone <votre-repo>
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Modifier les valeurs dans .env selon vos besoins
```

5. Appliquer les migrations :
```bash
python manage.py migrate
```

6. Créer un superutilisateur :
```bash
python manage.py createsuperuser
```

7. Lancer le serveur de développement :
```bash
python manage.py runserver
```

## Structure du Projet

```
tourisme/
├── apps/               # Applications Django
├── config/             # Configuration du projet
├── static/            # Fichiers statiques
├── templates/         # Templates HTML
├── manage.py          # Script de gestion Django
└── requirements.txt   # Dépendances Python
```

## Développement

- Le code source est organisé dans le dossier `apps/`
- La configuration du projet est dans le dossier `config/`
- Les templates sont dans le dossier `templates/`
- Les fichiers statiques sont dans le dossier `static/`

## API REST

L'API REST est construite avec Django REST Framework. La documentation de l'API est disponible à l'URL suivante :
- `/api/docs/` - Documentation de l'API (Swagger/OpenAPI)

## Déploiement

Instructions pour le déploiement en production :

1. Configurer les variables d'environnement pour la production
2. Collecter les fichiers statiques :
```bash
python manage.py collectstatic
```
3. Configurer un serveur web (nginx, Apache) avec gunicorn

