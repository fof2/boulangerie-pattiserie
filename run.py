import os
import django
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boulangerie.settings')
django.setup()

from gestion.models import (
    Poste, Ouvrier, AffectationPoste, Livreur, Produit, 
    CommandeLivreur, LigneCommande, EntreeStock
)

def creer_postes():
    postes = [
        {"nom": "Boulanger", "remuneration": Decimal('2500'), "mode_paiement": "jour"},
        {"nom": "Vendeur", "remuneration": Decimal('2000'), "mode_paiement": "jour"},
        {"nom": "Livreur", "remuneration": Decimal('3000'), "mode_paiement": "jour"},
        {"nom": "Gérant", "remuneration": Decimal('500000'), "mode_paiement": "mois"},
        {"nom": "Comptable", "remuneration": Decimal('300000'), "mode_paiement": "mois"},
    ]
    
    for poste_data in postes:
        Poste.objects.get_or_create(**poste_data)
    print("Postes créés avec succès!")

def creer_ouvriers():
    ouvriers = [
        {"nom": "Moussa Diop", "telephone": "771234567"},
        {"nom": "Amina Fall", "telephone": "761234567"},
        {"nom": "Jean Dupont", "telephone": "701234567"},
        {"nom": "Fatou Ndiaye", "telephone": "781234567"},
        {"nom": "Ibrahima Sow", "telephone": "771234568"},
    ]
    
    for ouvrier_data in ouvriers:
        Ouvrier.objects.get_or_create(**ouvrier_data)
    print("Ouvriers créés avec succès!")

def creer_affectations():
    postes = Poste.objects.all()
    ouvriers = Ouvrier.objects.all()
    
    for i, ouvrier in enumerate(ouvriers):
        poste = postes[i % len(postes)]  # Répartition cyclique des postes
        date_debut = timezone.now() - timedelta(days=random.randint(30, 365))
        
        AffectationPoste.objects.get_or_create(
            ouvrier=ouvrier,
            poste=poste,
            date_debut=date_debut,
            defaults={'date_fin': None}
        )
    print("Affectations créées avec succès!")

def creer_livreurs():
    livreurs = [
        {"nom": "Alioune Gueye", "telephone": "771234569", "actif": True},
        {"nom": "Papa Diouf", "telephone": "761234568", "actif": True},
        {"nom": "Samba Diallo", "telephone": "701234568", "actif": False},
    ]
    
    for livreur_data in livreurs:
        Livreur.objects.get_or_create(**livreur_data)
    print("Livreurs créés avec succès!")

def creer_produits():
    produits = [
        {"nom": "Pain", "prix_vente": Decimal('150'), "prix_livreur": Decimal('100'), "stock": 100},
        {"nom": "Croissant", "prix_vente": Decimal('300'), "prix_livreur": Decimal('250'), "stock": 50},
        {"nom": "Baguette", "prix_vente": Decimal('200'), "prix_livreur": Decimal('150'), "stock": 80},
        {"nom": "Gateau", "prix_vente": Decimal('500'), "prix_livreur": Decimal('400'), "stock": 30},
        {"nom": "Donut", "prix_vente": Decimal('250'), "prix_livreur": Decimal('200'), "stock": 60},
    ]
    
    for produit_data in produits:
        Produit.objects.get_or_create(nom=produit_data["nom"], defaults=produit_data)
    print("Produits créés avec succès!")

def creer_commandes_livreurs():
    livreurs = Livreur.objects.filter(actif=True)
    produits = Produit.objects.all()
    
    for i in range(5):
        livreur = random.choice(livreurs)
        commande = CommandeLivreur.objects.create(
            livreur=livreur,
            total=Decimal('0'),
            payee=random.choice([True, False]),
            mode_paiement=random.choice(['espece', 'mobile', 'virement'])
        )
        
        # Ajouter 1 à 5 lignes de commande
        for _ in range(random.randint(1, 5)):
            produit = random.choice(produits)
            quantite = random.randint(1, 10)
            
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=quantite,
                prix_unitaire=produit.prix_livreur
            )
        
        # Mettre à jour le total
        commande.total = sum(Decimal(str(ligne.total_ligne)) for ligne in commande.lignes.all())
        commande.save()
    print("Commandes livreurs créées avec succès!")

def creer_entrees_stock():
    produits = Produit.objects.all()
    responsables = ["M. Diallo", "Mme. Ndiaye", "M. Fall"]
    
    for produit in produits:
        for _ in range(2):  # 2 entrées par produit
            EntreeStock.objects.create(
                produit=produit,
                quantite=random.randint(20, 100),
                prix_achat=produit.prix_vente * Decimal('0.7'),  # 30% de marge
                fournisseur="Fournisseur " + random.choice(["A", "B", "C"]),
                responsable=random.choice(responsables)
            )
    print("Entrées de stock créées avec succès!")

def main():
    # Nettoyer la base de données (optionnel)
    print("Nettoyage des tables sélectionnées...")
    LigneCommande.objects.all().delete()
    CommandeLivreur.objects.all().delete()
    EntreeStock.objects.all().delete()
    AffectationPoste.objects.all().delete()
    Produit.objects.all().delete()
    Livreur.objects.all().delete()
    Ouvrier.objects.all().delete()
    Poste.objects.all().delete()
    
    # Création des données
    creer_postes()
    creer_ouvriers()
    creer_affectations()
    creer_livreurs()
    creer_produits()
    creer_entrees_stock()
    creer_commandes_livreurs()
    
    print("\nDonnées de base créées avec succès (sans ventes ni paiements)!")

if __name__ == "__main__":
    main()