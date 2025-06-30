from django import forms
from .models import Ouvrier, AffectationPoste, Poste
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, F, Q
from .models import Ouvrier, AffectationPoste, Poste, EntreeStock, CommandeLivreur, Livreur, LigneCommande, Produit
from .models import CommandeLivreur,Livreur,EntreeStock

class OuvrierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = Ouvrier
        fields = ['nom', 'telephone']
        widgets = {
            'telephone': forms.TextInput(attrs={
                'placeholder': 'Format: +0123456789',
                'pattern': r'\+\d{10,15}',  # Validation côté client
                'title': 'Format: + suivi de 10 à 15 chiffres'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        nom = cleaned_data.get('nom')
        telephone = cleaned_data.get('telephone')

        # Vérification des doublons
        queryset = Ouvrier.objects.all()
        if self.instance.pk:  # Si c'est une modification
            queryset = queryset.exclude(pk=self.instance.pk)

        if nom:
            nom = nom.strip().upper()  # Normalisation du nom
            if queryset.filter(nom__iexact=nom).exists():
                self.add_error('nom', "Un ouvrier avec ce nom existe déjà.")

        if telephone:
            telephone = telephone.strip()
            if queryset.filter(telephone=telephone).exists():
                self.add_error('telephone', "Un ouvrier avec ce numéro existe déjà.")

        return cleaned_data
    
class AffectationPosteForm(forms.ModelForm):
    poste = forms.ModelChoiceField(
        queryset=Poste.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Poste occupé"
    )
    
    class Meta:
        model = AffectationPoste
        fields = ['poste', 'date_debut', 'date_fin']
        widgets = {
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_fin and date_debut and date_debut > date_fin:
            self.add_error('date_fin', "La date de fin doit être postérieure ou égale à la date de début.")

        return cleaned_data
# Dans gestion/forms.py
class LivreurForm(forms.ModelForm):
    class Meta:
        model = Livreur
        fields = ['nom', 'telephone', 'actif']
        
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if Livreur.objects.filter(nom__iexact=nom).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Un livreur avec ce nom existe déjà.")
        return nom

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone and Livreur.objects.filter(telephone=telephone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Un livreur avec ce numéro de téléphone existe déjà.")
        return telephone


class CommandeForm(forms.ModelForm):
    class Meta:
        model = CommandeLivreur
        fields = ['livreur']

class PaiementCommandeForm(forms.ModelForm):
    class Meta:
        model = CommandeLivreur
        fields = ['mode_paiement']  # On ne garde que le mode de paiement
        widgets = {
            'mode_paiement': forms.Select(attrs={'class': 'form-control'})
        }

# forms.py
class EntreeStockForm(forms.ModelForm):
    class Meta:
        model = EntreeStock
        fields = ['produit', 'quantite', 'prix_achat', 'fournisseur']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control'}),
            'fournisseur': forms.TextInput(attrs={'class': 'form-control'}),
        }
    

# Ajoutez ceci à votre fichier forms.py
# Dans forms.py
class LigneCommandeForm(forms.ModelForm):
    class Meta:
        model = LigneCommande
        fields = ['produit', 'quantite']
        widgets = {
            'produit': forms.Select(attrs={
                'class': 'form-select produit-select',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control quantite-input',
                'min': '1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produit'].queryset = Produit.objects.filter(actif=True)