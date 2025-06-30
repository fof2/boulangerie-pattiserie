from django.urls import path
from .viewslivreurs import (
    LivreurListView,
    LivreurCreateView,
    LivreurUpdateView,
    LivreurDeleteView
)

urlpatterns = [
    path('', LivreurListView.as_view(), name='livreur_liste'),
    path('ajouter/', LivreurCreateView.as_view(), name='livreur_ajouter'),
    path('<int:pk>/modifier/', LivreurUpdateView.as_view(), name='livreur_modifier'),
    path('<int:pk>/supprimer/', LivreurDeleteView.as_view(), name='livreur_supprimer'),
]
