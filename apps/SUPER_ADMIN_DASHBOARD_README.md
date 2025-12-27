# Dashboard Super Administrateur

## Description

Le Dashboard Super Administrateur est une interface moderne et attrayante qui permet au super utilisateur de :

1. **Voir les statistiques globales** de la plateforme
2. **Gérer les commissions** perçues sur les transactions
3. **Approuver/rejeter** les business locations
4. **Visualiser les données** avec des graphiques interactifs

## Fonctionnalités

### 📊 Vue d'ensemble
- **Statistiques en temps réel** : nombre de business locations, utilisateurs, approbations en attente
- **Graphiques interactifs** : activité des 7 derniers jours, répartition par type de business
- **Transactions récentes** : historique des dernières transactions
- **Commissions du mois** : calcul automatique des commissions (5% sur toutes les transactions)

### ✅ Gestion des approbations
- **Liste des business locations** en attente d'approbation
- **Approbation en un clic** avec confirmation
- **Rejet avec raison** pour traçabilité
- **Interface intuitive** avec cartes modernes

### 💰 Wallet & Commissions
- **Solde total** du wallet super admin
- **Historique des commissions** avec détails
- **Statistiques des commissions** (totale, mensuelle)
- **Fonction de retrait** (à implémenter selon vos besoins)

## Installation et Configuration

### 1. Vérifier les URLs
Les URLs sont automatiquement configurées dans `apps/business/urls.py` :
```python
path('super-admin/', include('apps.business.views.admin.super_admin_urls')),
```

### 2. Créer un super utilisateur
```bash
python manage.py createsuperuser
```

### 3. Tester le dashboard
Exécutez le script de test :
```bash
python test_super_admin.py
```

### 4. Accéder au dashboard
- URL : `http://127.0.0.1:8000/business/super-admin/dashboard/`
- Ou via le menu utilisateur (icône couronne) pour les super utilisateurs

## Structure des fichiers

```
apps/business/
├── views/
│   └── admin/
│       ├── __init__.py
│       ├── admin.py              # Vues du super admin
│       ├── urls.py               # URLs admin existantes
│       └── super_admin_urls.py   # URLs du super admin
├── templates/
│   └── business/
│       └── admin/
│           ├── super_admin_dashboard.html    # Dashboard principal
│           ├── super_admin_wallet.html       # Gestion du wallet
│           └── business_approval_list.html   # Liste des approbations
```

## Sécurité

- **Accès restreint** : Seuls les super utilisateurs (`is_superuser=True`) peuvent accéder
- **Décorateurs de sécurité** : `@login_required` et `@user_passes_test(is_superuser)`
- **Protection CSRF** : Tous les formulaires incluent le token CSRF
- **Validation des données** : Vérification des permissions avant chaque action

## Personnalisation

### Modifier le taux de commission
Dans `apps/business/views/admin.py`, ligne 47 :
```python
commission_rate = 0.05  # 5% - modifiez selon vos besoins
```

### Ajouter de nouveaux graphiques
Dans la fonction `get_chart_data()` :
```python
def get_chart_data():
    # Ajoutez vos nouvelles données ici
    return {
        'dates': dates,
        'business_counts': business_counts,
        'transaction_amounts': transaction_amounts,
        'votre_nouvelle_metrique': nouvelle_donnees,
    }
```

### Modifier le design
Les styles CSS sont dans les templates avec des variables CSS personnalisées :
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #48bb78;
    --warning-color: #ed8936;
    --danger-color: #f56565;
}
```

## API Endpoints

### Statistiques en temps réel
- **URL** : `/business/super-admin/api/stats/`
- **Méthode** : GET
- **Réponse** : JSON avec les statistiques actuelles

### Approuver un business
- **URL** : `/business/super-admin/approve/{id}/`
- **Méthode** : POST
- **Réponse** : JSON avec `{"success": true}`

### Rejeter un business
- **URL** : `/business/super-admin/reject/{id}/`
- **Méthode** : POST
- **Paramètres** : `reason` (raison du rejet)
- **Réponse** : JSON avec `{"success": true}`

## Fonctionnalités avancées

### Animations et transitions
- **Fade-in** : Apparition progressive des éléments
- **Slide-in** : Glissement des cartes d'approbation
- **Hover effects** : Effets au survol des cartes
- **Pulse** : Animation pour les notifications

### Graphiques interactifs
- **Chart.js** : Graphiques en ligne et en secteurs
- **Données en temps réel** : Mise à jour automatique toutes les 30 secondes
- **Responsive** : Adaptation automatique à la taille d'écran

### Notifications
- **Messages de succès** : Confirmation des actions
- **Messages d'erreur** : Gestion des erreurs
- **Badges** : Indicateurs visuels pour les approbations en attente

## Support et Maintenance

### Logs
Toutes les actions sont tracées dans les messages Django :
```python
messages.success(request, f'Business location "{business_location.name}" approuvé avec succès!')
```

### Debug
Pour activer le mode debug, ajoutez dans les vues :
```python
print(f"[DEBUG] Données: {data}")
```

### Extensions futures
- **Système de notifications** par email
- **Rapports PDF** des statistiques
- **Export des données** en CSV/Excel
- **Dashboard mobile** optimisé
- **Intégration avec des APIs** externes

## Dépannage

### Erreur 404
- Vérifiez que les URLs sont bien incluses dans `urls.py`
- Vérifiez que le serveur Django est démarré

### Erreur de permission
- Vérifiez que l'utilisateur a `is_superuser=True`
- Vérifiez que l'utilisateur est connecté

### Graphiques ne s'affichent pas
- Vérifiez que Chart.js est chargé
- Vérifiez la console JavaScript pour les erreurs
- Vérifiez que les données sont bien passées au template

### Transactions ne s'affichent pas
- Vérifiez que le modèle `UserTransaction` est bien importé
- Vérifiez que les transactions existent en base de données
- Vérifiez les permissions d'accès aux modèles 