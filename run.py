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

from gestion.models import (
    Poste, Ouvrier, AffectationPoste, Livreur, Produit, 
    CommandeLivreur, LigneCommande, EntreeStock
)

# Liste étendue de noms ivoiriens réalistes
PRENOMS_MASCULINS = ["Koffi", "Yao", "Kouamé", "Jean", "Serge", "Alain", "Moussa", 
                    "Daouda", "Abdoul", "Mohamed", "Paul", "Armand", "Ismaël", "Mamadou"]
PRENOMS_FEMININS = ["Aminata", "Fatou", "Aïcha", "Mariam", "Adjoua", "Affoué", 
                   "Naminata", "Ramatoulaye", "Kadidja", "Salimata", "Régina", "Bintou", "Estelle"]
NOMS = ["Kouassi", "Koné", "Yao", "Bamba", "Diabaté", "Sangaré", "Touré", 
       "Coulibaly", "Ouattara", "Diarra", "Yéo", "Keita", "Cissé", "Aké", "Soro", "Fofana", "Kouadio"]

def generer_telephone():
    """Génère un numéro de téléphone ivoirien valide (01, 05 ou 07)"""
    prefixe = random.choice(['01', '05', '07'])
    return prefixe + ''.join([str(random.randint(0, 9)) for _ in range(8)])

def generer_nom_complet():
    """Génère un nom complet ivoirien réaliste"""
    if random.choice([True, False]):  # Homme ou femme
        return f"{random.choice(PRENOMS_MASCULINS)} {random.choice(NOMS)}"
    else:
        return f"{random.choice(PRENOMS_FEMININS)} {random.choice(NOMS)}"

def creer_postes():
    """Crée les différents postes de la boulangerie"""
    postes = [
        {"nom": "Boulanger", "remuneration": Decimal('2500'), "mode_paiement": "jour"},
        {"nom": "Vendeur", "remuneration": Decimal('2000'), "mode_paiement": "jour"},
        {"nom": "Livreur", "remuneration": Decimal('3000'), "mode_paiement": "jour"},
        {"nom": "Gérant", "remuneration": Decimal('500000'), "mode_paiement": "mois"},
        {"nom": "Comptable", "remuneration": Decimal('300000'), "mode_paiement": "mois"},
        {"nom": "Pâtissier", "remuneration": Decimal('2800'), "mode_paiement": "jour"},
    ]
    
    for poste in postes:
        Poste.objects.get_or_create(nom=poste["nom"], defaults=poste)
    print(f"✅ {len(postes)} postes créés")

def creer_ouvriers():
    """Crée les ouvriers avec des données réalistes"""
    created = 0
    while created < 15:  # On veut 15 ouvriers
        try:
            nom = generer_nom_complet()
            telephone = generer_telephone()
            
            Ouvrier.objects.create(
                nom=nom,
                telephone=telephone
            )
            created += 1
        except IntegrityError:
            continue  # Si le nom ou téléphone existe déjà, on réessaye
    
    print(f"✅ {created} ouvriers créés")

def creer_affectations():
    """Affecte les ouvriers à des postes"""
    postes = list(Poste.objects.all())
    
    for ouvrier in Ouvrier.objects.all():
        date_debut = timezone.now() - timedelta(days=random.randint(30, 365))
        
        # 20% de chance que l'affectation soit terminée
        date_fin = None
        if random.random() < 0.2:
            date_fin = date_debut + timedelta(days=random.randint(30, 180))
        
        AffectationPoste.objects.create(
            ouvrier=ouvrier,
            poste=random.choice(postes),
            date_debut=date_debut,
            date_fin=date_fin
        )
    print(f"✅ {Ouvrier.objects.count()} affectations créées")

def creer_livreurs():
    """Crée les livreurs avec au moins 3 actifs"""
    created = 0
    actifs = 0
    
    while created < 8:  # On veut 8 livreurs
        try:
            nom = generer_nom_complet()
            telephone = generer_telephone()
            
            # On s'assure qu'au moins 3 sont actifs
            est_actif = random.choice([True, False]) if actifs >= 3 else True
            
            Livreur.objects.create(
                nom=nom,
                telephone=telephone,
                actif=est_actif
            )
            created += 1
            if est_actif:
                actifs += 1
        except IntegrityError:
            continue
    
    print(f"✅ {created} livreurs créés (dont {actifs} actifs)")

