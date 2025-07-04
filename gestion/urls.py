from django.urls import path
from django.views.generic import TemplateView
from .views import (
    custom_login,
    custom_logout,
    ListeOuvriersView,
    DetailOuvrierView,
    AjouterOuvrierView,
    ModifierOuvrierView,
    SupprimerOuvrierView,
    ajouter_affectation,
    terminer_affectation,
    modifier_affectation,
    ListePostesView,
    DetailPosteView,
    AjouterPosteView,
    ModifierPosteView,
    stats_data,
    SupprimerPosteView,
    affecter_ouvrier_poste,  
    mon_profil,
    statistiques,
    parametres,
)

urlpatterns = [
    # Authentification
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('statistiques/', statistiques, name='statistiques'),
    path('stats-data/', stats_data, name='stats_data'),
    
    # Page d'accueil
    path('', TemplateView.as_view(template_name='gestion/accueil.html'), name='accueil'),
    
    # Ouvriers
    path('ouvriers/', ListeOuvriersView.as_view(), name='liste_ouvriers'),
    path('ouvriers/ajouter/', AjouterOuvrierView.as_view(), name='ajouter_ouvrier'),
    path('ouvriers/<int:pk>/', DetailOuvrierView.as_view(), name='detail_ouvrier'),
    path('ouvriers/<int:pk>/modifier/', ModifierOuvrierView.as_view(), name='modifier_ouvrier'),
    path('ouvriers/<int:pk>/supprimer/', SupprimerOuvrierView.as_view(), name='supprimer_ouvrier'),

    # Affectations
    path('affectations/ajouter/', ajouter_affectation, name='ajouter_affectation_generique'),
    path('ouvriers/<int:ouvrier_id>/affectations/ajouter/', ajouter_affectation, name='ajouter_affectation'),
    path('affectations/<int:pk>/modifier/', modifier_affectation, name='modifier_affectation'),
    path('affectations/<int:pk>/terminer/', terminer_affectation, name='terminer_affectation'),
    
    # Postes
    path('postes/', ListePostesView.as_view(), name='liste_postes'),
    path('postes/ajouter/', AjouterPosteView.as_view(), name='ajouter_poste'),
    path('postes/<int:pk>/', DetailPosteView.as_view(), name='detail_poste'), 
    path('postes/<int:poste_id>/affecter/', affecter_ouvrier_poste, name='affecter_ouvrier_poste'),
    path('postes/<int:pk>/modifier/', ModifierPosteView.as_view(), name='modifier_poste'),
    path('postes/<int:pk>/supprimer/', SupprimerPosteView.as_view(), name='supprimer_poste'),

    # Profil et paramètres
    path('mon-profil/', mon_profil, name='mon_profil'),
    path('parametres/', parametres, name='parametres'),
]