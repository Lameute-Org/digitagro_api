from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductionViewSet, ProductionSearchViewSet, CommandeViewSet,
    PaiementViewSet, EvaluationViewSet
)

router = DefaultRouter()
router.register(r'productions', ProductionViewSet, basename='production')
router.register(r'productions-search', ProductionSearchViewSet, basename='production-search')
router.register(r'commandes', CommandeViewSet, basename='commande')
router.register(r'paiements', PaiementViewSet, basename='paiement')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')

urlpatterns = router.urls

