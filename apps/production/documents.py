# ==================== apps/production/documents.py (Elasticsearch) ====================
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Production

@registry.register_document
class ProductionDocument(Document):
    producteur = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'nom': fields.TextField(),
        'prenom': fields.TextField(),
        'type_production': fields.TextField(),
    })
    
    localisation = fields.GeoPointField()
    
    class Index:
        name = 'productions'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
    
    class Django:
        model = Production
        fields = [
            'id',
            'produit',
            'type_production',
            'quantite',
            'unite_mesure',
            'prix_unitaire',
            'disponible',
            'date_recolte',
            'certification',
            'description',
            'date_creation',
        ]
    
    def prepare_localisation(self, instance):
        return {
            'lat': float(instance.latitude),
            'lon': float(instance.longitude)
        }
    
    def prepare_producteur(self, instance):
        return {
            'id': instance.producteur.user.id,
            'nom': instance.producteur.user.nom,
            'prenom': instance.producteur.user.prenom,
            'type_production': instance.producteur.type_production,
        }