def creer_produits():
    """Crée les produits de la boulangerie"""
    produits = [
        {"nom": "Pain", "prix_vente": Decimal('150'), "prix_livreur": Decimal('100'), "stock": 100},
        {"nom": "Croissant", "prix_vente": Decimal('300'), "prix_livreur": Decimal('250'), "stock": 50},
        {"nom": "Baguette", "prix_vente": Decimal('200'), "prix_livreur": Decimal('150'), "stock": 80},
        {"nom": "Gateau", "prix_vente": Decimal('500'), "prix_livreur": Decimal('400'), "stock": 30},
        {"nom": "Donut", "prix_vente": Decimal('250'), "prix_livreur": Decimal('200'), "stock": 60},
        {"nom": "Pain au chocolat", "prix_vente": Decimal('350'), "prix_livreur": Decimal('300'), "stock": 40},
    ]
    
    for produit in produits:
        Produit.objects.get_or_create(nom=produit["nom"], defaults=produit)
    print(f"✅ {len(produits)} produits créés")

def creer_entrees_stock():
    """Crée les entrées en stock"""
    fournisseurs = ["CI Foods", "Abidjan Farine", "Yamoussoukro Lait", "San Pedro Sucre"]
    
    for produit in Produit.objects.all():
        for _ in range(3):  # 3 entrées par produit
            EntreeStock.objects.create(
                produit=produit,
                quantite=random.randint(20, 100),
                prix_achat=produit.prix_vente * Decimal(str(random.uniform(0.6, 0.8))),
                fournisseur=random.choice(fournisseurs),
                responsable=generer_nom_complet()
            )
    print(f"✅ {EntreeStock.objects.count()} entrées de stock créées")

def creer_commandes_livreurs():
    """Crée des commandes pour les livreurs actifs"""
    livreurs = list(Livreur.objects.filter(actif=True))
    produits = list(Produit.objects.all())
    
    if not livreurs:
        print("❌ Aucun livreur actif - pas de commandes créées")
        return
    
    for _ in range(20):  # 20 commandes
        commande = CommandeLivreur.objects.create(
            livreur=random.choice(livreurs),
            total=Decimal('0'),
            payee=random.choice([True, False]),
            mode_paiement=random.choice(['espece', 'mobile', 'virement'])
        )
        
        # Ajoute 1 à 5 produits différents
        for produit in random.sample(produits, random.randint(1, 5)):
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=random.randint(1, 10),
                prix_unitaire=produit.prix_livreur
            )
        
        # Met à jour le total
        commande.total = sum(
            ligne.quantite * ligne.prix_unitaire 
            for ligne in commande.lignes.all()
        )
        commande.save()
    
    print(f"✅ {CommandeLivreur.objects.count()} commandes créées")

def main():
    """Fonction principale"""
    print("\n" + "="*50)
    print("  GÉNÉRATION DES DONNÉES DE LA BOULANGERIE")
    print("="*50 + "\n")
    
    print("🔄 Nettoyage de la base de données...")
    models = [LigneCommande, CommandeLivreur, EntreeStock, 
              AffectationPoste, Produit, Livreur, Ouvrier, Poste]
    
    for model in models:
        model.objects.all().delete()
    print("✅ Base nettoyée avec succès\n")
    
    print("🏗️ Création des données...")
    creer_postes()
    creer_ouvriers()
    creer_affectations()
    creer_livreurs()
    creer_produits()
    creer_entrees_stock()
    creer_commandes_livreurs()
    
    print("\n" + "📊 RÉCAPITULATIF FINAL:")
    print(f"- Postes: {Poste.objects.count()}")
    print(f"- Ouvriers: {Ouvrier.objects.count()}")
    print(f"- Livreurs: {Livreur.objects.count()} (dont {Livreur.objects.filter(actif=True).count()} actifs)")
    print(f"- Produits: {Produit.objects.count()}")
    print(f"- Commandes: {CommandeLivreur.objects.count()}")
    print(f"- Lignes de commande: {LigneCommande.objects.count()}")
    print(f"- Entrées de stock: {EntreeStock.objects.count()}")
    print("\n🎉 Données générées avec succès!")

if __name__ == "__main__":
    main()