from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from django.http import HttpResponse
from django.templatetags.static import static
from django.template.loader import render_to_string, get_template
from io import BytesIO
from django.http import JsonResponse
import os
import base64
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime
from calendar import month_name
from xhtml2pdf import pisa
from .models import CommandeLivreur, Livreur
from django.conf import settings
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
from calendar import month_name
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Sum  # Make sure you have these imports
from xhtml2pdf import pisa
from django.contrib import messages
from django.db.models import Sum, F, Q
from datetime import timedelta
from django.forms import inlineformset_factory
from django.db import transaction
from .models import CommandeLivreur, LigneCommande, Produit, Livreur, Vente, LigneVente, EntreeStock
from .forms import CommandeForm, EntreeStockForm, PaiementCommandeForm, LigneCommandeForm 
from django.forms import inlineformset_factory
from django.db import transaction
# Dans viewscommandes.py


def get_prix_produit(request, produit_id):
    print(f"Requête reçue pour produit ID: {produit_id}")  # Debug
    try:
        produit = Produit.objects.get(pk=produit_id)
        print(f"Produit trouvé: {produit.nom}, Prix: {produit.prix_livreur}")  # Debug
        return JsonResponse({
            'prix_livreur': str(produit.prix_livreur),
            'nom': produit.nom
        })
    except Produit.DoesNotExist:
        print("Produit non trouvé")  # Debug
        return JsonResponse({'error': 'Produit non trouvé'}, status=404)

def creer_commande(request, livreur_id=None):
    livreur = get_object_or_404(Livreur, pk=livreur_id) if livreur_id else None
    
    LigneCommandeFormSet = inlineformset_factory(
        CommandeLivreur,
        LigneCommande,
        form=LigneCommandeForm,
        fields=('produit', 'quantite'),
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = CommandeForm(request.POST)
        formset = LigneCommandeFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    commande = form.save(commit=False)
                    if livreur:
                        commande.livreur = livreur
                    commande.save()
                    
                    # Sauvegarder les lignes de commande
                    instances = formset.save(commit=False)
                    for instance in instances:
                        instance.commande = commande
                        instance.prix_unitaire = instance.produit.prix_livreur  # Prix automatique
                        instance.save()
                    
                    # Supprimer les lignes marquées pour suppression
                    for obj in formset.deleted_objects:
                        obj.delete()
                    
                    # Calculer le total
                    commande.total = sum(
                        ligne.total_ligne 
                        for ligne in commande.lignes.all()
                    )
                    commande.save()
                    
                    messages.success(request, "Commande enregistrée avec succès!")
                    return redirect('commande_detail', pk=commande.pk)
            
            except Exception as e:
                messages.error(request, f"Une erreur est survenue: {str(e)}")
    else:
        form = CommandeForm(initial={'livreur': livreur} if livreur else None)
        formset = LigneCommandeFormSet()

    return render(request, 'gestion/commandes/form.html', {
        'form': form,
        'formset': formset,
        'livreur': livreur,
    })


class CommandeDetailView(DetailView):
    model = CommandeLivreur
    template_name = 'gestion/commandes/detail.html'
    context_object_name = 'commande'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['livreur'] = self.object.livreur 
        # Vous pouvez ajouter d'autres données au contexte ici si nécessaire
        return context



def image_to_base64(image_path):
    """Convertit une image en base64 pour l'intégration directe dans le HTML"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        extension = os.path.splitext(image_path)[1][1:]  # 'png' ou 'jpg'
        return f"data:image/{extension};base64,{encoded_string}"
    except Exception as e:
        print(f"Erreur lors de la conversion de l'image: {e}")
        return None

def get_image_path(filename):
    """Retourne le chemin absolu de l'image"""
    # Déterminer le répertoire static
    static_dir = os.path.join(settings.BASE_DIR, 'static', 'gestion', 'images')
    
    # Crée le répertoire s'il n'existe pas
    os.makedirs(static_dir, exist_ok=True)
    
    # Essaye différentes extensions
    for ext in ['.png', '.jpg', '.jpeg']:
        path = os.path.join(static_dir, f"{filename}{ext}")
        if os.path.exists(path):
            return path
    
    # Si aucune image n'est trouvée, essayer dans STATIC_ROOT si défini
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        static_root_dir = os.path.join(settings.STATIC_ROOT, 'gestion', 'images')
        for ext in ['.png', '.jpg', '.jpeg']:
            path = os.path.join(static_root_dir, f"{filename}{ext}")
            if os.path.exists(path):
                return path
    
    return None

def generer_facture_livreur(request, livreur_id):
    """Génère la facture PDF pour un livreur"""
    try:
        # Récupération du livreur
        livreur = get_object_or_404(Livreur, pk=livreur_id)
        
        # Gestion des paramètres month/year
        month = request.GET.get('month')
        year = request.GET.get('year', datetime.now().year)
        
        try:
            year = int(year)
            if month:
                month = int(month)
                selected_month_name = month_name[month]
            else:
                selected_month_name = "Tous les mois"
        except (ValueError, TypeError):
            month = None
            year = datetime.now().year
            selected_month_name = "Tous les mois"
        
        # Filtrage des commandes
        commandes = CommandeLivreur.objects.filter(livreur=livreur)
        if month and year:
            commandes = commandes.filter(
                date__year=year,
                date__month=month
            )
        
        # Calcul des totaux
        total_commandes_livreur = commandes.aggregate(total=Sum('total'))['total'] or 0
        total_paye = commandes.filter(payee=True).aggregate(total=Sum('total'))['total'] or 0
        total_impaye = total_commandes_livreur - total_paye
        
        # Création des données pour le QR code
        qr_data = f"Facture Livreur: {livreur.nom}\n"
        qr_data += f"Période: {selected_month_name} {year}\n"
        qr_data += f"Total: {total_commandes_livreur} FCFA\n"
        qr_data += f"Boulangerie Epi D'Or\nAngre Château\n01 03 41 96 90"

        # Chemins des images
        logo_path = get_image_path('logo')
        signature_path = get_image_path('signature')

        # Convertir les images en base64
        logo_b64 = image_to_base64(logo_path)
        signature_b64 = image_to_base64(signature_path)

        # Création du contexte
        context = {
            'livreur': livreur,
            'commandes': commandes,
            'total_commandes_livreur': total_commandes_livreur,
            'total_paye': total_paye,
            'total_impaye': total_impaye,
            'selected_month': month,
            'selected_month_name': selected_month_name,
            'selected_year': year,
            'qr_data': qr_data,
            'logo_b64': logo_b64,
            'signature_b64': signature_b64,
            'debug': settings.DEBUG,
        }

        # Génération du PDF
        html = render_to_string('gestion/commandes/facture_livreur.html', context)
        response = HttpResponse(content_type='application/pdf')
        filename = f"facture_{livreur.nom}_{selected_month_name}_{year}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Création du PDF avec gestion des erreurs
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8',
            link_callback=lambda uri, _: uri  # Important pour les images
        )
        
        if pisa_status.err:
            return HttpResponse('Erreur lors de la génération du PDF', status=500)
        return response

    except Exception as e:
        return HttpResponse(f'Erreur lors de la génération de la facture: {str(e)}', status=500)

