
# gestion/models.py
from django.db import models
from django.utils import timezone 
# Create your models here.

class Poste(models.Model):
    nom = models.CharField(max_length=100)
    remuneration = models.DecimalField(max_digits=8, decimal_places=2)
    mode_paiement = models.CharField(choices=[('jour', 'Jour'), ('semaine', 'Semaine'), ('mois', 'Mois')], max_length=10)

    def __str__(self):
        return f"{self.nom} ({self.remuneration} {self.get_mode_paiement_display()})"
    
    class Meta:
        ordering = ['nom']  # Pour un ordre cohérent

class Ouvrier(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom")
    telephone = models.CharField(max_length=20, unique=True, verbose_name="Téléphone")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nom'],
                name='unique_nom_ouvrier',
                condition=models.Q(nom__isnull=False),
                violation_error_message="Un ouvrier avec ce nom existe déjà"
            ),
            models.UniqueConstraint(
                fields=['telephone'],
                name='unique_telephone_ouvrier',
                violation_error_message="Un ouvrier avec ce numéro existe déjà"
            )
        ]
        ordering = ['nom']
    
    def save(self, *args, **kwargs):
        # Normalisation des données avant sauvegarde
        self.nom = self.nom.strip().upper() if self.nom else None
        self.telephone = self.telephone.strip() if self.telephone else None
        super().save(*args, **kwargs)


class AffectationPoste(models.Model):
    ouvrier = models.ForeignKey(Ouvrier, on_delete=models.CASCADE)
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)


class Livreur(models.Model):
    nom = models.CharField(max_length=100, unique=True)  # Ajout de unique=True
    telephone = models.CharField(max_length=20, blank=True, null=True, unique=True)  # Ajout de unique=True
    actif = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Livreur"
        verbose_name_plural = "Livreurs"
        constraints = [
            models.UniqueConstraint(fields=['nom', 'telephone'], name='unique_livreur')
        ]

    class Meta:
        verbose_name = "Livreur"
        verbose_name_plural = "Livreurs"

class Produit(models.Model):
    nom = models.CharField(max_length=100)
    prix_vente = models.DecimalField(max_digits=6, decimal_places=2)
    prix_livreur = models.DecimalField(max_digits=6, decimal_places=2)
    actif = models.BooleanField(default=True)
    # Utilise PositiveIntegerField, mais la vérification avant la sauvegarde est cruciale
    stock = models.PositiveIntegerField(default=0) # Ajoute un default si tu ne l'as pas déjà

    def __str__(self):
        return self.nom

# models.py
class CommandeLivreur(models.Model):
    livreur = models.ForeignKey(Livreur, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payee = models.BooleanField(default=False)
    date_paiement = models.DateTimeField(null=True, blank=True)
    mode_paiement = models.CharField(
        max_length=10, 
        choices=[('espece', 'Espèces'), ('mobile', 'Mobile Money'), ('virement', 'Virement')],
        null=True, blank=True
    )
    
    def save(self, *args, **kwargs):
        if self.payee and not self.date_paiement:
            self.date_paiement = timezone.now()
        super().save(*args, **kwargs)

class EntreeStock(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    prix_achat = models.DecimalField(max_digits=8, decimal_places=2)
    fournisseur = models.CharField(max_length=100, blank=True, null=True)
    responsable = models.CharField(max_length=100)  # Personne qui a fait l'entrée
    
    def save(self, *args, **kwargs):
        # Mise à jour du stock
        self.produit.stock += self.quantite
        self.produit.save()
        super().save(*args, **kwargs)


class LigneCommande(models.Model):
    commande = models.ForeignKey(CommandeLivreur, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)  # Non nullable
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
    
    def save(self, *args, **kwargs):
        if not self.prix_unitaire and self.produit:  # Vérifiez que produit existe
            self.prix_unitaire = self.produit.prix_livreur
        super().save(*args, **kwargs)
    
    @property
    def total_ligne(self):
        return self.quantite * self.prix_unitaire
    
    def __str__(self):
        return f"{self.produit.nom} x{self.quantite} à {self.prix_unitaire} FCFA"

# Dans models.py
class Vente(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    # Ajoutez d'autres champs nécessaires

class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=8, decimal_places=2)

class PaiementSalaire(models.Model):
    ouvrier = models.ForeignKey(Ouvrier, on_delete=models.CASCADE)
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    date_paiement = models.DateTimeField(auto_now_add=True)
    mode_paiement = models.CharField(
        max_length=10,
        choices=[('espece', 'Espèces'), ('mobile', 'Mobile Money'), ('virement', 'Virement')]
    )

    def __str__(self):
        return f"Paiement {self.ouvrier.nom} - {self.periode_debut} à {self.periode_fin}"

    class Meta:
        verbose_name = "Paiement de salaire"
        verbose_name_plural = "Paiements de salaires"