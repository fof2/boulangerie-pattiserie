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
    if request.method == 'POST':
        user = request.user
        # Récupération des données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation des champs obligatoires
        if not all([username, email, first_name, last_name]):
            messages.error(request, "Tous les champs sont obligatoires")
        else:
            # Mise à jour des informations
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, "Profil mis à jour avec succès!")
            return redirect('mon_profil')
    
    return render(request, 'gestion/mon_profil.html', {'user': request.user})

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
    
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncYear
from django.db.models import Sum, Count, F, Q, DecimalField, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from decimal import Decimal
from .models import Ouvrier, Poste, AffectationPoste, Livreur, Produit, CommandeLivreur, LigneCommande

@login_required
def statistiques(request):
    # Paramètres de période
    period = request.GET.get('period', 'day')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Période par défaut (30 derniers jours)
    if not date_from or not date_to:
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=30)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Fonction de troncature de date
    def trunc_date(field):
        if period == 'day': return TruncDay(field)
        elif period == 'month': return TruncMonth(field)
        return TruncYear(field)
    
    # Statistiques des commandes par période
    commandes_period = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).annotate(
        period=trunc_date('date')
    ).values('period').annotate(
        count=Count('id', output_field=IntegerField()),
        total=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2)),
        payees=Count('id', filter=Q(payee=True), output_field=IntegerField())
    ).order_by('period')

    # Préparation des données pour les graphiques
    period_labels = []
    commandes_data = []
    commandes_total = []
    
    if commandes_period:
        period_labels = [item['period'].strftime('%d/%m/%Y' if period == 'day' else '%m/%Y' if period == 'month' else '%Y') 
                        for item in commandes_period]
        commandes_data = [item['count'] for item in commandes_period]
        commandes_total = [float(item['total'] or 0) for item in commandes_period]
    else:
        # Valeurs par défaut si aucune donnée
        period_labels = []
        commandes_data = []
        commandes_total = []
    
    # Statistiques des livreurs avec output_field explicite
    livreurs_stats = Livreur.objects.annotate(
        nb_commandes=Coalesce(
            Count('commandelivreur', 
                  filter=Q(commandelivreur__date__date__gte=date_from, 
                           commandelivreur__date__date__lte=date_to),
                  output_field=IntegerField()), 
            0,
            output_field=IntegerField()
        ),
        total_ventes=Coalesce(
            Sum('commandelivreur__total', 
                filter=Q(commandelivreur__date__date__gte=date_from, 
                         commandelivreur__date__date__lte=date_to),
                output_field=DecimalField(max_digits=10, decimal_places=2)), 
            0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        commandes_payees=Coalesce(
            Count('commandelivreur', 
                  filter=Q(commandelivreur__payee=True, 
                           commandelivreur__date__date__gte=date_from, 
                           commandelivreur__date__date__lte=date_to),
                  output_field=IntegerField()), 
            0,
            output_field=IntegerField()
        )
    ).order_by('-total_ventes').values(
        'id', 'nom', 'nb_commandes', 'total_ventes', 'commandes_payees'
    )
    
    # Statistiques des produits avec output_field explicite
    produits_stats = Produit.objects.annotate(
        quantite_vendue=Coalesce(
            Sum('lignecommande__quantite', 
                filter=Q(lignecommande__commande__date__date__gte=date_from, 
                         lignecommande__commande__date__date__lte=date_to),
                output_field=IntegerField()), 
            0,
            output_field=IntegerField()
        ),
        chiffre_affaire=Coalesce(
            Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire'), 
                filter=Q(lignecommande__commande__date__date__gte=date_from, 
                         lignecommande__commande__date__date__lte=date_to),
                output_field=DecimalField(max_digits=10, decimal_places=2)), 
            0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-chiffre_affaire').values(
        'id', 'nom', 'quantite_vendue', 'chiffre_affaire'
    )
    
    # Statistiques des ouvriers avec output_field explicite
    ouvriers_stats = Ouvrier.objects.annotate(
        jours_travailles=Coalesce(
            Count('affectationposte', 
                  filter=Q(affectationposte__date_debut__lte=date_to) & 
                         (Q(affectationposte__date_fin__gte=date_from) | 
                          Q(affectationposte__date_fin__isnull=True)),
                  output_field=IntegerField()), 
            0,
            output_field=IntegerField()
        ),
        postes_occupes=Coalesce(
            Count('affectationposte__poste', distinct=True,
                  filter=Q(affectationposte__date_debut__lte=date_to) & 
                         (Q(affectationposte__date_fin__gte=date_from) | 
                          Q(affectationposte__date_fin__isnull=True)),
                  output_field=IntegerField()), 
            0,
            output_field=IntegerField()
        )
    ).order_by('-jours_travailles').values(
        'id', 'nom', 'jours_travailles', 'postes_occupes'
    )
    
    context = {
        'livreurs_stats': list(livreurs_stats),
        'produits_stats': list(produits_stats),
        'ouvriers_stats': list(ouvriers_stats),
        'commandes_period': list(commandes_period),
        'period_labels': json.dumps(period_labels),
        'commandes_data': json.dumps(commandes_data),
        'commandes_total': json.dumps(commandes_total),
        'period': period,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
    }

        # Calcul des totaux pour les pourcentages
    total_commandes = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).count()

    total_ca = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).aggregate(total=Sum('total'))['total'] or 0

    total_quantite = LigneCommande.objects.filter(
        commande__date__date__gte=date_from,
        commande__date__date__lte=date_to
    ).aggregate(total=Sum('quantite'))['total'] or 0

    total_ca_produits = sum(p['chiffre_affaire'] for p in produits_stats)

    total_jours = sum(o['jours_travailles'] for o in ouvriers_stats)

    context.update({
        'total_commandes': total_commandes,
        'total_ca': total_ca,
        'total_quantite': total_quantite,
        'total_ca_produits': total_ca_produits,
        'total_jours': total_jours,
    })
        # Calcul des totaux pour les pourcentages
    total_commandes = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).count()

    total_ca = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).aggregate(total=Sum('total'))['total'] or 0

    total_quantite = LigneCommande.objects.filter(
        commande__date__date__gte=date_from,
        commande__date__date__lte=date_to
    ).aggregate(total=Sum('quantite'))['total'] or 0

    total_ca_produits = sum(p['chiffre_affaire'] for p in produits_stats)
    total_jours = sum(o['jours_travailles'] for o in ouvriers_stats)
    
    # Ajout des totaux pour les commandes par période
    total_commandes_period = sum(c['count'] for c in commandes_period)
    total_commandes_amount = sum(c['total'] or 0 for c in commandes_period)
    total_payees_period = sum(c['payees'] for c in commandes_period)
    
    # Calcul du total des payées pour les livreurs
    total_payees = sum(l['commandes_payees'] for l in livreurs_stats)
    
    # Calcul du total des postes occupés
    total_postes = sum(o['postes_occupes'] for o in ouvriers_stats)

    context = {
        'livreurs_stats': list(livreurs_stats),
        'produits_stats': list(produits_stats),
        'ouvriers_stats': list(ouvriers_stats),
        'commandes_period': list(commandes_period),
        'period_labels': json.dumps(period_labels),
        'commandes_data': json.dumps(commandes_data),
        'commandes_total': json.dumps(commandes_total),
        'period': period,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'total_commandes': total_commandes,
        'total_ca': total_ca,
        'total_quantite': total_quantite,
        'total_ca_produits': total_ca_produits,
        'total_jours': total_jours,
        'total_commandes_period': total_commandes_period,
        'total_commandes_amount': total_commandes_amount,
        'total_payees_period': total_payees_period,
        'total_payees': total_payees,
        'total_postes': total_postes,
    }
    
    
    return render(request, 'gestion/statistiques.html', context)
def stats_data(request):
    # Cette vue peut être utilisée pour des requêtes AJAX
    # Reprend la même logique que la vue statistiques mais retourne du JSON
    period = request.GET.get('period', 'day')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=30)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    commandes_period = CommandeLivreur.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).annotate(
        period=TruncDay('date') if period == 'day' else 
              (TruncMonth('date') if period == 'month' else TruncYear('date'))
    ).values('period').annotate(
        count=Count('id'),
        total=Sum('total'),
        payees=Count('id', filter=Q(payee=True))
    ).order_by('period')
    
    period_labels = [item['period'].strftime('%d/%m/%Y' if period == 'day' else '%m/%Y' if period == 'month' else '%Y') 
                    for item in commandes_period]
    commandes_data = [item['count'] for item in commandes_period]
    commandes_total = [float(item['total'] or 0) for item in commandes_period]
    
    data = {
        'period_labels': period_labels,
        'commandes_data': commandes_data,
        'commandes_total': commandes_total,
    }
    
    return JsonResponse(data)