class CommandeListView(ListView):
    model = CommandeLivreur
    template_name = 'gestion/commandes/liste.html'
    context_object_name = 'commandes'
    paginate_by = 10

    def get_queryset(self):
        livreur_id = self.kwargs.get('livreur_id')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year', datetime.now().year)
        
        queryset = super().get_queryset()
        
        if livreur_id:
            self.template_name = 'gestion/commandes/detail.html'
            queryset = queryset.filter(livreur_id=livreur_id)
            
            if month:
                queryset = queryset.filter(date__month=month, date__year=year)
        
        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        livreur_id = self.kwargs.get('livreur_id')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year', datetime.now().year)
        
        # Liste des mois pour le select
        months = [{'value': str(i), 'name': month_name[i]} for i in range(1, 13)]
        
        # Liste des années disponibles
        years = range(datetime.now().year - 5, datetime.now().year + 1)
        
        if livreur_id:
            livreur = get_object_or_404(Livreur, pk=livreur_id)
            commandes = self.get_queryset()
            
            total_commandes_livreur = commandes.aggregate(total=Sum('total'))['total'] or 0
            total_paye = commandes.filter(payee=True).aggregate(total=Sum('total'))['total'] or 0
            total_impaye = total_commandes_livreur - total_paye
            
            context.update({
                'livreur': livreur,
                'total_commandes_livreur': total_commandes_livreur,
                'total_paye': total_paye,
                'total_impaye': total_impaye,
                'selected_month': month,
                'selected_month_name': month_name[int(month)] if month else None,
                'selected_year': year,
                'months': months,
                'years': reversed(years),
            })
        
        if not livreur_id:
            livreurs_stats = Livreur.objects.annotate(
                nb_commandes=Count('commandelivreur'),
                total_commandes=Sum('commandelivreur__total')
            ).order_by('-nb_commandes')
            context['livreurs_stats'] = livreurs_stats
        
        return context

