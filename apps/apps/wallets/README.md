# App Wallets

Cette application gère les wallets (portefeuilles) et les transactions pour les utilisateurs et les entreprises.

## Modèles

### Wallets

- **UserWallet** : Wallet pour les utilisateurs individuels
- **BusinessWallet** : Wallet pour les entreprises

### Transactions

- **UserTransaction** : Transactions pour les wallets utilisateur
- **BusinessTransaction** : Transactions pour les wallets entreprise

## Fonctionnalités

### Opérations de base
- **Dépôts** : Ajouter de l'argent au wallet
- **Retraits** : Retirer de l'argent du wallet
- **Transferts** : Transférer de l'argent entre wallets
- **Paiements** : Effectuer des paiements

### Types de transactions
- `DEPOSIT` : Dépôt
- `WITHDRAWAL` : Retrait
- `TRANSFER` : Transfert
- `PAYMENT` : Paiement
- `HOLD` : Mise en attente
- `REFUND` : Remboursement

### Statuts de transaction
- `PENDING` : En attente
- `COMPLETED` : Complétée
- `FAILED` : Échouée
- `CANCELLED` : Annulée

## Services

### WalletService
Gestion des wallets avec méthodes :
- `get_or_create_user_wallet(user)`
- `get_or_create_business_wallet(business)`
- `update_wallet_balance(wallet, amount, operation)`
- `check_sufficient_funds(wallet, amount)`
- `get_wallet_statistics(wallet)`

### TransactionService
Gestion des transactions avec méthodes :
- `process_deposit(wallet, amount, description)`
- `process_withdrawal(wallet, amount, description)`
- `process_transfer(sender_wallet, recipient_wallet, amount, description)`
- `get_transaction_by_reference(reference)`
- `cancel_transaction(transaction)`

## Vues

### Vues Web
- `WalletDetailView` : Affichage du wallet utilisateur
- `BusinessWalletDetailView` : Affichage du wallet entreprise
- `DepositView` : Formulaire de dépôt
- `WithdrawalView` : Formulaire de retrait
- `TransferView` : Formulaire de transfert
- `TransactionListView` : Liste des transactions
- `TransactionDetailView` : Détails d'une transaction

### Vues API (DRF)
- `UserWalletViewSet` : API pour les wallets utilisateur
- `BusinessWalletViewSet` : API pour les wallets entreprise
- `UserTransactionViewSet` : API pour les transactions utilisateur
- `BusinessTransactionViewSet` : API pour les transactions entreprise

## URLs

### Routes Web
- `/wallets/` : Détails du wallet utilisateur
- `/wallets/business/` : Détails du wallet entreprise
- `/wallets/deposit/` : Formulaire de dépôt
- `/wallets/withdraw/` : Formulaire de retrait
- `/wallets/transfer/` : Formulaire de transfert
- `/wallets/transactions/` : Liste des transactions
- `/wallets/transactions/<id>/` : Détails d'une transaction

### Routes API
- `/wallets/api/user-wallets/` : API wallets utilisateur
- `/wallets/api/business-wallets/` : API wallets entreprise
- `/wallets/api/user-transactions/` : API transactions utilisateur
- `/wallets/api/business-transactions/` : API transactions entreprise

## Formulaires

- `UserWalletForm` : Création/modification wallet utilisateur
- `BusinessWalletForm` : Création/modification wallet entreprise
- `UserTransactionForm` : Création transaction utilisateur
- `BusinessTransactionForm` : Création transaction entreprise
- `DepositForm` : Formulaire de dépôt
- `WithdrawalForm` : Formulaire de retrait
- `TransferForm` : Formulaire de transfert

## Sécurité

- Les wallets ne peuvent pas être supprimés (seulement désactivés)
- Les transactions ne peuvent pas être supprimées (seulement annulées)
- Vérification des fonds suffisants avant retrait/transfert
- Transactions atomiques pour garantir la cohérence des données

## Utilisation

### Créer un wallet pour un utilisateur
```python
from apps.wallets.services import WalletService

wallet, created = WalletService.get_or_create_user_wallet(user)
```

### Effectuer un dépôt
```python
from apps.wallets.services import TransactionService

transaction = TransactionService.process_deposit(
    wallet=wallet,
    amount=100.00,
    description="Dépôt initial"
)
```

### Effectuer un transfert
```python
outgoing, incoming = TransactionService.process_transfer(
    sender_wallet=wallet1,
    recipient_wallet=wallet2,
    amount=50.00,
    description="Transfert entre comptes"
)
```

## Templates

L'app inclut des templates pour :
- Affichage des détails de wallet
- Formulaires de dépôt, retrait et transfert
- Liste des transactions
- Détails d'une transaction

Tous les templates utilisent Bootstrap pour le style et sont traduits avec Django i18n. 