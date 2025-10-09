# apps/production/serializers.py
from rest_framework import serializers
from rest_framework.validators import ValidationError
from .models import PhotoEvaluation, Production, PhotoProduction, Commande, Paiement, Evaluation


class ProductionCreateWithRoleSerializer(serializers.ModelSerializer):
    """Serializer pour première production avec activation producteur"""
    # Champs producteur requis à la première production
    type_production = serializers.CharField(max_length=100, write_only=True)
    superficie = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True)
    certification = serializers.CharField(max_length=100, required=False, write_only=True, default='standard')
    
    class Meta:
        model = Production
        fields = [
            'produit', 'type_production', 'quantite', 'unite_mesure', 
            'prix_unitaire', 'latitude', 'longitude', 'adresse_complete',
            'date_recolte', 'date_expiration', 'description', 
            'conditions_stockage', 'certification', 'superficie'
        ]
    
    def validate(self, attrs):
        """Vérification que les champs producteur sont présents"""
        if not attrs.get('type_production'):
            raise ValidationError('Le type de production est requis pour devenir producteur')
        return attrs


class PhotoProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoProduction
        fields = ['id', 'image', 'ordre']
        read_only_fields = ['id']


class ProductionListSerializer(serializers.ModelSerializer):
    producteur_nom = serializers.CharField(source='producteur.user.get_full_name', read_only=True)
    photo_principale = serializers.SerializerMethodField()
    note_moyenne = serializers.FloatField(read_only=True)
    quantite_disponible = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Production
        fields = [
            'id', 'produit', 'type_production', 'quantite', 'quantite_disponible',
            'unite_mesure', 'prix_unitaire', 'disponible', 'date_recolte',
            'certification', 'producteur_nom', 'photo_principale', 'note_moyenne',
            'latitude', 'longitude', 'date_creation'
        ]
    
    def get_photo_principale(self, obj):
        photo = obj.photos.first()
        return self.context['request'].build_absolute_uri(photo.image.url) if photo else None


class ProductionDetailSerializer(serializers.ModelSerializer):
    photos = PhotoProductionSerializer(many=True, read_only=True)
    producteur = serializers.SerializerMethodField()
    note_moyenne = serializers.FloatField(read_only=True)
    quantite_disponible = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Production
        fields = '__all__'
        read_only_fields = ['producteur', 'date_creation', 'date_modification']
    
    def get_producteur(self, obj):
        return {
            'id': obj.producteur.user.id,
            'nom': obj.producteur.user.get_full_name(),
            'type_production': obj.producteur.type_production,
            'certification': obj.producteur.certification,
        }


class CommandeSerializer(serializers.ModelSerializer):
    production_info = ProductionListSerializer(source='production', read_only=True)
    client_nom = serializers.CharField(source='client.get_full_name', read_only=True)
    
    class Meta:
        model = Commande
        fields = '__all__'
        read_only_fields = ['client', 'montant_total', 'date_creation', 
                           'date_confirmation', 'date_expedition', 'date_livraison']
    
    def validate(self, attrs):
        production = attrs.get('production')
        quantite = attrs.get('quantite')
        
        if production and quantite and quantite > production.quantite_disponible:
            raise ValidationError(f'Quantité disponible: {production.quantite_disponible}')
        
        return attrs


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'
        read_only_fields = ['date_creation', 'date_paiement', 'statut']


class EvaluationSerializer(serializers.ModelSerializer):
    photos = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Evaluation
        fields = ['id', 'commande', 'note', 'commentaire', 'photos', 'date_creation']
        read_only_fields = ['id', 'date_creation']
    
    def create(self, validated_data):
        photos_data = validated_data.pop('photos', [])
        evaluation = Evaluation.objects.create(**validated_data)
        
        for photo in photos_data:
            PhotoEvaluation.objects.create(evaluation=evaluation, image=photo)
        
        return evaluation