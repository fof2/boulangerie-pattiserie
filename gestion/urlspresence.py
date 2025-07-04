
from django.urls import path
from .viewpresence import MarquerPresenceView, StatsPresenceView

urlpatterns = [
    path('presences/marquer/', MarquerPresenceView.as_view(), name='marquer_presences'),
    path('presences/stats/', StatsPresenceView.as_view(), name='stats_presences'),
    # ... vos autres URLs ...
]