from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.openapi import AutoSchema
from rest_framework import status

# ==================== CONSTANTES ====================

CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_MULTIPART = 'multipart/form-data'

# Exemples réutilisables
EXAMPLE_EMAIL = 'user@example.com'
EXAMPLE_PHONE = '+237123456789'
EXAMPLE_PASSWORD = 'motdepasse123'
EXAMPLE_TOKEN = '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'
EXAMPLE_EXPIRY = '2024-12-31T23:59:59.999999Z'

# Messages réutilisables
MSG_USER_CREATED = 'Utilisateur créé avec succès'
MSG_INVALID_DATA = 'Données invalides'
MSG_INVALID_CREDENTIALS = 'Identifiants invalides'
MSG_UNAUTHORIZED = 'Non authentifié'

# Tags réutilisables
TAG_AUTH = 'Authentication'
TAG_PROFILE = 'Profile'
TAG_PASSWORD_RESET = 'Password Reset'
TAG_SOCIAL_AUTH = 'Social Authentication'
TAG_ROLES = 'Roles'

# Descriptions réutilisables
DESC_PROFILE_COMPLETED = 'État de complétion du profil'
DESC_TOKEN_KNOX = 'Token Knox 64 caractères'
DESC_DATE_EXPIRY = "Date d'expiration du token"
DESC_USER_PROFILE = "Profil complet de l'utilisateur connecté"

# ==================== SCHÉMAS DE RÉPONSE ====================

USER_REGISTRATION_SCHEMA = extend_schema(
    operation_id="user_registration",
    summary="Inscription utilisateur",
    description="Créer un nouveau compte. Tous les utilisateurs sont consommateurs par défaut. Les rôles professionnels s'activent à la demande.",
    responses={
        201: {
            'description': MSG_USER_CREATED,
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'user': {
                            'id': 1,
                            'email': EXAMPLE_EMAIL,
                            'is_consommateur': True,
                            'is_producteur': False,
                            'is_transporteur': False,
                            'is_transformateur': False,
                            'is_distributeur': False,
                            'profile_completed': False,
                            'active_roles': ['consommateur']
                        },
                        'token': EXAMPLE_TOKEN,
                        'expiry': EXAMPLE_EXPIRY
                    }
                }
            }
        },
        400: {'description': MSG_INVALID_DATA}
    },
    tags=[TAG_AUTH]
)

LOGIN_SCHEMA = extend_schema(
    operation_id="user_login",
    summary="Connexion utilisateur",
    description="Authentification via email ou téléphone avec génération de token Knox.",
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'identifier': {
                    'type': 'string',
                    'description': 'Email ou numéro de téléphone'
                },
                'password': {
                    'type': 'string',
                    'description': 'Mot de passe'
                }
            },
            'required': ['identifier', 'password']
        }
    },
    responses={
        200: {
            'description': 'Connexion réussie - Token Knox généré',
            'content': {
                CONTENT_TYPE_JSON: {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'token': {
                                'type': 'string',
                                'description': DESC_TOKEN_KNOX,
                                'example': EXAMPLE_TOKEN
                            },
                            'expiry': {
                                'type': 'string',
                                'format': 'date-time',
                                'description': DESC_DATE_EXPIRY,
                                'example': EXAMPLE_EXPIRY
                            },
                            'user': {
                                'type': 'object',
                                'description': DESC_USER_PROFILE,
                                'properties': {
                                    'id': {'type': 'integer', 'example': 1},
                                    'email': {'type': 'string', 'example': EXAMPLE_EMAIL},
                                    'telephone': {'type': 'string', 'example': EXAMPLE_PHONE},
                                    'nom': {'type': 'string', 'example': 'Dupont'},
                                    'prenom': {'type': 'string', 'example': 'Jean'},
                                    'adresse': {'type': 'string', 'example': 'Yaoundé'},
                                    'avatar': {'type': 'string', 'example': '/media/avatars/photo.jpg'},
                                    'profile_completed': {'type': 'boolean', 'example': True},
                                    'date_creation': {'type': 'string', 'format': 'date-time', 'example': '2024-01-15T10:30:00Z'},
                                    'active_roles': {
                                        'type': 'array',
                                        'items': {'type': 'string'},
                                        'example': ['consommateur', 'producteur']
                                    },
                                    'role_profiles': {
                                        'type': 'object',
                                        'example': {
                                            'producteur': {
                                                'type_production': 'Maraîchage',
                                                'superficie': '2.50',
                                                'total_productions': 5
                                            }
                                        }
                                    }
                                },
                                'required': ['id', 'email', 'active_roles']
                            }
                        },
                        'required': ['token', 'expiry', 'user']
                    }
                }
            }
        },
        400: {
            'description': MSG_INVALID_CREDENTIALS,
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {"non_field_errors": [MSG_INVALID_CREDENTIALS]}
                }
            }
        }
    },
    tags=[TAG_AUTH]
)

