# apps/production/views.py
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Production, Commande, Paiement, Evaluation, PhotoProduction
from .serializers import (
    ProductionListSerializer, 
    ProductionDetailSerializer, 
    ProductionCreateWithRoleSerializer,
    CommandeSerializer,
    PaiementSerializer, 
    EvaluationSerializer, 
    PhotoProductionSerializer
)
from .permissions import IsProducteurOrReadOnly, IsCommandeOwner, CanBecomeProducteur
from apps.users.models import Producteur


class ProductionListCreateView(generics.ListCreateAPIView):
    """
    Liste des productions (GET) ou création avec activation automatique producteur (POST)
    """
    permission_classes = [IsAuthenticated, CanBecomeProducteur]
    
    def get_queryset(self):
        return Production.objects.select_related(
            'producteur__user'
        ).prefetch_related('photos').filter(disponible=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST' and not self.request.user.is_producteur:
            return ProductionCreateWithRoleSerializer
        return ProductionListSerializer if self.request.method == 'GET' else ProductionDetailSerializer
    
    def create(self, request, *args, **kwargs):
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
                # Activation rôle producteur
                request.user.activate_role('producteur')
                
                # Création profil producteur
                producteur = Producteur.objects.create(
                    user=request.user,
                    type_production=serializer.validated_data.pop('type_production'),
                    superficie=serializer.validated_data.pop('superficie', None),
                    certification=serializer.validated_data.pop('certification', '')
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
        
        # Si déjà producteur, création normale
        serializer = ProductionDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(producteur=request.user.producteur)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression production"""
    queryset = Production.objects.all()
    serializer_class = ProductionDetailSerializer
    permission_classes = [IsAuthenticated, IsProducteurOwner]
    
    def get_queryset(self):
        return super().get_queryset().select_related('producteur__user')


class ProductionNearbyListView(generics.ListAPIView):
    """Recherche productions par proximité GPS"""
    serializer_class = ProductionListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        radius = float(self.request.query_params.get('radius', 10))
        
        if not (lat and lon):
            return Production.objects.none()
        
        lat, lon = float(lat), float(lon)
        
        # Filtrage par distance Haversine
        productions = []
        for p in Production.objects.filter(disponible=True):
            if self._haversine_distance(lat, lon, float(p.latitude), float(p.longitude)) <= radius:
                productions.append(p.id)
        
        return Production.objects.filter(id__in=productions)
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        from math import radians, cos, sin, asin, sqrt
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return 6371 * c


class CommandeListCreateView(generics.ListCreateAPIView):
    """Liste et création de commandes"""
    serializer_class = CommandeSerializer
    permission_classes = [IsAuthenticated, IsCommandeOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_producteur and hasattr(user, 'producteur'):
            # Producteur voit ses ventes
            return Commande.objects.filter(
                production__producteur=user.producteur
            ).select_related('production__producteur__user', 'client')
        # Client voit ses achats
        return user.commandes_production.select_related('production__producteur__user')
    
    def perform_create(self, serializer):
        commande = serializer.save(client=self.request.user)
        
        # Notification producteur
        from apps.notifications.services import NotificationService
        NotificationService.notify_producteur_new_order(commande)


class CommandeRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Détail et actions sur commande"""
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    permission_classes = [IsAuthenticated, IsCommandeOwner]
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        commande = self.get_object()
        
        if not request.user.is_producteur:
            return Response({'error': 'Producteur uniquement'}, status=403)
        
        commande.statut = 'confirmee'
        commande.save(update_fields=['statut', 'date_confirmation'])
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_consommateur_order_confirmed(commande)
        
        return Response({'status': 'confirmée'})
    
    @action(detail=True, methods=['post']) 
    def cancel(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'annulee'
        commande.save(update_fields=['statut'])
        
        from apps.notifications.services import NotificationService
        NotificationService.notify_order_cancelled(commande, request.user)
        
        return Response({'status': 'annulée'})


class EvaluationCreateView(generics.CreateAPIView):
    """Créer une évaluation après livraison"""
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        evaluation = serializer.save()
        
        # Notification producteur
        from apps.notifications.services import NotificationService
        NotificationService.notify_producteur_review(evaluation)