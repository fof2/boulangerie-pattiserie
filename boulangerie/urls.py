from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from gestion import urlslivreurs, urlsproduits, urlscommandes

urlpatterns = [
    # Page de connexion comme page d'accueil principale
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # URLs admin
    path('admin/', admin.site.urls),
    
    # URLs d'authentification (incluant /login/, /logout/, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # URLs de votre application
    path('gestion/', include('gestion.urls')),
    path('livreurs/', include(urlslivreurs.urlpatterns)), 
    path('produits/', include(urlsproduits.urlpatterns)),
    path('commandes/', include(urlscommandes.urlpatterns)),
]