LOGOUT_SCHEMA = extend_schema(
    operation_id="user_logout",
    summary="Déconnexion utilisateur",
    description="Révoque le token d'authentification actuel",
    responses={
        204: {'description': 'Déconnexion réussie'},
        401: {'description': MSG_UNAUTHORIZED}
    },
    tags=[TAG_AUTH]
)

LOGOUT_ALL_SCHEMA = extend_schema(
    operation_id="user_logout_all",
    summary="Déconnexion de tous les appareils",
    description="Révoque tous les tokens de l'utilisateur",
    responses={
        204: {'description': 'Déconnexion de tous les appareils réussie'},
        401: {'description': MSG_UNAUTHORIZED}
    },
    tags=[TAG_AUTH]
)

USER_PROFILE_GET_SCHEMA = extend_schema(
    operation_id="get_user_profile",
    summary="Consulter profil utilisateur",
    description="""
    Récupère les informations complètes du profil utilisateur connecté.
    
    **Inclut :**
    - Informations de base (nom, email, etc.)
    - Tous les rôles actifs et leur statut de vérification
    - Détails des profils pour chaque rôle actif
    - État de complétion du profil
    """,
    responses={
        200: {
            'description': 'Profil récupéré avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'id': 1,
                        'email': EXAMPLE_EMAIL,
                        'telephone': EXAMPLE_PHONE,
                        'nom': 'Dupont',
                        'prenom': 'Jean',
                        'adresse': 'Yaoundé, Cameroun',
                        'avatar': '/media/avatars/photo.jpg',
                        'is_consommateur': True,
                        'is_producteur': True,
                        'is_transporteur': False,
                        'is_transformateur': False,
                        'is_distributeur': False,
                        'is_producteur_verified': False,
                        'is_transporteur_verified': False,
                        'profile_completed': True,
                        'date_creation': '2024-01-15T10:30:00Z',
                        'active_roles': ['consommateur', 'producteur'],
                        'role_profiles': {
                            'producteur': {
                                'type_production': 'Maraîchage',
                                'superficie': '2.50',
                                'certification': 'Bio',
                                'total_productions': 5
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': MSG_UNAUTHORIZED,
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'detail': "Informations d'authentification non fournies."}
                }
            }
        }
    },
    tags=[TAG_PROFILE]
)

