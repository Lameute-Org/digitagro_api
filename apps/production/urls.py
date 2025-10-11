# apps/production/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductionViewSet, ProductionSearchViewSet, CommandeViewSet,
    PaiementViewSet, EvaluationViewSet
)

router = DefaultRouter()

# ⚠️ IMPORTANT : Routes spécifiques EN PREMIER
router.register(r'commandes', CommandeViewSet, basename='commande')
router.register(r'paiements', PaiementViewSet, basename='paiement')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')
router.register(r'search', ProductionSearchViewSet, basename='production-search')

# Route générique EN DERNIER
router.register(r'', ProductionViewSet, basename='production')

urlpatterns = router.urls