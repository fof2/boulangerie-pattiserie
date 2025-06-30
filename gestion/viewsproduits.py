from django.shortcuts import get_object_or_404, redirect
from .models import CommandeLivreur, LigneCommande, Produit
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from xhtml2pdf import pisa
from io import BytesIO
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Produit
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

class ProduitListView(ListView):
    model = Produit
    template_name = 'gestion/produits/liste.html'
    context_object_name = 'produits'

class ProduitCreateView(CreateView):
    model = Produit
    template_name = 'gestion/produits/form.html'
    fields = ['nom', 'prix_vente', 'prix_livreur', 'stock']
    success_url = reverse_lazy('produit_liste')

class ProduitUpdateView(UpdateView):
    model = Produit
    template_name = 'gestion/produits/form.html'
    fields = ['nom', 'prix_vente', 'prix_livreur', 'stock']
    success_url = reverse_lazy('produit_liste')

class ProduitDeleteView(DeleteView):
    model = Produit
    template_name = 'gestion/produits/confirm_delete.html'
    success_url = reverse_lazy('produit_liste')


def ajuster_stock(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    
    if request.method == 'POST':
        quantite = int(request.POST.get('quantite', 0))
        set_absolute = request.POST.get('set_absolute') == 'on'
        
        if set_absolute:
            produit.stock = quantite
        else:
            produit.stock += quantite
        
        produit.save()
        messages.success(request, f"Stock de {produit.nom} mis à jour: {produit.stock} unités")
        return redirect('produit_liste')
    
    return redirect('produit_liste')



def generate_pdf(request):
    template = 'your_template.html'
    context = {'data': 'your_data'}
    
    html = render_to_string(template, context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="document.pdf"'
    
    pisa_status = pisa.CreatePDF(
        BytesIO(html.encode("UTF-8")),
        dest=response
    )
    
    if pisa_status.err:
        return HttpResponse('PDF generation error')
    return response


def marquer_commande_payee(request, pk):
    commande = get_object_or_404(CommandeLivreur, pk=pk)
    
    if not commande.payee:
        commande.payee = True
        commande.save()
        messages.success(request, f"La commande #{commande.id} a été marquée comme payée")
    else:
        messages.warning(request, f"La commande #{commande.id} était déjà payée")
    
    return redirect('commande_detail', pk=commande.pk)