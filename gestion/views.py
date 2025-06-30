# Bloc 1
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Count
from django.db.models import Q
from datetime import datetime
from django.db import models
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http import HttpResponseRedirect
from django.utils import timezone
import logging

from django.db import IntegrityError
from .models import Ouvrier, Poste, AffectationPoste
from .forms import OuvrierForm, AffectationPosteForm
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http import HttpResponseRedirect
from django.utils import timezone
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Bloc 2 (qui contient la bonne importation mais est un doublon)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from .models import Ouvrier, Poste, AffectationPoste
from .forms import OuvrierForm, AffectationPosteForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator # <-- CETTE LIGNE EST LA BONNE

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('accueil')  # Remplacez par le nom de votre vue d'accueil
        else:
            messages.error(request, "Identifiant ou mot de passe incorrect")
    
    return render(request, 'registration/login.html')

@login_required
def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required
def mon_profil(request):
    user = request.user
    context = {
        'user': user,
        'title': 'Mon Profil'
    }
    return render(request, 'gestion/mon_profil.html', context)

@login_required
def parametres(request):
    context = {
        'title': 'Paramètres'
    }
    return render(request, 'gestion/parametres.html', context)

@method_decorator(login_required, name='dispatch')
class ListeOuvriersView(ListView):
    model = Ouvrier
    template_name = 'gestion/ouvriers/liste.html'
    context_object_name = 'ouvriers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        
        # Filtrage par recherche si un terme est fourni
        if search_query:
            queryset = queryset.filter(
                models.Q(nom__icontains=search_query) | 
                models.Q(telephone__icontains=search_query)
            )
        
        # Annotation des doublons
        queryset = queryset.annotate(
            duplicate_names=Count('nom', distinct=False),
            duplicate_phones=Count('telephone', distinct=False)
        )
        
        return queryset.order_by('nom', 'telephone')

@method_decorator(login_required, name='dispatch') # <-- MODIFIEZ CECI
class DetailOuvrierView(DetailView):
    model = Ouvrier
    template_name = 'gestion/ouvriers/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['affectations'] = self.object.affectationposte_set.select_related('poste').order_by('-date_debut')
        context['postes_disponibles'] = Poste.objects.all().order_by('nom')
        return context
    

# Configuration du logger
logger = logging.getLogger(__name__)
@method_decorator(login_required, name='dispatch')
class AjouterOuvrierView(CreateView):
    model = Ouvrier
    form_class = OuvrierForm
    template_name = 'gestion/ouvriers/ajouter.html'
    success_url = reverse_lazy('liste_ouvriers')

    def get_context_data(self, **kwargs):
        # Initialiser self.object à None pour éviter l'erreur
        self.object = None
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['affectation_form'] = AffectationPosteForm(self.request.POST)
        else:
            context['affectation_form'] = AffectationPosteForm(initial={
                'date_debut': timezone.now().date()
            })
        return context

    def post(self, request, *args, **kwargs):
        # Initialiser self.object
        self.object = None
        form = self.get_form()
        affectation_form = AffectationPosteForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder l'ouvrier
                    self.object = form.save(commit=False)
                    self.object.nom = form.cleaned_data['nom'].strip().upper()
                    self.object.telephone = form.cleaned_data['telephone'].strip()
                    self.object.save()

                    # Valider l'affectation
                    if affectation_form.is_valid():
                        affectation = affectation_form.save(commit=False)
                        affectation.ouvrier = self.object
                        affectation.save()
                        messages.success(request, "Ouvrier et affectation ajoutés avec succès!")
                        return HttpResponseRedirect(self.get_success_url())
                    else:
                        for field, errors in affectation_form.errors.items():
                            for error in errors:
                                messages.error(request, f"Erreur affectation - {field}: {error}")
                        return self.render_to_response(
                            self.get_context_data(form=form, affectation_form=affectation_form))
            
            except IntegrityError as e:
                messages.error(request, "Erreur de base de données. Possible doublon.")
                logger.error(f"Erreur intégrité: {str(e)}")
            except Exception as e:
                messages.error(request, f"Erreur inattendue: {str(e)}")
                logger.error(f"Erreur inattendue: {str(e)}")
        
        # Si le formulaire principal est invalide ou si exception
        return self.render_to_response(
            self.get_context_data(form=form, affectation_form=affectation_form))

