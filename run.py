import os
import django
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal
from django.db.utils import IntegrityError

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boulangerie.settings')
django.setup()

from gestion.models import Produit, Livreur, CommandeLivreur, LigneCommande

def creer_produits():
    """Crée des produits réalistes pour une boulangerie"""
    produits = [
        {"nom": "Pain traditionnel", "prix_vente": 200, "prix_livreur": 150},
        {"nom": "Baguette", "prix_vente": 250, "prix_livreur": 200},
        {"nom": "Croissant", "prix_vente": 300, "prix_livreur": 250},
        {"nom": "Pain au chocolat", "prix_vente": 350, "prix_livreur": 300},
        {"nom": "Donut", "prix_vente": 250, "prix_livreur": 200},
        {"nom": "Tarte aux pommes", "prix_vente": 1500, "prix_livreur": 1300},
    ]
    
    for p in produits:
        Produit.objects.get_or_create(
            nom=p["nom"],
            defaults={
                "prix_vente": p["prix_vente"],
                "prix_livreur": p["prix_livreur"],
                "stock": random.randint(20, 100)
            }
        )
    print(f"✅ {Produit.objects.count()} produits créés")

def creer_livreurs():
    """Crée des livreurs avec des noms ivoiriens réalistes"""
    noms_livreurs = [
        "Koffi Konan", "Yao Kouassi", "Amani Traoré", 
        "Fatou Diabaté", "Moussa Cissé", "Aïcha Coulibaly"
    ]
    
    for nom in noms_livreurs:
        Livreur.objects.get_or_create(
            nom=nom,
            defaults={
                "telephone": f"07{random.randint(10000000, 99999999)}",
                "actif": True
            }
        )
    print(f"✅ {Livreur.objects.count()} livreurs créés")

def creer_commandes():
    """Crée des commandes réalistes sur les 6 derniers mois"""
    produits = list(Produit.objects.all())
    livreurs = list(Livreur.objects.filter(actif=True))
    
    if not produits or not livreurs:
        print("❌ Créez d'abord des produits et livreurs")
        return
    
    for i in range(120):  # 120 commandes au total
        # Date aléatoire dans les 6 derniers mois
        jours_aleatoires = random.randint(1, 180)
        date_commande = timezone.now() - timedelta(days=jours_aleatoires)
        
        # Création de la commande
        commande = CommandeLivreur.objects.create(
            livreur=random.choice(livreurs),
            date=date_commande,
            total=0,
            payee=random.choice([True, False]),
            mode_paiement=random.choice(['espece', 'mobile', 'virement'])
        )
        
        # Ajout de 1 à 5 produits par commande
        total_commande = 0
        for produit in random.sample(produits, random.randint(1, 5)):
            quantite = random.randint(1, 10)
            ligne = LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=quantite,
                prix_unitaire=produit.prix_livreur
            )
            total_commande += ligne.total_ligne
        
        # Mise à jour du total de la commande
        commande.total = total_commande
        commande.save()
    
    print(f"✅ {CommandeLivreur.objects.count()} commandes créées")
    print(f"✅ {LigneCommande.objects.count()} lignes de commande créées")

def verifier_donnees():
    """Vérifie que les données sont correctement liées"""
    from django.db.models import Sum, Count
    from django.db.models.functions import ExtractMonth
    
    print("\n🔍 Vérification des données:")
    
    # 1. Vérification des relations de base
    try:
        cmd = CommandeLivreur.objects.first()
        print(f"Première commande: ID {cmd.id} le {cmd.date} par {cmd.livreur.nom}")
        
        lignes = cmd.lignes.all()
        print(f"Cette commande a {lignes.count()} lignes")
        
        # 2. Test des requêtes du dashboard
        print("\nTest requête produits par mois:")
        test_produits = LigneCommande.objects.annotate(
            month=ExtractMonth('commande__date')
        ).values('month', 'produit__nom').annotate(
            total=Sum('quantite')
        ).order_by('month')[:5]
        
        for item in test_produits:
            print(f"Mois {item['month']}: {item['produit__nom']} x{item['total']}")
            
        print("\nTest requête chiffre d'affaires:")
        test_ca = CommandeLivreur.objects.annotate(
            month=ExtractMonth('date')
        ).values('month').annotate(
            total=Sum('total')
        ).order_by('month')[:6]
        
        for item in test_ca:
            print(f"Mois {item['month']}: {item['total']} FCFA")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {str(e)}")

def main():
    print("\n=== GÉNÉRATION DES DONNÉES DE TEST ===")
    print("Cette opération va effacer toutes les données existantes!")
    confirm = input("Voulez-vous continuer? (oui/non): ")
    
    if confirm.lower() != 'oui':
        print("Annulé")
        return
    
    print("\n🔄 Nettoyage des données existantes...")
    CommandeLivreur.objects.all().delete()
    LigneCommande.objects.all().delete()
    Produit.objects.all().delete()
    Livreur.objects.all().delete()
    
    print("\n🏗️ Création des nouvelles données...")
    creer_produits()
    creer_livreurs()
    creer_commandes()
    
    print("\n✅ Données générées avec succès!")
    print(f"Total produits: {Produit.objects.count()}")
    print(f"Total livreurs: {Livreur.objects.count()}")
    print(f"Total commandes: {CommandeLivreur.objects.count()}")
    print(f"Total lignes de commande: {LigneCommande.objects.count()}")
    
    # Vérification des données
    verifier_donnees()

if __name__ == "__main__":
    main()