USER_PROFILE_UPDATE_SCHEMA = extend_schema(
    operation_id="update_user_profile",
    summary="Mettre à jour profil",
    description="Modification partielle des informations du profil utilisateur",
    request={
        CONTENT_TYPE_MULTIPART: {
            'type': 'object',
            'properties': {
                'telephone': {'type': 'string'},
                'nom': {'type': 'string'},
                'prenom': {'type': 'string'},
                'adresse': {'type': 'string'},
                'avatar': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses={
        200: {'description': 'Profil mis à jour avec succès'},
        400: {'description': MSG_INVALID_DATA}
    },
    tags=[TAG_PROFILE]
)

COMPLETE_PROFILE_SCHEMA = extend_schema(
    operation_id="complete_user_profile",
    summary="Compléter profil",
    description="""
    Finalise les informations manquantes du profil (notamment après social auth).
    Marque automatiquement le profil comme complété.
    """,
    request={
        CONTENT_TYPE_MULTIPART: {
            'type': 'object',
            'properties': {
                'telephone': {'type': 'string', 'description': 'Requis si manquant'},
                'nom': {'type': 'string'},
                'prenom': {'type': 'string'},
                'adresse': {'type': 'string', 'description': 'Requis si manquant'},
                'avatar': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses={
        200: {
            'description': 'Profil complété avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'id': 1,
                        'profile_completed': True,
                        'telephone': EXAMPLE_PHONE,
                        'adresse': 'Yaoundé, Cameroun'
                    }
                }
            }
        },
        400: {'description': MSG_INVALID_DATA}
    },
    tags=[TAG_PROFILE]
)

ROLE_ACTIVATION_SCHEMA = extend_schema(
    operation_id="activate_role",
    summary="Activer un rôle professionnel",
    description="Active un rôle (producteur, transporteur, etc.) avec les informations requises",
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'role': {
                    'type': 'string',
                    'enum': ['producteur', 'transporteur', 'transformateur', 'distributeur'],
                    'description': 'Rôle à activer'
                },
                'type_production': {'type': 'string', 'description': 'Requis pour producteur'},
                'superficie': {'type': 'number', 'description': 'Optionnel pour producteur'},
                'type_vehicule': {'type': 'string', 'description': 'Requis pour transporteur'},
                'capacite': {'type': 'number', 'description': 'Requis pour transporteur'},
                'permis_transport': {'type': 'string', 'description': 'Optionnel pour transporteur'},
                'type_transformation': {'type': 'string', 'description': 'Requis pour transformateur'},
                'type_distribution': {'type': 'string', 'description': 'Requis pour distributeur'},
                'zones_service': {'type': 'string', 'description': 'Optionnel pour distributeur'}
            },
            'required': ['role']
        }
    },
    examples=[
        OpenApiExample(
            name='Activer producteur',
            value={'role': 'producteur', 'type_production': 'Maraîchage', 'superficie': 2.5}
        ),
        OpenApiExample(
            name='Activer transporteur',
            value={'role': 'transporteur', 'type_vehicule': 'Camion', 'capacite': 5.0}
        )
    ],
    responses={
        200: {
            'description': 'Rôle activé avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'message': 'Rôle producteur activé avec succès',
                        'user': {
                            'id': 1,
                            'is_producteur': True,
                            'producteur_activated_at': '2024-01-15T10:30:00Z',
                            'active_roles': ['consommateur', 'producteur']
                        }
                    }
                }
            }
        },
        400: {'description': 'Profil non complété ou données invalides'}
    },
    tags=[TAG_ROLES]
)

ROLES_STATUS_SCHEMA = extend_schema(
    operation_id="get_roles_status",
    summary="Statut des rôles",
    description="Récupère le statut de tous les rôles disponibles",
    responses={
        200: {
            'description': 'Statut des rôles',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'active_roles': ['consommateur', 'producteur'],
                        'available_roles': {
                            'producteur': {
                                'active': True,
                                'verified': False,
                                'activated_at': '2024-01-15T10:30:00Z'
                            },
                            'transporteur': {
                                'active': False,
                                'verified': False,
                                'activated_at': None
                            }
                        },
                        'profile_completed': True
                    }
                }
            }
        }
    },
    tags=[TAG_ROLES]
)