@method_decorator(login_required, name='dispatch') # <-- MODIFIEZ CECI
class ModifierOuvrierView(UpdateView):
    model = Ouvrier
    form_class = OuvrierForm
    template_name = 'gestion/ouvriers/ajouter.html'
    success_url = reverse_lazy('liste_ouvriers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['affectation_form'] = AffectationPosteForm(self.request.POST)
        else:
            context['affectation_form'] = AffectationPosteForm()
        return context
    
@method_decorator(login_required, name='dispatch')
class SupprimerOuvrierView(DeleteView):
    model = Ouvrier
    template_name = 'gestion/ouvriers/supprimer.html'
    success_url = reverse_lazy('liste_ouvriers')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Ouvrier supprimé avec succès!")
        return response

# ... (vos fonctions ajouter_affectation, terminer_affectation, modifier_affectation restent inchangées car elles utilisent déjà @login_required directement sur la fonction) ...
def ajouter_affectation(request, ouvrier_id=None): # Ajout de ouvrier_id=None
    if request.method == 'POST':
        try:
      
            current_ouvrier_id = ouvrier_id
            if not current_ouvrier_id:
                current_ouvrier_id = request.POST.get('ouvrier')

            poste_id = request.POST.get('poste')
            date_debut_str = request.POST.get('date_debut')
            date_fin_str = request.POST.get('date_fin')

            # Vérification des champs obligatoires
            if not poste_id or not current_ouvrier_id or not date_debut_str:
                raise ValueError("Veuillez remplir tous les champs obligatoires (ouvrier, poste, date de début).")

            # Convertir les dates
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            date_fin = None
            if date_fin_str:
                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()

            with transaction.atomic():
                # Terminer l'affectation précédente de l'ouvrier s'il y en a une en cours
                AffectationPoste.objects.filter(
                    ouvrier_id=current_ouvrier_id,
                    date_fin__isnull=True
                ).update(date_fin=timezone.now().date()) # Utiliser timezone.now().date() pour la date actuelle

                # Créer la nouvelle affectation
                AffectationPoste.objects.create(
                    ouvrier_id=current_ouvrier_id,
                    poste_id=poste_id,
                    date_debut=date_debut,
                    date_fin=date_fin
                )

            ouvrier = get_object_or_404(Ouvrier, pk=current_ouvrier_id)
            poste = get_object_or_404(Poste, pk=poste_id)
            messages.success(request, f"Affectation réussie : {ouvrier.nom} → {poste.nom}")

            # Rediriger en fonction de l'origine de la requête
            if ouvrier_id: # Si l'affectation vient de la page détail ouvrier
                return redirect('detail_ouvrier', pk=current_ouvrier_id)
            else: # Si l'affectation vient de la page détail poste
                return redirect('detail_poste', pk=poste_id)

        except ValueError as ve:
            messages.error(request, f"Erreur de validation: {str(ve)}")
            # Rediriger vers la page précédente si possible, sinon une page par défaut
            return redirect(request.META.get('HTTP_REFERER', reverse('liste_postes')))
        except Exception as e:
            messages.error(request, f"Une erreur inattendue est survenue : {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', reverse('liste_postes')))

    # Si la méthode n'est pas POST, rediriger (cette vue ne doit être appelée qu'en POST)
    return redirect('liste_postes')

def liste_postes(request):
    query = request.GET.get('q', '')  # Récupère le paramètre de recherche 'q'
    postes = Poste.objects.all()
    
    if query:
        postes = postes.filter(
            Q(nom__icontains=query) | 
            Q(remuneration__icontains=query) |
            Q(mode_paiement__icontains=query)
        )
    
    context = {
        'postes': postes,
        'search_query': query  # Pour afficher la requête dans le template
    }
    return render(request, 'gestion/liste_postes.html', context)


def terminer_affectation(request, pk):
    affectation = get_object_or_404(AffectationPoste, pk=pk)
    
    if affectation.date_fin:
        messages.warning(request, "Cette affectation est déjà terminée.")
    else:
        affectation.date_fin = timezone.now().date()
        affectation.save()
        messages.success(request, f"L'affectation de {affectation.ouvrier.nom} au poste {affectation.poste.nom} a été terminée.")
    
    # Rediriger vers la page de détail de l'ouvrier
    return redirect('detail_ouvrier', pk=affectation.ouvrier.id)

# ... Vos autres vues ...


def modifier_affectation(request, pk):
    affectation = get_object_or_404(AffectationPoste, pk=pk)
    
    if request.method == 'POST':
        form = AffectationPosteForm(request.POST, instance=affectation)
        if form.is_valid():
            form.save()
            messages.success(request, "Affectation modifiée avec succès!")
            # Rediriger vers la page de détail de l'ouvrier ou du poste concerné
            # Ici, je redirige vers la page de l'ouvrier pour voir toutes ses affectations
            return redirect('detail_ouvrier', pk=affectation.ouvrier.id) 
    else:
        form = AffectationPosteForm(instance=affectation)
        
    return render(request, 'gestion/affectation_form.html', {
        'form': form,
        'affectation': affectation,
        'page_title': f"Modifier l'affectation de {affectation.ouvrier.nom}" # Ajout d'un titre pour le template
    })

@method_decorator(login_required, name='dispatch')
class ListePostesView(ListView):
    model = Poste
    template_name = 'gestion/postes/liste.html'
    context_object_name = 'postes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(remuneration__icontains=search_query) |
                Q(mode_paiement__icontains=search_query)
            )
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

@method_decorator(login_required, name='dispatch')
class DetailPosteView(DetailView):
    model = Poste
    template_name = 'gestion/postes/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ouvriers disponibles (non affectés à ce poste)
        context['ouvriers_disponibles'] = Ouvrier.objects.exclude(
            id__in=AffectationPoste.objects.filter(
                poste=self.object,
                date_fin__isnull=True
            ).values_list('ouvrier_id', flat=True)
        ).order_by('nom')
        
        # Affectations actives pour ce poste
        context['affectations'] = AffectationPoste.objects.filter(
            poste=self.object,
            date_fin__isnull=True
        ).select_related('ouvrier')
        
        return context

def affecter_ouvrier_poste(request, poste_id):
    poste = get_object_or_404(Poste, pk=poste_id)
    
    if request.method == 'POST':
        ouvrier_id = request.POST.get('ouvrier')
        date_debut = request.POST.get('date_debut')
        
        # Création de l'affectation
        AffectationPoste.objects.create(
            poste=poste,
            ouvrier_id=ouvrier_id,
            date_debut=date_debut
        )
        messages.success(request, "Ouvrier affecté avec succès!")
        return redirect('detail_poste', pk=poste.id)
    
    return redirect('detail_poste', pk=poste.id)
@method_decorator(login_required, name='dispatch') # <-- MODIFIEZ CECI
class AjouterPosteView(CreateView):
    model = Poste
    fields = ['nom', 'remuneration', 'mode_paiement']
    template_name = 'gestion/postes/ajouter.html'
    success_url = reverse_lazy('liste_postes')

    def form_valid(self, form):
        messages.success(self.request, "Poste ajouté avec succès!")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch') # <-- MODIFIEZ CECI
class ModifierPosteView(UpdateView):
    model = Poste
    fields = ['nom', 'remuneration', 'mode_paiement']
    template_name = 'gestion/postes/ajouter.html'
    success_url = reverse_lazy('liste_postes')
    
    def form_valid(self, form):
        messages.success(self.request, "Poste modifié avec succès!")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch') # <-- MODIFIEZ CECI
class SupprimerPosteView(DeleteView):
    model = Poste
    template_name = 'gestion/postes/supprimer.html'
    success_url = reverse_lazy('liste_postes')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Poste supprimé avec succès!")
        return super().delete(request, *args, **kwargs)