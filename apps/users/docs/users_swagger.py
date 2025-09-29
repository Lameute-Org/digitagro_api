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

# Descriptions réutilisables
DESC_PROFILE_COMPLETED = 'État de complétion du profil'
DESC_TOKEN_KNOX = 'Token Knox 64 caractères'
DESC_DATE_EXPIRY = "Date d'expiration du token"
DESC_USER_PROFILE = "Profil complet de l'utilisateur connecté"

# ==================== SCHÉMAS DE RÉPONSE ====================

USER_REGISTRATION_SCHEMA = extend_schema(
    operation_id="user_registration",
    summary="Inscription utilisateur avec rôle",
    description="Créer un nouveau compte utilisateur avec sélection du rôle spécifique.",
    responses={
        201: {
            'description': MSG_USER_CREATED,
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'user': {
                            'id': 1,
                            'email': 'producteur@example.com',
                            'role_choisi': 'producteur',
                            'profile_completed': True
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

TOKEN_OBTAIN_SCHEMA = extend_schema(
    operation_id="user_login",
    summary="Connexion utilisateur",
    description="Authentification via email ou téléphone avec génération de token Knox.",
    request={
        CONTENT_TYPE_JSON: {
            'type': 'object',
            'properties': {
                'identifier': {'type': 'string', 'description': 'Email ou numéro de téléphone'},
                'password': {'type': 'string', 'description': 'Mot de passe'}
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
                                    'nom': {'type': 'string', 'example': 'Jean'},
                                    'prenom': {'type': 'string', 'example': 'Dupont'},
                                    'adresse': {'type': 'string', 'example': 'Yaoundé'},
                                    'avatar': {'type': 'string', 'example': '/media/avatars/photo.jpg'},
                                    'role_choisi': {'type': 'string', 'example': 'producteur'},
                                    'profile_completed': {'type': 'boolean', 'example': True},
                                    'date_creation': {'type': 'string', 'format': 'date-time', 'example': '2024-01-15T10:30:00Z'},
                                    'user_role': {'type': 'string', 'example': 'Producteur'},
                                    'role_details': {
                                        'type': 'object',
                                        'example': {
                                            'type_production': 'Maraîchage',
                                            'superficie': '2.50',
                                            'certification': 'Bio'
                                        }
                                    }
                                },
                                'required': ['id', 'email', 'role_choisi', 'user_role']
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
    - Rôle et détails spécifiques au rôle
    - État de complétion du profil
    """,
    responses={
        200: {
            'description': 'Profil récupéré avec succès',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'id': 1,
                        'email': 'producteur@example.com',
                        'telephone': EXAMPLE_PHONE,
                        'nom': 'Dupont',
                        'prenom': 'Jean',
                        'adresse': 'Yaoundé, Cameroun',
                        'avatar': '/media/avatars/photo.jpg',
                        'role_choisi': 'producteur',
                        'profile_completed': True,
                        'date_creation': '2024-01-15T10:30:00Z',
                        'user_role': 'Producteur',
                        'role_details': {
                            'type_production': 'Maraîchage',
                            'superficie': '2.50',
                            'certification': 'Bio'
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
        }
    },
    tags=[TAG_PROFILE]
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
        }
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