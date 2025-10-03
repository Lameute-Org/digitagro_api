# apps/production/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    SearchFilterBackend, FilteringFilterBackend, OrderingFilterBackend,
    GeoSpatialFilteringFilterBackend, GeoSpatialOrderingFilterBackend
)
from .models import Production, Commande, Paiement, Evaluation, PhotoProduction
from .serializers import (
    ProductionListSerializer, ProductionDetailSerializer, CommandeSerializer,
    PaiementSerializer, EvaluationSerializer, PhotoProductionSerializer
)
from .documents import ProductionDocument
from .permissions import IsProducteurOrReadOnly, IsCommandeOwner
from .docs.production_swagger import (
    LIST_COMMANDES_SCHEMA, 
    CREATE_COMMANDE_SCHEMA,
    CREATE_PRODUCTION_SCHEMA,
    NEARBY_PRODUCTIONS_SCHEMA,
    UPLOAD_PHOTO_SCHEMA,
    SEARCH_PRODUCTIONS_SCHEMA,
    LIST_PRODUCTIONS_SCHEMA,
    CONFIRM_COMMANDE_SCHEMA,
    CANCEL_COMMANDE_SCHEMA,
    SHIP_COMMANDE_SCHEMA,
    DELIVER_COMMANDE_SCHEMA,
    INITIATE_PAIEMENT_SCHEMA,
    CALLBACK_PAIEMENT_SCHEMA,
    CREATE_EVALUATION_SCHEMA,
    
    )
from drf_spectacular.utils import extend_schema



class ProductionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsProducteurOrReadOnly]
    
    def get_queryset(self):

        return Production.objects.select_related(
            'producteur__user'
        ).prefetch_related('photos').all()
    
    def get_serializer_class(self):
        return ProductionDetailSerializer if self.action == 'retrieve' else ProductionListSerializer
    
    def perform_create(self, serializer):
        serializer.save(producteur=self.request.user.producteur)
    
    @LIST_PRODUCTIONS_SCHEMA
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @CREATE_PRODUCTION_SCHEMA
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @NEARBY_PRODUCTIONS_SCHEMA
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = float(request.query_params.get('radius', 10))
        
        if not (lat and lon):
            return Response({'error': 'lat et lon requis'}, status=400)
        
        lat, lon = float(lat), float(lon)
        
        productions = [
            p for p in self.get_queryset().filter(disponible=True)
            if self._haversine_distance(lat, lon, float(p.latitude), float(p.longitude)) <= radius
        ]
        
        serializer = self.get_serializer(productions, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    @UPLOAD_PHOTO_SCHEMA
    @action(detail=True, methods=['post'])
    def upload_photo(self, request, pk=None):
        production = self.get_object()
        
        if production.photos.count() >= 5:
            return Response({'error': 'Maximum 5 photos'}, status=400)
        
        serializer = PhotoProductionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(production=production, ordre=production.photos.count())
        
        return Response(serializer.data, status=201)


class ProductionSearchViewSet(DocumentViewSet):
    document = ProductionDocument
    serializer_class = ProductionListSerializer
    permission_classes = [AllowAny]
    
    filter_backends = [
        SearchFilterBackend,
        FilteringFilterBackend,
        OrderingFilterBackend,
        GeoSpatialFilteringFilterBackend,
        GeoSpatialOrderingFilterBackend,
    ]
    
    search_fields = ('produit', 'description', 'type_production')
    filter_fields = {
        'type_production': 'type_production',
        'certification': 'certification',
        'disponible': 'disponible',
    }
    ordering_fields = {
        'prix_unitaire': 'prix_unitaire',
        'date_creation': 'date_creation',
    }
    geo_spatial_filter_fields = {
        'localisation': {
            'lookups': ['geo_distance'],
        },
    }


class CommandeViewSet(viewsets.ModelViewSet):
    serializer_class = CommandeSerializer
    permission_classes = [IsAuthenticated, IsCommandeOwner]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'producteur'):
            return Commande.objects.filter(
                production__producteur=user.producteur
            ).select_related('production__producteur__user', 'client')
        return user.commandes_production.select_related('production__producteur__user')
    
    @LIST_COMMANDES_SCHEMA
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @CREATE_COMMANDE_SCHEMA
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
        
        from apps.notifications.services import NotificationService
        commande = serializer.instance
        NotificationService.notify_producteur_new_order(commande)
    
    @CONFIRM_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        commande = self.get_object()
        
        if not hasattr(request.user, 'producteur'):
            return Response({'error': 'Producteur uniquement'}, status=403)
        
        commande.statut = 'confirmee'
        commande.date_confirmation = timezone.now()
        commande.save()
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_consommateur_order_confirmed(commande)
        
        return Response({'status': 'confirmée'})
    
    @CANCEL_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'annulee'
        commande.save()
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_order_cancelled(commande, request.user)
        
        return Response({'status': 'annulée'})
    
    @SHIP_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        commande = self.get_object()
        
        if not hasattr(request.user, 'producteur'):
            return Response({'error': 'Producteur uniquement'}, status=403)
        
        commande.statut = 'expediee'
        commande.date_expedition = timezone.now()
        commande.save()
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_consommateur_product_shipped(commande)
        
        return Response({'status': 'expédiée'})
    
    @DELIVER_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'livree'
        commande.date_livraison = timezone.now()
        commande.save()
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_consommateur_delivery_completed(commande)
        NotificationService.notify_producteur_delivery_completed(commande)
        
        return Response({'status': 'livrée'})


class PaiementViewSet(viewsets.ModelViewSet):
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Paiement.objects.filter(commande__client=self.request.user)
    
    @INITIATE_PAIEMENT_SCHEMA
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        return Response({'message': 'Paiement initié'}, status=201)
    
    @CALLBACK_PAIEMENT_SCHEMA
    @action(detail=False, methods=['post'])
    def callback(self, request):
        return Response({'status': 'received'})


class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Evaluation.objects.filter(commande__client=self.request.user)
    
    @CREATE_EVALUATION_SCHEMA
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        evaluation = serializer.save()
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_producteur_review(evaluation)