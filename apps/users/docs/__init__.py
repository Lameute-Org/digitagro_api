from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers

# Décorateur pour forcer la réponse LOGIN
def force_login_response():
    return extend_schema(
        operation_id="user_login",
        summary="Connexion utilisateur",
        description="Authentification via email ou téléphone - retourne token Knox",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'identifier': {'type': 'string', 'description': 'Email ou téléphone'},
                    'password': {'type': 'string', 'description': 'Mot de passe'}
                },
                'required': ['identifier', 'password']
            }
        },
        responses={
            200: {
                'description': 'Connexion réussie',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'token': {
                                    'type': 'string',
                                    'description': 'Token Knox 64 caractères',
                                    'example': '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'
                                },
                                'expiry': {
                                    'type': 'string', 
                                    'format': 'date-time',
                                    'example': '2024-12-31T23:59:59.999999Z'
                                },
                                'user': {
                                    'type': 'object',
                                    'description': 'Données utilisateur complètes'
                                }
                            },
                            'required': ['token', 'expiry', 'user']
                        }
                    }
                }
            },
            400: {
                'description': 'Identifiants invalides'
            }
        },
        tags=['Authentication']
    )

