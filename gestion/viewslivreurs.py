# gestion/views/livreurs.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import LivreurForm
from .models import Livreur
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count


@method_decorator(login_required, name='dispatch')
class LivreurListView(ListView):
    """
    Vue pour lister les livreurs avec possibilité de recherche et filtrage
    """
    model = Livreur
    template_name = 'gestion/livreurs/liste.html'
    context_object_name = 'livreurs'  # Utilisé dans le template comme livreurs_stats
    paginate_by = 10  # Pagination: 10 livreurs par page

    def get_queryset(self):
        """Filtrage et recherche des livreurs"""
        queryset = super().get_queryset().order_by('nom')
        search_query = self.request.GET.get('q', '')
        actif_filter = self.request.GET.get('actif')  # Nouveau filtre par statut actif
        
        # Filtre combiné pour la recherche
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) | 
                Q(telephone__icontains=search_query)
            )
            
        # Filtre par statut actif/inactif
        if actif_filter in ['True', 'False']:
            queryset = queryset.filter(actif=actif_filter == 'True')
            
        return queryset

    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['actif_filter'] = self.request.GET.get('actif', '')
        
        # Annotation du nombre de commandes par livreur
        livreurs = context['livreurs'].annotate(nb_commandes=Count('commandelivreur'))
        context['livreurs_stats'] = livreurs
        
        return context


@method_decorator(login_required, name='dispatch')
class LivreurCreateView(CreateView):
    """
    Vue pour créer un nouveau livreur
    """
    model = Livreur
    form_class = LivreurForm
    template_name = 'gestion/livreurs/form.html'
    success_url = reverse_lazy('livreur_liste')

    def form_valid(self, form):
        """Traitement du formulaire valide"""
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Livreur ajouté avec succès!")
            return response
        except IntegrityError:
            messages.error(self.request, "Un livreur avec ce nom ou ce numéro existe déjà.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Traitement du formulaire invalide"""
        messages.error(self.request, "Veuillez corriger les erreurs ci-dessous.")
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class LivreurUpdateView(UpdateView):
    """
    Vue pour modifier un livreur existant
    """
    model = Livreur
    form_class = LivreurForm
    template_name = 'gestion/livreurs/form.html'
    success_url = reverse_lazy('livreur_liste')

    def form_valid(self, form):
        """Traitement du formulaire valide"""
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Livreur mis à jour avec succès!")
            return response
        except IntegrityError:
            messages.error(self.request, "Un livreur avec ce nom ou ce numéro existe déjà.")
            return self.form_invalid(form)


@method_decorator(login_required, name='dispatch')
class LivreurDeleteView(DeleteView):
    """
    Vue pour supprimer un livreur
    """
    model = Livreur
    template_name = 'gestion/livreurs/confirm_delete.html'
    success_url = reverse_lazy('livreur_liste')

    def delete(self, request, *args, **kwargs):
        """Traitement de la suppression"""
        messages.success(request, "Livreur supprimé avec succès!")
        return super().delete(request, *args, **kwargs)