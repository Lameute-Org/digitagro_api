# apps/production/docs/production_swagger.py
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status

TAG_PRODUCTION = 'Productions'
TAG_COMMANDE = 'Commandes'
TAG_PAIEMENT = 'Paiements'
TAG_EVALUATION = 'Évaluations'

# ==================== PRODUCTIONS ====================

LIST_PRODUCTIONS_SCHEMA = extend_schema(
    operation_id="list_productions",
    summary="Liste des productions",
    description="Productions disponibles avec pagination",
    responses={
        200: {
            'description': 'Liste paginée',
            'content': {
                'application/json': {
                    'example': {
                        'count': 42,
                        'results': [{
                            'id': 1,
                            'produit': 'Tomates',
                            'type_production': 'legumes',
                            'quantite': 100,
                            'quantite_disponible': 85,
                            'unite_mesure': 'kg',
                            'prix_unitaire': 500,
                            'disponible': True,
                            'date_recolte': '2025-01-15',
                            'certification': 'bio',
                            'producteur_nom': 'Jean Dupont',
                            'photo_principale': 'http://.../media/productions/photo.jpg',
                            'note_moyenne': 4.5,
                            'latitude': 3.8667,
                            'longitude': 11.5167,
                            'date_creation': '2025-01-10T10:00:00Z'
                        }]
                    }
                }
            }
        }
    },
    tags=[TAG_PRODUCTION]
)

CREATE_PRODUCTION_SCHEMA = extend_schema(
    operation_id="create_production",
    summary="Créer production",
    description="""
    Déclarer une nouvelle production. 
    
    **Si vous n'êtes pas encore producteur :**
    - Fournissez les champs `type_production`, `superficie` (optionnel), `certification` (optionnel)
    - Votre rôle producteur sera automatiquement activé
    - Votre profil producteur sera créé avec ces informations
    
    **Si vous êtes déjà producteur :**
    - Ces champs ne sont pas nécessaires
    - La production sera simplement créée sous votre profil existant
    """,
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'produit': {'type': 'string', 'example': 'Tomates'},
                'type_production': {'type': 'string', 'example': 'Maraîchage', 'description': 'REQUIS si pas encore producteur'},
                'superficie': {'type': 'number', 'example': 2.5, 'description': 'Optionnel pour nouveau producteur'},
                'certification': {'type': 'string', 'example': 'Bio', 'description': 'Optionnel pour nouveau producteur'},
                'quantite': {'type': 'number', 'example': 100},
                'unite_mesure': {'type': 'string', 'enum': ['kg', 'tonne', 'unite', 'litre', 'sac']},
                'prix_unitaire': {'type': 'number', 'example': 500},
                'latitude': {'type': 'number', 'example': 3.8667},
                'longitude': {'type': 'number', 'example': 11.5167},
                'adresse_complete': {'type': 'string'},
                'date_recolte': {'type': 'string', 'format': 'date'},
                'date_expiration': {'type': 'string', 'format': 'date'},
                'description': {'type': 'string'},
                'conditions_stockage': {'type': 'string'}
            },
            'required': ['produit', 'quantite', 'unite_mesure', 'prix_unitaire', 'latitude', 'longitude']
        }
    },
    responses={
        201: {
            'description': 'Production créée (rôle producteur activé si nécessaire)',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'produit': 'Tomates',
                        'producteur': {
                            'id': 1,
                            'nom': 'Jean Dupont',
                            'type_production': 'Maraîchage'
                        },
                        'message': 'Rôle producteur activé automatiquement'
                    }
                }
            }
        },
        400: {
            'description': 'Profil incomplet ou données invalides',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Complétez votre profil (nom, prénom, téléphone, adresse) avant de vendre'
                    }
                }
            }
        },
        403: {'description': 'Non autorisé'}
    },
    tags=[TAG_PRODUCTION]
)

NEARBY_PRODUCTIONS_SCHEMA = extend_schema(
    operation_id="nearby_productions",
    summary="Productions à proximité",
    description="Recherche par rayon GPS (défaut: 10km)",
    parameters=[
        OpenApiParameter('lat', float, description='Latitude', required=True),
        OpenApiParameter('lon', float, description='Longitude', required=True),
        OpenApiParameter('radius', float, description='Rayon en km (défaut: 10)'),
    ],
    responses={
        200: {'description': 'Productions dans le rayon'},
        400: {'description': 'lat et lon requis'}
    },
    tags=[TAG_PRODUCTION]
)

UPLOAD_PHOTO_SCHEMA = extend_schema(
    operation_id="upload_production_photo",
    summary="Ajouter photo",
    description="Upload photo production (max 5 par production)",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {'type': 'string', 'format': 'binary'},
                'ordre': {'type': 'integer', 'example': 0}
            },
            'required': ['image']
        }
    },
    responses={
        201: {'description': 'Photo ajoutée'},
        400: {'description': 'Maximum 5 photos'},
        403: {'description': 'Non autorisé'}
    },
    tags=[TAG_PRODUCTION]
)