def marquer_commande_payee(request, pk):
    commande = get_object_or_404(CommandeLivreur, pk=pk)
    
    if request.method == 'POST':
        form = PaiementCommandeForm(request.POST, instance=commande)
        if form.is_valid():
            commande = form.save(commit=False)
            commande.payee = True
            commande.date_paiement = timezone.now()
            commande.save()
            
            # Ajoutez ce message
            messages.success(request, f"Le paiement de la commande #{commande.id} a été enregistré avec succès")
            
            # Redirigez vers la page de détail de la commande
            return redirect('commande_detail', pk=commande.pk)
    else:
        form = PaiementCommandeForm(instance=commande)
    
    return render(request, 'gestion/commandes/confirmation_paiement.html', {
        'commande': commande,
        'form': form
    })

def bilan_periodique(request, periode='jour'):
    aujourdhui = timezone.now().date()
    context = {'periode': periode}
    
    date_debut = aujourdhui
    date_fin = aujourdhui
    titre = "Bilan Journalier"
    
    if periode == 'semaine':
        date_debut = aujourdhui - timedelta(days=aujourdhui.weekday())
        date_fin = date_debut + timedelta(days=6)
        titre = "Bilan Hebdomadaire"
    elif periode == 'mois':
        date_debut = aujourdhui.replace(day=1)
        date_fin = (date_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        titre = "Bilan Mensuel"
    elif periode == 'annee':
        date_debut = aujourdhui.replace(month=1, day=1)
        date_fin = aujourdhui.replace(month=12, day=31)
        titre = "Bilan Annuel"
    elif periode != 'jour':
        return HttpResponse("Période non reconnue", status=400)
    
    ventes = Vente.objects.filter(date__date__gte=date_debut, date__date__lte=date_fin)
    total_ventes = ventes.aggregate(total=Sum('montant_total'))['total'] or 0
    
    context.update({
        'titre': titre,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'total_ventes': total_ventes,
    })
    
    return render(request, 'gestion/bilans/bilan_periodique.html', context)

def generer_bilan_pdf(request, periode):
    context = bilan_periodique(request, periode).context_data
    
    html_string = render_to_string('gestion/bilans/pdf_bilan.html', context)
    
    response = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), response)
    
    if not pdf.err:
        response_http = HttpResponse(response.getvalue(), content_type='application/pdf')
        filename = f"bilan_{periode}_{context['date_debut']}_au_{context['date_fin']}.pdf"
        response_http['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response_http
    
    return HttpResponse("Erreur lors de la génération du PDF", status=400)

def liste_entrees_stock(request):
    entrees = EntreeStock.objects.select_related('produit').order_by('-date')
    return render(request, 'gestion/stock/liste_entrees.html', {'entrees': entrees})

def ajouter_entree_stock(request):
    if request.method == 'POST':
        form = EntreeStockForm(request.POST)
        if form.is_valid():
            entree = form.save(commit=False)
            entree.responsable = request.user.username
            entree.save()
            return redirect('liste_entrees_stock')
    else:
        form = EntreeStockForm()
    
    return render(request, 'gestion/stock/form_entree.html', {'form': form})

def dashboard(request):
    aujourdhui = timezone.now().date()
    
    stats = {
        'ventes_jour': Vente.objects.filter(date__date=aujourdhui).aggregate(total=Sum('montant_total'))['total'] or 0,
        'commandes_jour': CommandeLivreur.objects.filter(date__date=aujourdhui).count(),
        'produits_vendus': LigneVente.objects.filter(vente__date__date=aujourdhui).aggregate(total=Sum('quantite'))['total'] or 0,
        'ventes_semaine': Vente.objects.filter(
            date__date__gte=aujourdhui - timedelta(days=7),
            date__date__lte=aujourdhui
        ).aggregate(total=Sum('montant_total'))['total'] or 0,
    }
    
    sections = {
        'top_produits': LigneVente.objects.filter(
            vente__date__date__gte=aujourdhui - timedelta(days=7)
        ).values('produit__nom').annotate(
            total=Sum(F('quantite') * F('prix_unitaire')),
            quantite=Sum('quantite')
        ).order_by('-total')[:10],
        
        'alertes_stock': Produit.objects.filter(stock__lte=5),
        
        'commandes_attente': CommandeLivreur.objects.filter(payee=False)
                                 .order_by('-date')[:10],
        
        'bilans': [
            {'periode': 'jour', 'nom': 'Journalier'},
            {'periode': 'semaine', 'nom': 'Hebdomadaire'}, 
            {'periode': 'mois', 'nom': 'Mensuel'},
            {'periode': 'annee', 'nom': 'Annuel'}
        ]
    }
    
    context = {
        'stats': stats,
        'sections': sections,
        'aujourdhui': aujourdhui.strftime("%d/%m/%Y")
    }
    
    return render(request, 'gestion/dashboard.html', context)