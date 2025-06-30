from django.urls import path
from .viewscommandes import CommandeDetailView, creer_commande
from .viewsproduits import  generate_pdf

from .viewsproduits import (
    ProduitListView,
    ProduitCreateView,
    ProduitUpdateView,
    ProduitDeleteView,
    ajuster_stock,
)

    
urlpatterns = [
    path('', ProduitListView.as_view(), name='produit_liste'),  # accessible à /produits/
    path('ajouter/', ProduitCreateView.as_view(), name='produit_ajouter'),
    path('modifier/<int:pk>/', ProduitUpdateView.as_view(), name='produit_modifier'),
    path('supprimer/<int:pk>/', ProduitDeleteView.as_view(), name='produit_supprimer'),
    path('ajuster-stock/<int:pk>/', ajuster_stock, name='produit_ajuster_stock'),
]

