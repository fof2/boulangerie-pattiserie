from django.contrib import admin
from django.utils import timezone
from .models import (
    Poste, Ouvrier, AffectationPoste,
    Livreur, Produit, CommandeLivreur, 
    LigneCommande, EntreeStock, Vente,
    LigneVente, PaiementSalaire
)

# Configuration pour les affectations de poste
class AffectationPosteInline(admin.TabularInline):
    model = AffectationPoste
    extra = 1
    fields = ('poste', 'date_debut', 'date_fin')
    autocomplete_fields = ['poste']

# Configuration pour les lignes de vente
class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 1
    autocomplete_fields = ['produit']

# Configuration pour les lignes de commande
class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1
    fields = ('produit', 'quantite', 'prix_unitaire', 'total_ligne')
    readonly_fields = ('total_ligne',)
    autocomplete_fields = ['produit']
    
    def total_ligne(self, instance):
        return instance.total_ligne
    total_ligne.short_description = 'Total ligne'

@admin.register(Ouvrier)
class OuvrierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'poste_actuel')
    search_fields = ('nom', 'telephone')
    list_filter = ('affectationposte__poste',)
    inlines = [AffectationPosteInline]
    
    def poste_actuel(self, obj):
        return obj.affectationposte_set.latest('date_debut').poste if obj.affectationposte_set.exists() else None
    poste_actuel.short_description = 'Poste actuel'

@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'remuneration', 'mode_paiement')
    list_filter = ('mode_paiement',)
    search_fields = ('nom',)

@admin.register(Livreur)
class LivreurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'actif', 'total_commandes')
    list_filter = ('actif',)
    search_fields = ('nom', 'telephone')
    actions = ['activer_livreurs', 'desactiver_livreurs']
    
    def total_commandes(self, obj):
        return obj.commandelivreur_set.count()
    total_commandes.short_description = 'Commandes'
    
    def activer_livreurs(self, request, queryset):
        queryset.update(actif=True)
    activer_livreurs.short_description = "Activer les livreurs sélectionnés"
    
    def desactiver_livreurs(self, request, queryset):
        queryset.update(actif=False)
    desactiver_livreurs.short_description = "Désactiver les livreurs sélectionnés"

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix_vente', 'prix_livreur', 'stock', 'actif')
    list_editable = ('prix_vente', 'prix_livreur', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom',)
    actions = ['activer_produits', 'desactiver_produits']

    def activer_produits(self, request, queryset):
        queryset.update(actif=True)
    activer_produits.short_description = "Activer les produits sélectionnés"
    
    def desactiver_produits(self, request, queryset):
        queryset.update(actif=False)
    desactiver_produits.short_description = "Désactiver les produits sélectionnés"

@admin.register(CommandeLivreur)
class CommandeLivreurAdmin(admin.ModelAdmin):
    list_display = ('id', 'livreur', 'date', 'total', 'payee', 'mode_paiement')
    list_filter = ('payee', 'date', 'mode_paiement')
    search_fields = ('livreur__nom', 'id')
    inlines = [LigneCommandeInline]
    readonly_fields = ('total',)
    fieldsets = (
        (None, {
            'fields': ('livreur', 'date', 'payee')
        }),
        ('Paiement', {
            'fields': ('mode_paiement', 'date_paiement', 'total'),
            'classes': ('collapse',)
        }),
    )
    actions = ['marquer_comme_payee']

    def marquer_comme_payee(self, request, queryset):
        queryset.update(payee=True, date_paiement=timezone.now())
    marquer_comme_payee.short_description = "Marquer comme payée"

@admin.register(EntreeStock)
class EntreeStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite', 'prix_achat', 'date', 'fournisseur')
    list_filter = ('date', 'fournisseur')
    search_fields = ('produit__nom', 'responsable')
    date_hierarchy = 'date'
    autocomplete_fields = ['produit']

@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'montant_total')
    date_hierarchy = 'date'
    inlines = [LigneVenteInline]

@admin.register(PaiementSalaire)
class PaiementSalaireAdmin(admin.ModelAdmin):
    list_display = ('ouvrier', 'poste', 'periode_debut', 'periode_fin', 'montant')
    list_filter = ('poste', 'mode_paiement')
    search_fields = ('ouvrier__nom',)
    date_hierarchy = 'date_paiement'