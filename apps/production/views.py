# apps/production/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    SearchFilterBackend, FilteringFilterBackend, OrderingFilterBackend,
    GeoSpatialFilteringFilterBackend, GeoSpatialOrderingFilterBackend
)
from .models import Production, Commande, Paiement, Evaluation, PhotoProduction
from .serializers import (
    ProductionListSerializer, ProductionDetailSerializer, 
    ProductionCreateWithRoleSerializer, CommandeSerializer,
    PaiementSerializer, EvaluationSerializer, PhotoProductionSerializer
)
from .documents import ProductionDocument
from .permissions import IsProducteurOrReadOnly, IsCommandeOwner, CanBecomeProducteur, IsProducteurOwner
from apps.users.models import Producteur
from .docs.production_swagger import (
    LIST_COMMANDES_SCHEMA, CREATE_COMMANDE_SCHEMA, CREATE_PRODUCTION_SCHEMA,
    NEARBY_PRODUCTIONS_SCHEMA, UPLOAD_PHOTO_SCHEMA, SEARCH_PRODUCTIONS_SCHEMA,
    LIST_PRODUCTIONS_SCHEMA, CONFIRM_COMMANDE_SCHEMA, CANCEL_COMMANDE_SCHEMA,
    SHIP_COMMANDE_SCHEMA, DELIVER_COMMANDE_SCHEMA, INITIATE_PAIEMENT_SCHEMA,
    CALLBACK_PAIEMENT_SCHEMA, CREATE_EVALUATION_SCHEMA,
)
from drf_spectacular.utils import extend_schema


class ProductionViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les productions avec activation automatique du rôle producteur"""
    permission_classes = [IsAuthenticated, CanBecomeProducteur]
    
    def get_queryset(self):
        return Production.objects.select_related(
            'producteur__user'
        ).prefetch_related('photos').all()
    
    def get_serializer_class(self):
        # Pour la création uniquement
        if self.action == 'create':
            # Si pas encore producteur, utiliser le serializer avec champs producteur
            if not self.request.user.is_producteur:
                return ProductionCreateWithRoleSerializer
            # Si déjà producteur, utiliser le serializer normal
            return ProductionDetailSerializer
        
        # Pour les autres actions (list, retrieve, update)
        return ProductionDetailSerializer if self.action == 'retrieve' else ProductionListSerializer
        
    def get_permissions(self):
        """Permissions personnalisées selon l'action"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsProducteurOwner()]
        return [IsAuthenticated(), CanBecomeProducteur()]
    
    @extend_schema(
        operation_id="my_productions",
        summary="Mes productions",
        description="Liste des productions créées par l'utilisateur connecté (producteur uniquement)",
        responses={
            200: ProductionListSerializer(many=True),
            403: {'description': 'Vous devez être producteur'}
        },
        tags=['Productions']
    )
    @action(detail=False, methods=['get'])
    def mine(self, request):
        """Liste des productions de l'utilisateur connecté"""
        # Vérifier si l'utilisateur est producteur
        if not request.user.is_producteur or not hasattr(request.user, 'producteur'):
            return Response(
                {'error': 'Vous devez être producteur pour accéder à cette ressource'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filtrer les productions du producteur connecté
        my_productions = Production.objects.filter(
            producteur=request.user.producteur
        ).select_related('producteur__user').prefetch_related('photos')
        
        # Paginer les résultats
        page = self.paginate_queryset(my_productions)
        if page is not None:
            serializer = ProductionListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductionListSerializer(my_productions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @LIST_PRODUCTIONS_SCHEMA
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @CREATE_PRODUCTION_SCHEMA
    def create(self, request, *args, **kwargs):
        """Création de production avec activation automatique du rôle producteur"""
        # Vérification profil complété
        if not request.user.profile_completed:
            return Response(
                {'error': 'Complétez votre profil (nom, prénom, téléphone, adresse) avant de vendre'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si pas encore producteur, activer avec les champs fournis
        if not request.user.is_producteur:
            serializer = ProductionCreateWithRoleSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                # Extraction des données pour le profil producteur
                type_production = serializer.validated_data.pop('type_production')
                superficie = serializer.validated_data.pop('superficie', None)
                certification = serializer.validated_data.pop('certification', '')
                
                # Activation rôle producteur
                request.user.activate_role('producteur')
                
                # Création profil producteur
                producteur = Producteur.objects.create(
                    user=request.user,
                    type_production=type_production,
                    superficie=superficie,
                    certification=certification
                )
                
                # Création production
                production = Production.objects.create(
                    producteur=producteur,
                    **serializer.validated_data
                )
                
            return Response(
                ProductionDetailSerializer(production).data,
                status=status.HTTP_201_CREATED
            )
        
        # ✅ Si déjà producteur : utiliser get_serializer() qui appellera get_serializer_class()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            ProductionDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        """Méthode appelée après validation pour sauvegarder"""
        serializer.save(producteur=self.request.user.producteur)    
    
    @NEARBY_PRODUCTIONS_SCHEMA
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Recherche productions par proximité GPS"""
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
        """Upload photo production (max 5 par production)"""
        production = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire
        if production.producteur.user != request.user:
            return Response({'error': 'Non autorisé'}, status=403)
        
        if production.photos.count() >= 5:
            return Response({'error': 'Maximum 5 photos'}, status=400)
        
        serializer = PhotoProductionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(production=production, ordre=production.photos.count())
        
        return Response(serializer.data, status=201)
class ProductionSearchViewSet(DocumentViewSet):
    """Recherche avancée avec Elasticsearch"""
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
    """Gestion des commandes"""
    serializer_class = CommandeSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsCommandeOwner()]
    
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
        commande = serializer.save(client=self.request.user)
        
        # Notification producteur
        from apps.notifications.services import NotificationService
        NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type='new_order',
            title='Nouvelle commande reçue',
            message=f'{commande.client.get_full_name()} - {commande.quantite} {commande.production.produit}',
            content_object=commande,
            data={'order_id': commande.id, 'amount': float(commande.montant_total)}
        )
    
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
        NotificationService.create(
            recipient=commande.client,
            notif_type='order_confirmed',
            title='Commande confirmée',
            message=f'Votre commande #{commande.id} a été confirmée',
            content_object=commande
        )
        
        return Response({'status': 'confirmée'})
    
    @CANCEL_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'annulee'
        commande.save()
        
        from apps.notifications.services import NotificationService
        # Notifier l'autre partie
        other_user = commande.production.producteur.user if request.user == commande.client else commande.client
        NotificationService.create(
            recipient=other_user,
            notif_type='order_cancelled',
            title='Commande annulée',
            message=f'Commande #{commande.id} annulée par {request.user.get_full_name()}',
            content_object=commande
        )
        
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
        NotificationService.create(
            recipient=commande.client,
            notif_type='product_shipped',
            title='Produit expédié',
            message=f'Votre commande #{commande.id} a été expédiée',
            content_object=commande
        )
        
        return Response({'status': 'expédiée'})
    
    @DELIVER_COMMANDE_SCHEMA
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'livree'
        commande.date_livraison = timezone.now()
        commande.save()
        
        from apps.notifications.services import NotificationService
        
        # Notification client
        NotificationService.create(
            recipient=commande.client,
            notif_type='delivery_completed',
            title='Livraison effectuée',
            message=f'Votre commande #{commande.id} a été livrée',
            content_object=commande
        )
        
        # Notification producteur
        NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type='delivery_completed',
            title='Livraison effectuée',
            message=f'Commande #{commande.id} livrée au client',
            content_object=commande
        )
        
        return Response({'status': 'livrée'})
class PaiementViewSet(viewsets.ModelViewSet):
    """Gestion des paiements"""
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Paiement.objects.filter(commande__client=self.request.user)
    
    @INITIATE_PAIEMENT_SCHEMA
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initier paiement mobile money"""
        return Response({'message': 'Paiement initié'}, status=201)
    
    @CALLBACK_PAIEMENT_SCHEMA
    @action(detail=False, methods=['post'])
    def callback(self, request):
        """Webhook mobile money"""
        return Response({'status': 'received'})


class EvaluationViewSet(viewsets.ModelViewSet):
    """Gestion des évaluations"""
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Evaluation.objects.filter(commande__client=self.request.user)
    
    @CREATE_EVALUATION_SCHEMA
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        evaluation = serializer.save()
        
        # ✅ CORRECTION : Utiliser NotificationService.create() directement
        from apps.notifications.services import NotificationService
        NotificationService.create(
            recipient=evaluation.commande.production.producteur.user,  # Accès via commande → production → producteur
            notif_type='new_review',
            title='Nouvelle évaluation',
            message=f'{evaluation.note}/5 étoiles - {evaluation.commentaire[:50]}',
            content_object=evaluation,
            data={'rating': evaluation.note}
        )