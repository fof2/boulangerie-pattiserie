from django.urls import path
from . import views  # Importez le module views (si vos vues sont dans views.py)
# OU
from .viewscommandes import (  # Si vos vues sont dans viewscommandes.py
    CommandeListView, 
    creer_commande,
    CommandeDetailView,
    generer_facture_livreur,
    marquer_commande_payee,
    generer_bilan_pdf,
    bilan_periodique,
    liste_entrees_stock,
    get_prix_produit,
    ajouter_entree_stock,
    dashboard
)

urlpatterns = [
    path('', CommandeListView.as_view(), name='commande_liste'),
    path('dashboard/', dashboard, name='dashboard'),
    path('creer/', creer_commande, name='commande_creer'),
    path('livreurs/<int:livreur_id>/commandes/', CommandeListView.as_view(), name='commandes_par_livreur'),
    path('creer/<int:livreur_id>/', creer_commande, name='commande_creer_pour_livreur'),
    path('livreur/<int:livreur_id>/', CommandeListView.as_view(), name='commandes_par_livreur'),
    path('get_prix_produit/<int:produit_id>/', get_prix_produit, name='get_prix_produit'),
    path('<int:pk>/', CommandeDetailView.as_view(), name='commande_detail'),
    path('livreurs/<int:livreur_id>/facture/', generer_facture_livreur, name='generer_facture_livreur'),
    path('<int:pk>/pdf/', generer_facture_livreur, name='commande_pdf'),
    path('<int:pk>/payee/', marquer_commande_payee, name='commande_marquer_payee'),
    path('bilans/<str:periode>/', bilan_periodique, name='bilan_periodique'),
    path('bilans/<str:periode>/pdf/', generer_bilan_pdf, name='generer_bilan_pdf'),
    path('entrees-stock/', liste_entrees_stock, name='liste_entrees_stock'),
    path('entrees-stock/ajouter/', ajouter_entree_stock, name='ajouter_entree_stock'),
]