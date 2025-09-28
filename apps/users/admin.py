from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, PasswordResetRequest, Producteur, 
    Transporteur, Transformateur, Distributeur, Consommateur
)


class ProducteurInline(admin.StackedInline):
    model = Producteur
    can_delete = False
    verbose_name_plural = 'Informations Producteur'


class TransporteurInline(admin.StackedInline):
    model = Transporteur
    can_delete = False
    verbose_name_plural = 'Informations Transporteur'


class TransformateurInline(admin.StackedInline):
    model = Transformateur
    can_delete = False
    verbose_name_plural = 'Informations Transformateur'


class DistributeurInline(admin.StackedInline):
    model = Distributeur
    can_delete = False
    verbose_name_plural = 'Informations Distributeur'


class ConsommateurInline(admin.StackedInline):
    model = Consommateur
    can_delete = False
    verbose_name_plural = 'Informations Consommateur'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'nom', 'prenom', 'telephone', 'role_choisi', 'profile_completed', 'is_active', 'date_creation']
    list_filter = ['role_choisi', 'profile_completed', 'is_active', 'is_staff', 'date_creation']
    search_fields = ['email', 'nom', 'prenom', 'telephone']
    ordering = ['-date_creation']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone', 'adresse', 'avatar')}),
        ('Rôle et Statut', {'fields': ('role_choisi', 'profile_completed', 'is_active', 'is_staff', 'is_superuser')}),
        ('Dates importantes', {'fields': ('last_login', 'date_creation')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'role_choisi', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_creation', 'last_login']
    
    def get_inline_instances(self, request, obj=None):
        """Affiche l'inline approprié selon le rôle"""
        if not obj:
            return []
        
        role_inlines = {
            'producteur': ProducteurInline,
            'transporteur': TransporteurInline,
            'transformateur': TransformateurInline,
            'distributeur': DistributeurInline,
            'consommateur': ConsommateurInline,
        }
        
        inline_class = role_inlines.get(obj.role_choisi)
        if inline_class:
            return [inline_class(self.model, self.admin_site)]
        
        return []


@admin.register(Producteur)
class ProducteurAdmin(admin.ModelAdmin):
    list_display = ['user', 'type_production', 'superficie', 'certification']
    list_filter = ['type_production', 'certification']
    search_fields = ['user__nom', 'user__prenom', 'type_production']


@admin.register(Transporteur)
class TransporteurAdmin(admin.ModelAdmin):
    list_display = ['user', 'type_vehicule', 'capacite', 'permis_transport']
    list_filter = ['type_vehicule']
    search_fields = ['user__nom', 'user__prenom', 'type_vehicule', 'permis_transport']


@admin.register(Transformateur)
class TransformateurAdmin(admin.ModelAdmin):
    list_display = ['user', 'type_transformation', 'certification', 'capacite_traitement']
    list_filter = ['type_transformation', 'certification']
    search_fields = ['user__nom', 'user__prenom', 'type_transformation']


@admin.register(Distributeur)
class DistributeurAdmin(admin.ModelAdmin):
    list_display = ['user', 'type_distribution', 'licence']
    list_filter = ['type_distribution']
    search_fields = ['user__nom', 'user__prenom', 'type_distribution', 'licence']


@admin.register(Consommateur)
class ConsommateurAdmin(admin.ModelAdmin):
    list_display = ['user', 'adresse_livraison']
    search_fields = ['user__nom', 'user__prenom']


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'is_validated', 'expires_at', 'created_at']
    list_filter = ['is_validated', 'created_at']
    search_fields = ['user__email', 'otp_code']
    readonly_fields = ['otp_code', 'reset_token', 'created_at']
    ordering = ['-created_at']