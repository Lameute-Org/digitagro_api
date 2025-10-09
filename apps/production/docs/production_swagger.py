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
    summary="Liste des productions disponibles",
    description="Récupère toutes les productions disponibles avec pagination",
    parameters=[
        OpenApiParameter('page', int, description='Numéro de page'),
        OpenApiParameter('page_size', int, description='Taille de page'),
    ],
    responses={
        200: {
            'description': 'Liste paginée des productions',
            'content': {
                'application/json': {
                    'example': {
                        'count': 42,
                        'next': 'http://api/productions/?page=2',
                        'previous': None,
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
                            'photo_principale': 'http://api/media/productions/photo.jpg',
                            'note_moyenne': 4.5,
                            'latitude': 3.8667,
                            'longitude': 11.5167,
                            'date_creation': '2025-01-10T10:00:00Z'
                        }]
                    }
                }
            }
        },
        401: {'description': 'Non authentifié'}
    },
    tags=[TAG_PRODUCTION]
)

CREATE_PRODUCTION_SCHEMA = extend_schema(
    operation_id="create_production",
    summary="Déclarer une production (activation producteur automatique)",
    description="""
    Création d'une production avec activation automatique du rôle producteur.
    
    **Si pas encore producteur:**
    - Le profil doit être complété (nom, prénom, téléphone, adresse)
    - Inclure type_production (REQUIS) + superficie/certification (optionnels)
    - Le rôle producteur sera activé automatiquement
    
    **Si déjà producteur:**
    - Seuls les champs production sont nécessaires
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                # Champs producteur (première fois uniquement)
                'type_production': {'type': 'string', 'description': 'REQUIS si pas encore producteur (Maraîchage, Élevage, etc.)'},
                'superficie': {'type': 'number', 'description': 'Superficie en hectares (optionnel)'},
                'certification': {'type': 'string', 'enum': ['bio', 'standard', 'agroecologique'], 'description': 'Type de certification'},
                
                # Champs production
                'produit': {'type': 'string', 'description': 'Nom du produit'},
                'quantite': {'type': 'number', 'description': 'Quantité disponible'},
                'unite_mesure': {'type': 'string', 'enum': ['kg', 'tonne', 'litre', 'unite', 'sac']},
                'prix_unitaire': {'type': 'number', 'description': 'Prix par unité en FCFA'},
                'latitude': {'type': 'number', 'description': 'Latitude GPS'},
                'longitude': {'type': 'number', 'description': 'Longitude GPS'},
                'adresse_complete': {'type': 'string', 'description': 'Adresse détaillée'},
                'date_recolte': {'type': 'string', 'format': 'date', 'description': 'Date de récolte'},
                'date_expiration': {'type': 'string', 'format': 'date', 'description': 'Date limite (optionnel)'},
                'description': {'type': 'string', 'description': 'Description détaillée'},
                'conditions_stockage': {'type': 'string', 'description': 'Conditions de conservation'}
            },
            'required': ['produit', 'quantite', 'unite_mesure', 'prix_unitaire', 'latitude', 'longitude', 'adresse_complete', 'date_recolte', 'description']
        }
    },
    responses={
        201: {
            'description': 'Production créée avec succès',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'produit': 'Tomates',
                        'message': 'Production créée et rôle producteur activé'
                    }
                }
            }
        },
        400: {
            'description': 'Erreur validation',
            'content': {
                'application/json': {
                    'examples': {
                        'profil_incomplet': {
                            'value': {'error': 'Complétez votre profil (nom, prénom, téléphone, adresse) avant de vendre'}
                        },
                        'champs_manquants': {
                            'value': {'error': 'Le type de production est requis pour devenir producteur'}
                        }
                    }
                }
            }
        },
        401: {'description': 'Non authentifié'}
    },
    tags=[TAG_PRODUCTION]
)

UPDATE_PRODUCTION_SCHEMA = extend_schema(
    operation_id="update_production",
    summary="Modifier une production",
    description="Modification partielle ou complète d'une production (propriétaire uniquement)",
    responses={
        200: {'description': 'Production modifiée'},
        403: {'description': 'Non propriétaire'},
        404: {'description': 'Production non trouvée'}
    },
    tags=[TAG_PRODUCTION]
)

DELETE_PRODUCTION_SCHEMA = extend_schema(
    operation_id="delete_production",
    summary="Supprimer une production",
    description="Suppression définitive d'une production (propriétaire uniquement)",
    responses={
        204: {'description': 'Production supprimée'},
        403: {'description': 'Non propriétaire'},
        404: {'description': 'Production non trouvée'}
    },
    tags=[TAG_PRODUCTION]
)

NEARBY_PRODUCTIONS_SCHEMA = extend_schema(
    operation_id="nearby_productions",
    summary="Productions à proximité",
    description="Recherche des productions dans un rayon GPS défini",
    parameters=[
        OpenApiParameter('lat', float, description='Latitude', required=True),
        OpenApiParameter('lon', float, description='Longitude', required=True),
        OpenApiParameter('radius', float, description='Rayon en km (défaut: 10km)'),
    ],
    responses={
        200: {
            'description': 'Productions trouvées dans le rayon',
            'content': {
                'application/json': {
                    'example': [{
                        'id': 1,
                        'produit': 'Tomates',
                        'distance_km': 2.5,
                        'producteur_nom': 'Jean Dupont',
                        'prix_unitaire': 500
                    }]
                }
            }
        },
        400: {'description': 'Paramètres lat/lon manquants'}
    },
    tags=[TAG_PRODUCTION]
)

# ==================== COMMANDES ====================

LIST_COMMANDES_SCHEMA = extend_schema(
    operation_id="list_commandes",
    summary="Mes commandes",
    description="""
    Liste des commandes selon le rôle:
    - Client: commandes passées
    - Producteur: commandes reçues
    """,
    responses={
        200: {
            'description': 'Liste des commandes',
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
                        'adresse_livraison': 'Yaoundé, Bastos',
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
    summary="Passer une commande",
    description="Création d'une commande sur une production disponible",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'production': {'type': 'integer', 'description': 'ID de la production'},
                'quantite': {'type': 'number', 'description': 'Quantité souhaitée'},
                'adresse_livraison': {'type': 'string', 'description': 'Adresse de livraison'},
                'notes': {'type': 'string', 'description': 'Instructions spéciales'},
                'date_livraison_souhaitee': {'type': 'string', 'format': 'date'}
            },
            'required': ['production', 'quantite', 'adresse_livraison']
        }
    },
    responses={
        201: {'description': 'Commande créée - Notification envoyée au producteur'},
        400: {'description': 'Quantité insuffisante ou données invalides'}
    },
    tags=[TAG_COMMANDE]
)

CONFIRM_COMMANDE_SCHEMA = extend_schema(
    operation_id="confirm_commande",
    summary="Confirmer une commande",
    description="Le producteur confirme la commande reçue",
    responses={
        200: {'description': 'Commande confirmée - Notification envoyée au client'},
        403: {'description': 'Réservé aux producteurs'},
        404: {'description': 'Commande non trouvée'}
    },
    tags=[TAG_COMMANDE]
)

CANCEL_COMMANDE_SCHEMA = extend_schema(
    operation_id="cancel_commande",
    summary="Annuler une commande",
    description="Annulation par le client ou le producteur",
    responses={
        200: {'description': 'Commande annulée - Notifications envoyées'},
        404: {'description': 'Commande non trouvée'}
    },
    tags=[TAG_COMMANDE]
)

# ==================== PAIEMENTS ====================

INITIATE_PAIEMENT_SCHEMA = extend_schema(
    operation_id="initiate_paiement",
    summary="Initier un paiement",
    description="Lancement d'un paiement mobile money",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'commande': {'type': 'integer'},
                'methode': {'type': 'string', 'enum': ['orange_money', 'mtn_money', 'virement', 'cash']},
                'numero_telephone': {'type': 'string', 'description': 'Numéro mobile money'}
            },
            'required': ['commande', 'methode']
        }
    },
    responses={
        201: {'description': 'Paiement initié - En attente de confirmation'},
        400: {'description': 'Données invalides'}
    },
    tags=[TAG_PAIEMENT]
)

# ==================== ÉVALUATIONS ====================

CREATE_EVALUATION_SCHEMA = extend_schema(
    operation_id="create_evaluation",
    summary="Évaluer un producteur",
    description="Noter une commande livrée (1-5 étoiles)",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'commande': {'type': 'integer', 'description': 'ID de la commande'},
                'note': {'type': 'integer', 'minimum': 1, 'maximum': 5, 'description': 'Note de 1 à 5'},
                'commentaire': {'type': 'string', 'description': 'Commentaire détaillé'},
                'photos': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'Photos du produit reçu'
                }
            },
            'required': ['commande', 'note', 'commentaire']
        }
    },
    responses={
        201: {'description': 'Évaluation créée - Notification envoyée au producteur'},
        400: {'description': 'Commande déjà évaluée ou non livrée'},
        404: {'description': 'Commande non trouvée'}
    },
    tags=[TAG_EVALUATION]
)