SEARCH_PRODUCTIONS_SCHEMA = extend_schema(
    operation_id="search_productions",
    summary="Recherche Elasticsearch",
    description="Recherche avancée avec filtres",
    parameters=[
        OpenApiParameter('search', str, description='Terme recherche'),
        OpenApiParameter('type_production', str, description='Type production'),
        OpenApiParameter('certification', str, description='Certification'),
        OpenApiParameter('disponible', bool, description='Disponible'),
        OpenApiParameter('ordering', str, description='Tri: prix_unitaire, -date_creation'),
    ],
    responses={200: {'description': 'Résultats'}},
    tags=[TAG_PRODUCTION]
)

# ==================== COMMANDES ====================

LIST_COMMANDES_SCHEMA = extend_schema(
    operation_id="list_commandes",
    summary="Mes commandes",
    description="Liste commandes (client) ou reçues (producteur)",
    responses={
        200: {
            'description': 'Liste commandes',
            'content': {
                'application/json': {
                    'example': [{
                        'id': 1,
                        'production_info': {
                            'id': 1,
                            'produit': 'Tomates',
                            'prix_unitaire': 500
                        },
                        'client_nom': 'Marie Martin',
                        'quantite': 10,
                        'montant_total': 5000,
                        'statut': 'confirmee',
                        'adresse_livraison': 'Yaoundé',
                        'date_creation': '2025-01-15T10:00:00Z',
                        'date_confirmation': '2025-01-15T11:00:00Z'
                    }]
                }
            }
        }
    },
    tags=[TAG_COMMANDE]
)

CREATE_COMMANDE_SCHEMA = extend_schema(
    operation_id="create_commande",
    summary="Passer commande",
    description="Créer commande sur une production",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'production': {'type': 'integer'},
                'quantite': {'type': 'number'},
                'adresse_livraison': {'type': 'string'},
                'notes': {'type': 'string'},
                'date_livraison_souhaitee': {'type': 'string', 'format': 'date'}
            },
            'required': ['production', 'quantite', 'adresse_livraison']
        }
    },
    responses={
        201: {'description': 'Commande créée - Notification producteur envoyée'},
        400: {'description': 'Quantité insuffisante'}
    },
    tags=[TAG_COMMANDE]
)

CONFIRM_COMMANDE_SCHEMA = extend_schema(
    operation_id="confirm_commande",
    summary="Confirmer commande",
    description="Producteur confirme la commande",
    responses={
        200: {'description': 'Commande confirmée - Notification client'},
        403: {'description': 'Producteur uniquement'}
    },
    tags=[TAG_COMMANDE]
)

CANCEL_COMMANDE_SCHEMA = extend_schema(
    operation_id="cancel_commande",
    summary="Annuler commande",
    description="Client ou producteur annule",
    responses={
        200: {'description': 'Commande annulée - Notifications envoyées'}
    },
    tags=[TAG_COMMANDE]
)

SHIP_COMMANDE_SCHEMA = extend_schema(
    operation_id="ship_commande",
    summary="Expédier commande",
    description="Producteur marque comme expédiée",
    responses={
        200: {'description': 'Expédiée - Notification client'},
        403: {'description': 'Producteur uniquement'}
    },
    tags=[TAG_COMMANDE]
)

DELIVER_COMMANDE_SCHEMA = extend_schema(
    operation_id="deliver_commande",
    summary="Livrer commande",
    description="Marquer comme livrée",
    responses={
        200: {'description': 'Livrée - Notifications client + producteur'}
    },
    tags=[TAG_COMMANDE]
)

# ==================== PAIEMENTS ====================

INITIATE_PAIEMENT_SCHEMA = extend_schema(
    operation_id="initiate_paiement",
    summary="Initier paiement",
    description="Lancer paiement mobile money",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'commande': {'type': 'integer'},
                'methode': {'type': 'string', 'enum': ['orange_money', 'mtn_money', 'virement', 'cash']},
                'numero_telephone': {'type': 'string'}
            },
            'required': ['commande', 'methode']
        }
    },
    responses={201: {'description': 'Paiement initié'}},
    tags=[TAG_PAIEMENT]
)

CALLBACK_PAIEMENT_SCHEMA = extend_schema(
    operation_id="paiement_callback",
    summary="Webhook mobile money",
    description="Callback opérateurs (Orange/MTN)",
    responses={200: {'description': 'Callback reçu'}},
    tags=[TAG_PAIEMENT]
)

# ==================== ÉVALUATIONS ====================

CREATE_EVALUATION_SCHEMA = extend_schema(
    operation_id="create_evaluation",
    summary="Évaluer producteur",
    description="Noter commande livrée (1-5 étoiles)",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'commande': {'type': 'integer'},
                'note': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                'commentaire': {'type': 'string'},
                'photos': {'type': 'array', 'items': {'type': 'string', 'format': 'binary'}}
            },
            'required': ['commande', 'note', 'commentaire']
        }
    },
    responses={
        201: {'description': 'Évaluation créée - Notification producteur'},
        400: {'description': 'Commande déjà évaluée ou non livrée'}
    },
    tags=[TAG_EVALUATION]
)