PASSWORD_RESET_REQUEST_SCHEMA = extend_schema(
    operation_id="password_reset_request",
    summary="Demander reset password",
    description="""
    Initialise le processus de réinitialisation par OTP et lien cryptographique.
    
    **Processus :**
    1. Génération automatique d'un code OTP 6 chiffres
    2. Génération d'un token sécurisé pour lien de reset
    3. Envoi par email du code OTP
    4. Expiration automatique après 5 minutes
    """,
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'identifier': {
                    'type': 'string',
                    'description': "Email ou téléphone de l'utilisateur"
                }
            },
            'required': ['identifier']
        }
    },
    examples=[
        OpenApiExample(
            name='Reset par email',
            value={'identifier': EXAMPLE_EMAIL}
        ),
        OpenApiExample(
            name='Reset par téléphone',
            value={'identifier': EXAMPLE_PHONE}
        )
    ],
    responses={
        200: {
            'description': 'Code de réinitialisation envoyé',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'message': 'Code de réinitialisation envoyé'}
                }
            }
        },
        400: {'description': 'Utilisateur non trouvé'}
    },
    tags=[TAG_PASSWORD_RESET]
)

OTP_VERIFICATION_SCHEMA = extend_schema(
    operation_id="verify_otp_code",
    summary="Vérifier code OTP",
    description="Valide le code à 6 chiffres reçu par email et retourne le token de reset",
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'otp_code': {'type': 'string', 'minLength': 6, 'maxLength': 6}
            },
            'required': ['email', 'otp_code']
        }
    },
    responses={
        200: {
            'description': 'Code validé avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'message': 'Code validé',
                        'reset_token': 'secure_reset_token_string'
                    }
                }
            }
        },
        400: {'description': 'Code invalide ou expiré'}
    },
    tags=[TAG_PASSWORD_RESET]
)

TOKEN_VALIDATION_SCHEMA = extend_schema(
    operation_id="validate_reset_token",
    summary="Valider token reset",
    description="Vérifie la validité du lien de réinitialisation cryptographique",
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'reset_token': {'type': 'string'}
            },
            'required': ['reset_token']
        }
    },
    responses={
        200: {
            'description': 'Token valide',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'message': 'Token valide'}
                }
            }
        },
        400: {'description': 'Token invalide ou expiré'}
    },
    tags=[TAG_PASSWORD_RESET]
)

PASSWORD_RESET_CONFIRM_SCHEMA = extend_schema(
    operation_id="confirm_password_reset",
    summary="Confirmer nouveau mot de passe",
    description="""
    Finalise la réinitialisation avec le nouveau mot de passe.
    Supprime automatiquement la demande de reset après succès.
    """,
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'reset_token': {'type': 'string'},
                'new_password': {'type': 'string', 'minLength': 8},
                'new_password_confirm': {'type': 'string'}
            },
            'required': ['reset_token', 'new_password', 'new_password_confirm']
        }
    },
    responses={
        200: {
            'description': 'Mot de passe réinitialisé avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'message': 'Mot de passe réinitialisé avec succès'}
                }
            }
        },
        400: {'description': 'Token invalide ou mots de passe non correspondants'}
    },
    tags=[TAG_PASSWORD_RESET]
)

GOOGLE_AUTH_SCHEMA = extend_schema(
    operation_id="google_oauth_login",
    summary="Connexion Google OAuth2",
    description="""
    Authentification via Google OAuth2 avec gestion du profil incomplet.
    
    **Processus :**
    1. Validation du token Google
    2. Création ou récupération de l'utilisateur
    3. Vérification de la complétion du profil
    4. Génération du token Knox
    """,
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'access_token': {
                    'type': 'string',
                    'description': "Token d'accès Google obtenu côté frontend"
                }
            },
            'required': ['access_token']
        }
    },
    responses={
        200: {'description': 'Connexion Google réussie'},
        400: {'description': 'Token Google invalide'},
        501: {'description': 'Fonctionnalité en développement'}
    },
    tags=[TAG_SOCIAL_AUTH]
)