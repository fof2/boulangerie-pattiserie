from django.views.generic import ListView, TemplateView
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q, F, FloatField
from django.db.models.expressions import ExpressionWrapper
from django.shortcuts import redirect
from .models import Presence, Ouvrier, Poste, AffectationPoste

class MarquerPresenceView(TemplateView):
    template_name = 'gestion/marquer_presence.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.request.GET.get('date', timezone.localdate().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = timezone.localdate()
        
        # CORRECTION ICI - Syntaxe corrigée pour la requête Q
        affectations = AffectationPoste.objects.filter(
            Q(date_debut__lte=date) & 
            (Q(date_fin__gte=date) | Q(date_fin__isnull=True))
        ).select_related('ouvrier', 'poste')
        
        # Créer un dictionnaire ouvrier -> poste
        postes_par_ouvrier = {a.ouvrier_id: a.poste for a in affectations}
        
        # Récupérer les présences existantes
        presences = Presence.objects.filter(date=date).select_related('ouvrier')
        presences_dict = {p.ouvrier_id: p for p in presences}
        
        # Préparer les données pour le template
        ouvriers_data = []
        for ouvrier in Ouvrier.objects.all().order_by('nom'):
            presence = presences_dict.get(ouvrier.id)
            poste = postes_par_ouvrier.get(ouvrier.id)
            
            ouvriers_data.append({
                'ouvrier': ouvrier,
                'presence': presence,
                'poste_affecte': poste
            })
        
        context.update({
            'date': date,
            'ouvriers_data': ouvriers_data,
            'postes': Poste.objects.all()
        })
        return context

    def post(self, request):
        date_str = request.POST.get('date', timezone.localdate().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = timezone.localdate()
        
        for ouvrier in Ouvrier.objects.all():
            presence_id = request.POST.get(f'presence_{ouvrier.id}')
            present = request.POST.get(f'present_{ouvrier.id}') == 'on'
            heures = float(request.POST.get(f'heures_{ouvrier.id}', 8.0))
            poste_id = request.POST.get(f'poste_{ouvrier.id}')
            
            if presence_id:
                presence = Presence.objects.get(id=presence_id)
                presence.present = present
                presence.heures_travaillees = heures
                presence.poste_id = poste_id if poste_id else None
                presence.save()
            else:
                Presence.objects.update_or_create(
                    ouvrier=ouvrier,
                    date=date,
                    defaults={
                        'present': present,
                        'heures_travaillees': heures,
                        'poste_id': poste_id if poste_id else None
                    }
                )
        
        return redirect('marquer_presences')

class StatsPresenceView(ListView):
    template_name = 'gestion/stats_presence.html'
    context_object_name = 'stats'
    
    def get_queryset(self):
        period = self.request.GET.get('period', 'day')
        date_str = self.request.GET.get('date', timezone.localdate().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = timezone.localdate()
        
        if period == 'day':
            start_date = end_date = date
        elif period == 'month':
            start_date = date.replace(day=1)
            end_date = (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        elif period == 'year':
            start_date = date.replace(month=1, day=1)
            end_date = date.replace(month=12, day=31)
        
        return Presence.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values('ouvrier__id', 'ouvrier__nom').annotate(
            jours_presents=Count('id', filter=Q(present=True)),
            heures_total=Sum('heures_travaillees', filter=Q(present=True)),
            taux_presence=ExpressionWrapper(
                Count('id', filter=Q(present=True)) * 100.0 / Count('id'),
                output_field=FloatField()
            )
        ).order_by('-jours_presents')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'day')
        date_str = self.request.GET.get('date', timezone.localdate().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = timezone.localdate()
        
        context['period'] = period
        context['selected_date'] = date_str
        
        if period == 'month':
            context['previous_period'] = (date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
            context['next_period'] = (date.replace(day=28) + timedelta(days=4)).strftime('%Y-%m-%d')
        elif period == 'year':
            context['previous_period'] = date.replace(year=date.year-1).strftime('%Y-%m-%d')
            context['next_period'] = date.replace(year=date.year+1).strftime('%Y-%m-%d')
        
        return context